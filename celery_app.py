from celery import Celery
from datetime import timedelta
import aiohttp
import asyncio
import os

celery_app = Celery(
    'weather_tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'
)

# Define the periodic task schedule
celery_app.conf.beat_schedule = {
    'fetch-weather-every-5-seconds': {
        'task': 'weather_tasks.fetch_weather_data',
        'schedule': 5.0,
        'args': ('London',)
    }
}
celery_app.conf.timezone = 'UTC'

FASTAPI_WEATHER_URL = "http://localhost:8000/weather"


async def call_weather_api(city: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(FASTAPI_WEATHER_URL, params={"city": city}) as response:
            response.raise_for_status()
            return await response.json()


@celery_app.task(name="weather_tasks.fetch_weather_data")
def fetch_weather_data(city: str):
    weather_data = asyncio.run(call_weather_api(city))
    print("Fetched weather data:", weather_data)
