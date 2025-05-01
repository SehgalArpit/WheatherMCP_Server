from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather")

OPENWEATHER_API_KEY = "e5062b065322673e8aca4ea1367abb9b"
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
USER_AGENT = "ZykrrWeatherBot/1.0 (your_email@example.com)"  # Customize this

async def fetch_weather_data(city: str) -> dict[str, Any] | None:
    headers = {
        "User-Agent": USER_AGENT
    }
    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(OPENWEATHER_BASE_URL, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

@mcp.tool()
async def get_temperature_alert(city: str) -> str:
    data = await fetch_weather_data(city)
    if not data or "main" not in data:
        return "Unable to fetch weather data."

    temp = data["main"]["temp"]
    feels_like = data["main"].get("feels_like", "N/A")
    humidity = data["main"].get("humidity", "N/A")
    condition = data["weather"][0]["description"].capitalize()

    if temp >= 40:
        alert = f"🔥 Heat Alert in {city}!"
    elif temp <= 5:
        alert = f"❄️ Cold Alert in {city}!"
    else:
        alert = f"✅ Temperature in {city} is within a normal range."

    return f"""
{alert}
Current Temp: {temp}°C
Feels Like: {feels_like}°C
Humidity: {humidity}%
Condition: {condition}
"""

# This is the FastAPI app that Render needs to serve
app = mcp.app

# Do NOT include mcp.run(...) here

