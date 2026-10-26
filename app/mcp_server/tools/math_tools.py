from langfuse import observe


@observe(name="tool:add", as_type="tool")
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b