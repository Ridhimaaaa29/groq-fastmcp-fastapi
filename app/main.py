from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastmcp.utilities.lifespan import combine_lifespans

from app.api.routes import router
from app.instrumentation import flush_langfuse
from app.mcp_server.server import mcp


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    print('FastAPI starting...')
    yield
    print('FastAPI shutting down...')
    flush_langfuse()


mcp_app = mcp.http_app()   # MCP endpoint lives at /mcp inside this sub-app

app = FastAPI(
    title='Groq + FastMCP',
    lifespan=combine_lifespans(app_lifespan, mcp_app.lifespan),
)

app.include_router(router)
app.mount('/mcp-server', mcp_app)   # final MCP URL: /mcp-server/mcp

