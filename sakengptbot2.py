import requests
import json
import asyncio
import logging
from aiogram import Bot, Dispatcher, html, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.methods import SendChatAction
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Bot token can be obtained via https://t.me/BotFather
TOKEN = os.getenv("BOT_TOKEN")

# All handlers should be attached to the Router (or Dispatcher)

dp = Dispatcher()


async def is_user_subscribed(user_id: int) -> bool:
    import aiohttp
    async with aiohttp.ClientSession() as session:
        start_time = datetime.now()
        async with session.get(f'https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id=@sakengpt&user_id={user_id}') as response:
            end_time = datetime.now()
            logging.info(f"Request to Telegram API took {end_time - start_time}")
            if response.status == 200:
                data = await response.json()
                status = data.get('result', {}).get('status', '')
                logging.info(f"Response from Telegram API: {data}")
                return status in ['member', 'administrator', 'creator']
            return False


async def get_request_to_feather(prompt):

    from openai import OpenAI

    client = OpenAI(
    base_url="https://api.featherless.ai/v1",
    api_key=os.getenv("FEATHERLESS_API_KEY"),
    )

    system_prompt = (
        "You Assistant SakenGPT. Answer ONLY in the same language in which you were asked the question.\n"
    )

    start_time = datetime.now()
    response = client.chat.completions.create(
        model='meta-llama/Meta-Llama-3.1-70B-Instruct',
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        max_tokens=4096,
        temperature=0.3,

        
    )
    end_time = datetime.now()
    logging.info(f"Request to Feather API took {end_time - start_time}")
    logging.info(f"Response from Feather API: {response.model_dump()}")
    return response.model_dump()['choices'][0]['message']['content']


async def save_voice_message_as_file(file_id: str):
    file_path = f"voice/message_{file_id}.ogg"
    file = await bot.get_file(file_id)
    await bot.download_file(file.file_path, file_path)

    return file_path

async def save_conversation(
    user_id, 
    message_id, 
    message_text, 
    is_reply, 
    bot_message_id, 
    bot_message_text, 
    bot_message_is_reply):
    conversation = {
        "role": "user",
        "message_id": message_id,
        "content": message_text,
        "reply_to_message": is_reply.message_id if is_reply else None,
    }
    bot_conversation = {
        "role": "assistant",
        "message_id": bot_message_id,
        "content": bot_message_text,
        "reply_to_message": bot_message_is_reply.message_id if bot_message_is_reply else None,
    }
    
    user_id = str(user_id)

    # create file if not exist
    if not os.path.exists(f"conversation_{user_id}.json"):
        with open(f"conversation_{user_id}.json", "a") as file:
            json.dump(conversation, file)
            file.write("\n")
            json.dump(bot_conversation, file)
            file.write("\n")
    else:
        with open(f"conversation_{user_id}.json", "a") as file:
            json.dump(conversation, file)
            file.write("\n")
            json.dump(bot_conversation, file)
            file.write("\n")


async def find_reply_to_message(user_id: int, message_id: int) -> str:
    with open(f"conversation_{user_id}.json", "r") as file:
        for line in file:
            if line.strip():
                conversation = json.loads(line)
                if "message_id" in conversation and "content" in conversation:
                    if conversation["message_id"] == message_id:
                        return conversation["content"]

@dp.message(CommandStart())
async def command_start_handler(message: types.Message) -> None:
    greeting = (
        f"Привет, {html.bold(message.from_user.full_name)}!\n"
        "Я виртуальный помощник SakenGPT, моя задача упростить вашу жизнь\n"
        "Чтобы начать общение, напиши мне сообщение\n"
        "Но учитывайте, что при ответе на мое конкретное сообщение, я могу поддерживать диалог\n"
        "Если же вы хотите начать новый диалог, то просто пишите запрос, не отвечая на сообщение"
    )
    logging.info(f"User {message.from_user.id} started conversation")
    await message.reply(greeting)

@dp.message()
async def echo_handler(message: Message) -> None:
    logging.info(f"User {message.from_user.id} sent message: {message.text}")
    if not await is_user_subscribed(message.from_user.id):
        bot_message_not_subscribed = await message.reply("Для работы с системой, нужно подписаться на канал @sakengpt")
        await save_conversation(message.from_user.id, message.message_id, message.text, None, bot_message_not_subscribed.message_id, bot_message_not_subscribed.text, None)
        logging.info(f"User {message.from_user.id} not subscribed")
        return
    
    message_text = message.text

    if message.content_type == "voice":
        # save the voice message as a file
        file_path = await save_voice_message_as_file(message.voice.file_id)
        logging.info(f"User {message.from_user.id} sent voice message: {file_path}")
        # convert audio to text
        from voice import speech_to_text
        text = await speech_to_text(file_path)
        message_text = text
        logging.info(f"User {message.from_user.id} sent voice message: {text}")
        # send voice is listened

    
    # check message is reply to message
    if message.reply_to_message:
        reply_to_message = await find_reply_to_message(message.from_user.id, message.reply_to_message.message_id)
        logging.info(f"reply_to_message: {reply_to_message}")
        prompt = f"{message_text}\n\nPrevious message to consider in the response: {reply_to_message}"
    else:
        prompt = message_text
    
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    router_llm_prompt = (
        "You're an LLM redirector. Your task is to accept requests from users and redirect them to the desired LLM model. "
        "Redirection consists of a response. In which you will write the name of the model. Which I need to send the client's request to. Here is a list of requests and model names. Which you need to direct to:\n"
        # "1. Weather queries: weather-llm\n"
        # "2. Exchange rate queries: exchange-rate-llm\n"
        # "3. Labour code of the Republic of Kazakhstan (Трудовой кодекс Республики Казахстан): labour-code-llm\n"
        "4. Other requests: other-llm\n"
        "\n"
        "The answer will become invalid if:\n"
        "1. You will include your comments in response\n"
        "2. If there are extra characters or names in the response\n"
        "3. If there are 2 or more model names in the response\n"
        "4. If you did not write verbatim in the name of the model"
        "\n"
        "Here is a user's request:\n"
        f"{prompt}"
    )

    router_llm_response = await get_request_to_feather(router_llm_prompt)
    logging.info(f"Router LLM response: {router_llm_response}")

    if "weather-llm" in router_llm_response:
        from weather2 import get_weather_info_by_message
        await message.answer("Запрашиваю погоду...")
        weather_llm_result = await get_weather_info_by_message(message_text)
        await message.answer(weather_llm_result)
    elif "exchange-rate-llm" in router_llm_response:
        from rates import get_rates_llm
        await message.answer("Запрашиваю курсы валют...")
        rates = await get_rates_llm(message_text)
        await message.answer(rates)
    elif "labour-code-llm" in router_llm_response:
        from law import get_labour_code_llm
        await message.reply("Запрашиваю трудовой кодекс Республики Казахстан...")
        labour_code_llm_result = await get_labour_code_llm(message_text)
        await message.reply(labour_code_llm_result)
    elif "other-llm" in router_llm_response:
        response = await get_request_to_feather(prompt)
        bot_message = await message.reply(response)
        save = await save_conversation(
            message.from_user.id, 
            message.message_id, 
            message.text, 
            message.reply_to_message, 
            bot_message.message_id, 
            bot_message.text, 
            bot_message.reply_to_message
        )
        logging.info(f"save_conversation: {save}")
    else:
        await message.reply("Failed to generate text")

if __name__ == "__main__":
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    asyncio.run(dp.start_polling(bot))


