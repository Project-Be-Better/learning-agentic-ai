from langchain_core.tools import tool


@tool
def get_weather(location: str) -> str:
    """Get current weather for a location."""
    weather_data = {
        "singapore": "Rainy, 32C, 85% humidity, poor visibility",
        "malaysia": "Sunny, 30C, 60% humidity, clear",
        "thailand": "Cloudy, 28C, 70% humidity, light rain expected",
    }

    normalized_location = location.lower().strip()
    weather = weather_data.get(
        normalized_location,
        f"Unknown location: {normalized_location}",
    )
    return f"Weather for {normalized_location}: {weather}"


@tool
def get_traffic(location: str) -> str:
    """Get current traffic conditions for a location."""
    traffic_data = {
        "singapore": "Heavy congestion on PIE, 45 min delays",
        "malaysia": "Light traffic on highway, normal flow",
        "thailand": "Moderate traffic, some congestion near Bangkok",
    }

    normalized_location = location.lower().strip()
    traffic = traffic_data.get(
        normalized_location,
        f"Unknown location: {normalized_location}",
    )
    return f"Traffic for {normalized_location}: {traffic}"
