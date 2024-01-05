import os
import json
import asyncio
import logging
import time
from openai import OpenAI, RateLimitError
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command

import config

logging.basicConfig(
    level=logging.INFO,
    filename="logfile.log",
    filemode="w",
    format="%(asctime)s %(levelname)s %(message)s",
)
client = OpenAI(api_key=config.OPENAI_KEY)

bot = Bot(token=config.TOKEN)
dp = Dispatcher()

allowed_users = [config.ADMIN]


'''
Для анимированного сообщения ожидания

async def loading_message(loading, msg):
    count = 0
    while loading:
        time.sleep(0.5)
        count += 1
        if count == 4:
            count = 1
        await msg.edit_text(f'Ожидайте{"." * count}')
'''


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Данный бот позволяет общаться с ChatGPT. Напиши любое сообщение.")


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("Бот передает все сообщения в ChatGPT через OpenAI API. Для доступа к боту обратись к @oijres")


@dp.message(F.from_user.id.in_(allowed_users))
async def chatgpt(message: types.Message):
    logging.info(f'{message.from_user.id}({message.from_user.username}) use ChatGPT')
    msg = await message.reply("Ожидайте...", parse_mode='Markdown')

    '''
    Для анимированного сообщения ожидания
    
    loading = True

    await loading_message(loading, msg)

    time.sleep(3)

    loading = False
    print('Stopped')
    '''
    try:
        path = f'chatgpt_history/{message.chat.id}.json'

        if os.path.exists(path):
            with open(path, 'r', encoding='UTF-8') as file:
                messages = json.load(file)
            if len(messages) > 20:
                messages = messages[-20:]
        else:
            messages = [{'role': 'system', 'content': 'You are a helpful assistant.'}]

        messages.append({'role': 'user', 'content': message.text})
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )

        messages.append(
            {
                'role': 'assistant',
                'content': str(completion.choices[0].message.content),
            }
        )

        with open(path, 'w', encoding='UTF-8') as file:
            json.dump(messages, file, ensure_ascii=False)

        await msg.edit_text(completion.choices[0].message.content, parse_mode='Markdown')
    except RateLimitError:
        await msg.edit_text(f"Ошибка {str(RateLimitError.status_code)}, обратитесь за помощью к администратору.",
                            parse_mode='Markdown')
        logging.warning(RateLimitError)
    except Exception:
        await msg.edit_text(f"Ошибка, обратитесь за помощью к администратору.")
        logging.warning(Exception)


@dp.message()
async def chatgpt(message: types.Message):
    await message.reply('У вас нет доступа к ChatGPT, напишите /help.')


async def main():
    print(f'Path to log: {os.getcwd()}/logfile.log')
    print('Start polling...')
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
