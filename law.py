import aiohttp


async def get_labour_code_llm(message):
    url = "https://trans01.rtrk.kz:8121/query"
    post_data = {"query": message}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=post_data) as response:
            response_json = await response.json()
            return response_json['response']
