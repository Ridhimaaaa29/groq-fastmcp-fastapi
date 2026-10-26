from fastmcp import FastMCP

from app.instrumentation import LangfuseMCPMiddleware
from app.mcp_server.tools.math_tools import add
from app.mcp_server.tools.weather_tools import get_weather

mcp = FastMCP('Tools')
mcp.add_middleware(LangfuseMCPMiddleware())

mcp.tool(add)
mcp.tool(get_weather)