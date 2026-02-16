import aiohttp


async def speech_to_text(audio_file):
    url = "https://trans01.rtrk.kz:8123/audio"
    post_file = {"file": open(audio_file, 'rb')}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=post_file) as response:
            response_json = await response.json()
            return response_json['result']
