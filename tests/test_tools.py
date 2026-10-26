import pytest
from fastmcp import Client

from app.mcp_server.server import mcp


@pytest.mark.asyncio
async def test_add():
    async with Client(mcp) as c:
        result = await c.call_tool('add', {'a': 2, 'b': 3})
        assert result.content[0].text == '5'


@pytest.mark.asyncio
async def test_tools_listed():
    async with Client(mcp) as c:
        names = {t.name for t in await c.list_tools()}
        assert {'add', 'get_weather'} <= names