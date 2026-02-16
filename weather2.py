import aiohttp
import asyncio
import json
from datetime import datetime
import pandas as pd

async def get_request_location_from_llm(message):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        async with session.post(
            'https://89.223.4.142:8001/api/generate', 
            json={
                "model": "newink/suzume:latest",
                "prompt": (
                    "If the request is about the weather, then based on the user's request, your task is to respond by filling in the following data:\n"
                    "address (string)\n"
                    "address: You must write in a simple and understandable format, the name of the locality, if there is information, only city name. You must answer only in English.\n"
                    "User's request: {message}\n"
                ).format(message=message),
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.3
                }
            }
        ) as response:
            result = await response.json()
            response_text = result['response']
            response_json = json.loads(response_text)
            return response_json['address']

async def get_weather_info_by_message(message):
    location = await get_request_location_from_llm(message)
    return location


async def get_weather_info_by_location(location):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        async with session.get(
            f'https://wttr.in/{location}?format=j1'
        ) as response:
            weather_data = await response.json()
            def get_current_condition(weather_data):
                current_condition = weather_data['current_condition'][0]
                feels_like_c = current_condition['FeelsLikeC']
                cloudcover = current_condition['cloudcover']
                humidity = current_condition['humidity']
                temp_C = current_condition['temp_C']
                windspeedKmph = current_condition['windspeedKmph']
                return {
                    "Current date": current_condition['localObsDateTime'],
                    "Feels like": f"{feels_like_c}°C",
                    "Cloud cover": f"{cloudcover}%",
                    "Humidity": f"{humidity}%",
                    "Temperature": f"{temp_C}°C",
                    "Wind": f"{windspeedKmph} km/h"
                }

            def get_forecast(weather_data):
                forecast = weather_data['weather']
                forecast_list = []
                for eachdate in forecast:
                    date = eachdate['date']
                    avgtempC = eachdate['avgtempC']
                    maxtempC = eachdate['maxtempC']
                    mintempC = eachdate['mintempC']
                    forecast_list.append({
                        "Date": date,
                        "Avg tmp": f"{avgtempC}°C",
                        "Max tmp": f"{maxtempC}°C",
                        "Min tmp": f"{mintempC}°C"
                    })
                return forecast_list

            current_condition = get_current_condition(weather_data)
            forecast = get_forecast(weather_data)
            return {
                "Current Weather": current_condition,
                "Forecast": forecast
            }

async def get_request_info_from_llm(message, weather_info, location):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        async with session.post(
            'https://89.223.4.142:8001/api/generate', 
            json={
                "model": "newink/suzume:latest",
                "prompt": (
                    "Answer the following questions as best you can. You must answer in Russian.\n"
                    "Use the following format:\n"

                    "Example question: какая сегодня погода в астане\n"
                    "Example context: \n"
                    "Example weather:\n"
                    "- Current date: 2024-06-19 03:59 AM\n"
                    "- Feels like: 18°C\n"
                    "- Cloud cover: 5%\n"
                    "- Humidity: 88%\n"
                    "- Temperature: 18°C\n"
                    "- Wind: 5 km/h\n"
                    "----------------------------\n"
                    "Forecast:\n"
                    "- Date: 2024-06-19\n"
                    "- Avg tmp: 23°C\n"
                    "- Max tmp: 30°C\n"
                    "- Min tmp: 17°C\n"
                    "----------------------------\n"
                    "Forecast:\n"
                    "- Date: 2024-06-20\n"
                    "- Avg tmp: 24°C\n"
                    "- Max tmp: 31°C\n"
                    "- Min tmp: 17°C\n"
                    "----------------------------\n"
                    "Forecast:\n"
                    "- Date: 2024-06-21\n"
                    "- Avg tmp: 23°C\n"
                    "- Max tmp: 29°C\n"
                    "- Min tmp: 18°C\n"
                    "----------------------------\n"
                    "Example final answer: Сегодня в Астане будет 18 градусов\n"
                    "Real question: {message}\n"
                    "Real context: \n"
                    "{weather_info}\n"
                    "Real location: \n"
                    "{location}\n"
                    "Real final answer:\n"
                ).format(
                    message=message,
                    weather_info=weather_info,
                    location=location
                ),
                "stream": False,
                "options": {
                    "temperature": 0.6
                }
            }
        ) as response:
            result = await response.json()
            response_text = result['response']
            return response_text


async def get_weather_info_by_message(message):
    location = await get_request_location_from_llm(message)
    weather_info = await get_weather_info_by_location(location)
    request_info = await get_request_info_from_llm(message, weather_info, location)
    return request_info

if __name__ == "__main__":
    message = "какая погода завтра в дубае"
    answer = asyncio.run(get_weather_info_by_message(message))
    print(answer)