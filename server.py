import logging
from fastapi import FastAPI
from starlette.applications import Starlette
from starlette.routing import Route, Mount

from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport

import httpx
from typing import Any

from dotenv import load_dotenv
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-server")

# Constants
OPENWEATHER_API_KEY = "e5062b065322673e8aca4ea1367abb9b"
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
USER_AGENT = "ZykrrWeatherBot/1.0"

# Initialize MCP Server
mcp = FastMCP("weather-sse-server")

async def fetch_weather_data(city: str) -> dict[str, Any] | None:
    """Fetch weather data for an Indian city."""
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
    """Get temperature alert for an Indian city."""
    data = await fetch_weather_data(city)

    if not data or "main" not in data:
        return "Unable to fetch weather data."

    temp = data["main"]["temp"]
    feels_like = data["main"].get("feels_like", "N/A")
    humidity = data["main"].get("humidity", "N/A")
    condition = data["weather"][0]["description"].capitalize()

    if temp >= 40:
        alert = f"Heat Alert in {city}!"
    elif temp <= 5:
        alert = f"Cold Alert in {city}!"
    else:
        alert = f"Temperature in {city} is within a normal range."

    return f"""{alert}
Current Temp: {temp}°C
Feels Like: {feels_like}°C
Humidity: {humidity}%
Condition: {condition}"""

# SSE Transport Setup
transport = SseServerTransport("/messages/")

# SSE Handler
async def handle_sse(request):
    async with transport.connect_sse(
        request.scope,
        request.receive,
        request._send
    ) as (in_stream, out_stream):
        await mcp._mcp_server.run(
            in_stream,
            out_stream,
            mcp._mcp_server.create_initialization_options()
        )

# Starlette App with routes
sse_app = Starlette(
    routes=[
        Route("/sse", handle_sse, methods=["GET"]),
        Mount("/messages/", app=transport.handle_post_message)
    ]
)

# Final FastAPI app
app = FastAPI()
app.mount("/", sse_app)

@app.get("/health")
def health_check():
    return {"message": "Indian Weather MCP SSE Server is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)
