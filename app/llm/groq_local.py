import json
import time

from fastmcp import Client
from groq import AsyncGroq
from langfuse import observe
from langfuse.openai import AsyncOpenAI

from app import config
from app.instrumentation import get_langfuse, record_trace_summary
from app.mcp_server.server import mcp

groq = AsyncGroq(api_key=config.GROQ_API_KEY)


@observe(name="ask_local", as_type="chain")
async def ask_local(question: str) -> str:
    langfuse = get_langfuse()
    overall_start = time.perf_counter()
    timeline = []

    # In-memory transport. Use Client('http://localhost:8000/mcp-server/mcp')
    # to go through the running HTTP endpoint instead.
    async with Client(mcp) as mcp_client:
        mcp_tools = await mcp_client.list_tools()
        tools = [
            {
                'type': 'function',
                'function': {
                    'name': t.name,
                    'description': t.description or '',
                    'parameters': t.input_schema if hasattr(t, 'input_schema') else getattr(t, 'inputSchema', {}),
                },
            }
            for t in mcp_tools
        ]

        messages = [{'role': 'user', 'content': question}]
        iteration = 0

        while True:
            iteration += 1
            call_start = time.perf_counter()

            with langfuse.start_as_current_observation(
                name=f"groq_chat_completion_iter_{iteration}",
                as_type="generation"
            ) as gen_span:
                gen_span.update(
                    model=config.GROQ_MODEL,
                    input=messages,
                    metadata={"iteration": iteration, "provider": "groq"}
                )
                try:
                    resp = await groq.chat.completions.create(
                        model=config.GROQ_MODEL,
                        messages=messages,
                        tools=tools,
                        tool_choice='auto',
                    )
                    duration_ms = (time.perf_counter() - call_start) * 1000

                    msg = resp.choices[0].message
                    usage = getattr(resp, 'usage', None)
                    usage_details = None
                    if usage:
                        usage_details = {
                            "prompt_tokens": getattr(usage, 'prompt_tokens', 0) or 0,
                            "completion_tokens": getattr(usage, 'completion_tokens', 0) or 0,
                            "total_tokens": getattr(usage, 'total_tokens', 0) or 0,
                        }

                    # Serialized tool calls if any
                    serialized_tool_calls = None
                    if msg.tool_calls:
                        serialized_tool_calls = [
                            {"id": tc.id, "name": tc.function.name, "arguments": tc.function.arguments}
                            for tc in msg.tool_calls
                        ]

                    gen_span.update(
                        output=msg.content or {"tool_calls": serialized_tool_calls},
                        usage_details=usage_details,
                        metadata={
                            "duration_ms": round(duration_ms, 2),
                            "inference_time_s": round(duration_ms / 1000, 3),
                            "model": config.GROQ_MODEL,
                        }
                    )

                    timeline.append({
                        "step": f"LLM Inference #{iteration}",
                        "type": "generation",
                        "model": config.GROQ_MODEL,
                        "duration_ms": round(duration_ms, 2),
                        "tokens": usage_details or {},
                        "tool_calls_requested": len(msg.tool_calls or [])
                    })
                except Exception as exc:
                    duration_ms = (time.perf_counter() - call_start) * 1000
                    gen_span.update(
                        level="ERROR",
                        status_message=str(exc),
                        metadata={"duration_ms": round(duration_ms, 2), "error": str(exc)}
                    )
                    raise

            messages.append(msg)

            if not msg.tool_calls:
                final_answer = msg.content or ''
                total_duration_ms = (time.perf_counter() - overall_start) * 1000
                record_trace_summary({
                    "trace_name": "ask_local",
                    "question": question,
                    "answer": final_answer,
                    "total_duration_ms": round(total_duration_ms, 2),
                    "model": config.GROQ_MODEL,
                    "timeline": timeline,
                })
                return final_answer

            for call in msg.tool_calls:
                args = json.loads(call.function.arguments or '{}')
                tool_start = time.perf_counter()
                result = await mcp_client.call_tool(call.function.name, args)
                tool_duration_ms = (time.perf_counter() - tool_start) * 1000

                timeline.append({
                    "step": f"MCP Tool: {call.function.name}",
                    "type": "tool",
                    "tool": call.function.name,
                    "args": args,
                    "result": [c.text for c in getattr(result, "content", []) if hasattr(c, "text")],
                    "duration_ms": round(tool_duration_ms, 2),
                })

                messages.append({
                    'role': 'tool',
                    'tool_call_id': call.id,
                    'content': result.content[0].text,
                })
