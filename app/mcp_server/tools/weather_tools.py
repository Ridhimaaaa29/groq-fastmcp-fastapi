from langfuse import observe


@observe(name="tool:get_weather", as_type="tool")
def get_weather(city: str) -> str:
    """Return a fake weather report for a city."""
    return f"It is 28°C and sunny in {city}."