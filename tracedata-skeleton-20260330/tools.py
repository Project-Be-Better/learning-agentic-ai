from langchain_core.tools import tool


@tool
def get_weather(location: str) -> str:
    """
    Get current weather for a location.

    In real TraceData:
    - Safety Agent would call this to understand driving conditions

    For this demo: Simulate weather data
    """
    # Simulated weather data
    weather_data = {
        "singapore": "Rainy, 32°C, 85% humidity, poor visibility",
        "malaysia": "Sunny, 30°C, 60% humidity, clear",
        "thailand": "Cloudy, 28°C, 70% humidity, light rain expected",
    }

    location = location.lower().strip()
    weather = weather_data.get(location, f"Unknown location: {location}")
    return f"Weather for {location}: {weather}"


@tool
def get_traffic(location: str) -> str:
    """
    Get current traffic conditions.

    In real TraceData:
    - Safety Agent would check traffic to assess driving difficulty

    For this demo: Simulate traffic data
    """
    # Simulated traffic data
    traffic_data = {
        "singapore": "Heavy congestion on PIE, 45 min delays",
        "malaysia": "Light traffic on highway, normal flow",
        "thailand": "Moderate traffic, some congestion near Bangkok",
    }

    location = location.lower().strip()
    traffic = traffic_data.get(location, f"Unknown location: {location}")
    return f"Traffic for {location}: {traffic}"
