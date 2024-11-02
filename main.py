# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import aiohttp
import json
import os
from datetime import datetime, timedelta

app = FastAPI()

# Configuration
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"
API_KEY = "8d0e8fed42d76ca1409dccedc472c1e8"
CACHE_DIR = "weather_cache"
CACHE_EXPIRY = timedelta(seconds=1)


os.makedirs(CACHE_DIR, exist_ok=True)


class WeatherResponse(BaseModel):
    city: str
    timestamp: str
    data: dict


async def fetch_weather(city: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(WEATHER_API_URL, params={"q": city, "appid": API_KEY}) as response:
            response.raise_for_status()
            return await response.json()


def store_locally(city: str, data: dict):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{CACHE_DIR}/{city}_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(data, f)
    return filename


@app.get("/weather")
async def get_weather(city: str):
    cache_file = f"{CACHE_DIR}/{city}.json"
    if os.path.exists(cache_file):
        cache_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        if datetime.now() - cache_time < CACHE_EXPIRY:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            return WeatherResponse(city=city, timestamp=str(cache_time), data=cached_data)

    try:
        weather_data = await fetch_weather(city)
        store_locally(city, weather_data)

        with open(cache_file, 'w') as f:
            json.dump(weather_data, f)

        return WeatherResponse(city=city, timestamp=str(datetime.now()), data=weather_data)

    except aiohttp.ClientResponseError as e:
        raise HTTPException(status_code=e.status, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
