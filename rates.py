import httpx
import asyncio
import aiohttp
import logging

logging.basicConfig(level=logging.INFO)

async def get_rates():
    logging.info("Fetching exchange rates from National Bank of Kazakhstan")
    import os

    logging.info("Downloading exchange rates from National Bank of Kazakhstan")
    async with httpx.AsyncClient() as client:
        response = await client.get("https://nationalbank.kz/rss/rates_all.xml")
        data = response.text
        
    import xml.etree.ElementTree as ET
    root = ET.fromstring(data)
    rates = []
    for item in root.findall('.//item'):
        currency_name = item.find('title').text
        rate_in_kazakhstan_tenge_for_1_currency = item.find('description').text
        rates.append(f"1 {currency_name} = {rate_in_kazakhstan_tenge_for_1_currency} KZT")
    logging.info(f"Fetched rates: {rates}")
    return rates

async def request_rate_from_llm(rates, message):
    logging.info("Requesting rate from LLM")
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        async with session.post(
            'https://89.223.4.142:8001/api/generate', 
            json={
                    "model": "newink/suzume:latest",
                    "prompt": (
                        "Answer the following questions as best you can. You must answer in Russian.\n"
                        "Current exchange rates in Kazakhstan in KZT:\n"
                        "{rates}\n\n"
                        "User question: {message}"
                    ).format(
                        message=message,
                        rates=rates
                    ),
                    "stream": False
                }
            ) as response:
                result = await response.json()
                response_text = result['response']
                logging.info(f"LLM response: {response_text}")
                return response_text

async def get_rates_llm(message):
    logging.info(f"Received message: {message}")
    getrate = await get_rates()
    getrate_llm = await request_rate_from_llm(getrate, message)
    return getrate_llm

if __name__ == "__main__":
    logging.info("Starting main function")
    asyncio.run(get_rates_llm("Какой курс рубля?"))
    logging.info("Main function completed")
