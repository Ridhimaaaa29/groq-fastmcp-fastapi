"""
Langfuse instrumentation module for FastMCP and LLM calls.
Provides helpers, middleware, and decorators to monitor tool calls and LLM inference.
"""
from typing import Any, Optional
import time
from fastmcp.server.middleware import Middleware, MiddlewareContext, CallNext
from fastmcp.tools.base import ToolResult
from langfuse import get_client, observe
from app import config

from collections import deque
from datetime import datetime

# Initialize client (uses LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST)
langfuse_client = get_client()

# In-memory telemetry buffer so the user/instructor can immediately inspect tool & LLM latency
# directly in the browser even without Langfuse cloud credentials configured
RECENT_TRACES = deque(maxlen=50)


def record_trace_summary(entry: dict):
    entry["timestamp"] = datetime.now().strftime("%H:%M:%S")
    RECENT_TRACES.appendleft(entry)


def get_recent_traces():
    return list(RECENT_TRACES)


def get_langfuse():
    return langfuse_client


def flush_langfuse():
    """Flush pending Langfuse events/spans."""
    try:
        langfuse_client.flush()
    except Exception:
        pass


class LangfuseMCPMiddleware(Middleware):
    """
    FastMCP Middleware that automatically traces every tool call to Langfuse
    as an observation with type='tool'.
    Captures tool name, input arguments, output result, execution time, and any errors.
    """

    async def on_call_tool(
        self,
        context: MiddlewareContext[Any],
        call_next: CallNext[Any, ToolResult]
    ) -> ToolResult:
        tool_name = getattr(context.message, 'name', 'unknown_tool')
        tool_args = getattr(context.message, 'arguments', {})

        start_time = time.perf_counter()

        # Create tool observation span
        with langfuse_client.start_as_current_observation(
            name=f"mcp_tool:{tool_name}",
            as_type="tool"
        ) as span:
            span.update(
                input=tool_args,
                metadata={
                    "tool_name": tool_name,
                    "transport": "mcp",
                }
            )
            try:
                result = await call_next(context)
                duration_ms = (time.perf_counter() - start_time) * 1000

                output_content = []
                for item in getattr(result, "content", []):
                    if hasattr(item, "text"):
                        output_content.append(item.text)
                    elif hasattr(item, "model_dump"):
                        output_content.append(item.model_dump())
                    else:
                        output_content.append(str(item))

                span.update(
                    output=output_content if len(output_content) > 1 else (output_content[0] if output_content else ""),
                    metadata={
                        "tool_name": tool_name,
                        "duration_ms": round(duration_ms, 2),
                        "is_error": getattr(result, "is_error", False),
                    }
                )
                return result
            except Exception as exc:
                duration_ms = (time.perf_counter() - start_time) * 1000
                span.update(
                    level="ERROR",
                    status_message=str(exc),
                    metadata={
                        "tool_name": tool_name,
                        "duration_ms": round(duration_ms, 2),
                        "error": str(exc),
                    }
                )
                raise
