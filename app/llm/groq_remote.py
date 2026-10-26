import time
from openai import OpenAI
from langfuse import observe
from app import config
from app.instrumentation import get_langfuse

client = OpenAI(
    api_key=config.GROQ_API_KEY,
    base_url='https://api.groq.com/openai/v1',
)


@observe(name="ask_remote", as_type="chain")
def ask_remote(question: str) -> str:
    langfuse = get_langfuse()
    call_start = time.perf_counter()

    with langfuse.start_as_current_observation(
        name="groq_remote_mcp_response",
        as_type="generation"
    ) as gen_span:
        gen_span.update(
            model=config.GROQ_MODEL,
            input=question,
            metadata={
                "server_url": config.MCP_PUBLIC_URL,
                "provider": "groq_remote_mcp",
            }
        )
        try:
            resp = client.responses.create(
                model=config.GROQ_MODEL,
                input=question,
                tools=[{
                    'type': 'mcp',
                    'server_label': 'my_tools',
                    'server_url': config.MCP_PUBLIC_URL,
                    'require_approval': 'never',
                }],
            )
            duration_ms = (time.perf_counter() - call_start) * 1000
            gen_span.update(
                output=resp.output_text,
                metadata={
                    "duration_ms": round(duration_ms, 2),
                    "inference_time_s": round(duration_ms / 1000, 3),
                }
            )
            return resp.output_text
        except Exception as exc:
            duration_ms = (time.perf_counter() - call_start) * 1000
            gen_span.update(
                level="ERROR",
                status_message=str(exc),
                metadata={"duration_ms": round(duration_ms, 2), "error": str(exc)}
            )
            raise
