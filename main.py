import asyncio
import logging

import sys
from os import getenv
from datetime import datetime

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv()

# Bot token can be obtained via https://t.me/BotFather
TOKEN = getenv("BOT_TOKEN")

# All handlers should be attached to the Router (or Dispatcher)

dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")

import requests

def get_lat_lon_for_address(address):
    geocode_api_key = getenv("GEOCODE_API_KEY")
    url = f"https://geocode.maps.co/search?q={address}&api_key={geocode_api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data[0]["lat"], data[0]["lon"]
    else:
        return None

def get_weather_data(latitude, longitude):
    import openmeteo_requests

    import requests_cache
    import pandas as pd
    from retry_requests import retry

    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ["temperature_2m", "precipitation_probability", "precipitation"],
        "timezone": "auto",
        "forecast_days": 1
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_precipitation_probability = hourly.Variables(1).ValuesAsNumpy()
    hourly_precipitation = hourly.Variables(2).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
        end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = hourly.Interval()),
        inclusive = "left"
    )}
    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["precipitation_probability"] = hourly_precipitation_probability
    hourly_data["precipitation"] = hourly_precipitation

    hourly_dataframe = pd.DataFrame(data = hourly_data)
    return hourly_dataframe



async def is_user_subscribed(user_id: int) -> bool:
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id=@sakengpt&user_id={user_id}') as response:
            if response.status == 200:
                data = await response.json()
                status = data.get('result', {}).get('status', '')
                return status in ['member', 'administrator', 'creator']
            return False


@dp.message()
async def echo_handler(message: Message) -> None:
    """
    Handler will forward receive a message back to the sender

    By default, message handler will handle all message types (like a text, photo, sticker etc.)
    """
    try:
        import aiohttp

        if not await is_user_subscribed(message.from_user.id):
            await message.answer("Для работы с системой, нужно подписаться на канал @sakengpt")
            return

        router_llm_promt = (
            "You're an LLM redirector. Your task is to accept requests from users and redirect them to the desired LLM model. "
            "Redirection consists of a response. In which you will write the name of the model. Which I need to send the client's request to. Here is a list of requests and model names. Which you need to direct to:\n"
            "1. Weather queries: weather-llm\n"
            "2. Exchange rate queries: exchange-rate-llm\n"
            "3. Other requests: other-llm\n"
            "\n"
            "The answer will become invalid if:\n"
            "1. You will include your comments in response\n"
            "2. If there are extra characters or names in the response\n"
            "3. If there are 2 or more model names in the response\n"
            "4. If you did not write verbatim in the name of the model"
            "\n"
            "Here is a user's request:\n"
            f"{message.text}"
        )

        full_promt = (
            "You. SakenGPT's virtual assistant. Your task is to respond to user requests. Use these rules when answering: \n"
            "1. Answer only in Russian language \n"
            "\n"
            "Don't answer. If you have one of these violations:\n"
            "1. The answer is in English or Russian letters are used in Russian transliteration \n"
            f"{message.text} \n\n"
        )

        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            router_llm_payload = {
                "model": "newink/suzume:latest",
                "prompt": router_llm_promt,
                "stream": False
            }

            full_llm_payload = {
                "model": "newink/suzume:latest",
                "prompt": full_promt,
                "stream": False
            }
            
            async with session.post('https://89.223.4.142:8001/api/generate', json=router_llm_payload) as response:
                if response.status == 200:
                    router_llm_result = await response.json()
                    router_llm_result = router_llm_result.get('response', 'No text generated')
                    logging.info(f"Request time: {datetime.now()}, User name: {message.from_user.full_name}, User id: {message.from_user.id}, Request text: {message.text}, Response text: {router_llm_result}")
                    if router_llm_result == "weather-llm":
                        from weather2 import get_weather_info_by_message
                        await message.answer("Запрашиваю погоду...")
                        weather_llm_result = asyncio.run(get_weather_info_by_message(message.text))
                        await message.answer(weather_llm_result)
                    elif router_llm_result == "exchange-rate-llm":
                        from rates import get_rates_llm
                        await message.answer("Запрашиваю курсы валют...")
                        rates = asyncio.run(get_rates_llm(message.text))
                        await message.answer(rates)
                    elif router_llm_result == "other-llm":
                        async with session.post('https://89.223.4.142:8001/api/generate', json=full_llm_payload) as response:
                            if response.status == 200:
                                full_llm_result = await response.json()
                                full_llm_result = full_llm_result.get('response', 'No text generated')
                                logging.info(f"Request time: {datetime.now()}, User name: {message.from_user.full_name}, User id: {message.from_user.id}, Request text: {message.text}, Response text: {full_llm_result}")
                                await message.answer(full_llm_result)
                    else:
                        await message.answer("Failed to generate text")
                else:
                    await message.answer("Failed to generate text")
    except TypeError:
        await message.answer("Nice try!")


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())