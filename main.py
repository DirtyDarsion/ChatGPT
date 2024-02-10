import os
import json
import asyncio
from openai import OpenAI, RateLimitError
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command

import config
from settings import logger

client = OpenAI(api_key=config.OPENAI_KEY)

bot = Bot(token=config.TOKEN)
dp = Dispatcher()

# Список пользователей, чьи запросы будут уходить на сервера OpenAI
allowed_users = [config.ADMIN] + config.USERS


# Обработка команды start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Данный бот позволяет использовать ChatGPT. Напиши любое сообщение.")
    with open('chatgpt_history/users.json', 'r', encoding='UTF-8') as file:
        users = json.load(file)
    if str(message.from_user.id) not in map(lambda x: x['id'], users):
        users.append({
            'id': message.from_user.id,
            'username': message.from_user.username,
            'firstname': message.from_user.first_name
        })
    with open('chatgpt_history/users.json', 'w', encoding='UTF-8') as file:
        json.dump(users, file, ensure_ascii=False)


# Обработка команды help
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("Бот транслирует сообщения в облачный сервис OpenAI API, "
                         "который в свою очередь использует модель ChatGPT. Чтобы воспользоваться этим ботом, "
                         "обратитесь к пользователю @oijres для получения доступа.")


# Отправить последние 30 строк из файла logfile.txt. Команда доступна только админу бота.
@dp.message(Command("log"), F.from_user.id == config.ADMIN)
async def cmd_help(message: types.Message):
    with open('logfile.log', 'r') as log:
        text = log.readlines()
        answer = text[-30:]
        message_text = ''.join(answer)
        message_text += f'\nВсего строк в логе: **{len(text)}**'
        await message.reply(message_text, parse_mode='Markdown')


@dp.message(Command("logfix"), F.from_user.id == config.ADMIN)
async def cmd_help(message: types.Message):
    with open('logfile.log', 'r') as log:
        text = log.readlines()
        answer = text[-30:]
        message_text = ''.join(answer)
        message_text += f'\nВсего строк в логе: {len(text)}'
        await message.reply(message_text)


# Отправка на API остальные запросы допущенных пользователей
@dp.message(F.from_user.id.in_(allowed_users))
async def chatgpt(message: types.Message):
    logger.info(f'{message.from_user.id}({message.from_user.username}) use ChatGPT. Text: "{message.text}"')

    # Сообщение будет редактироваться когда получит ответ от серверов OpenAI
    msg = await message.reply("Ожидайте...", parse_mode='Markdown')
    
    try:
        # История переписки с пользователем хранится в файле path:
        path = f'chatgpt_history/{message.chat.id}.json'

        # Считывание последних 20 строк файла path
        if os.path.exists(path):
            with open(path, 'r', encoding='UTF-8') as file:
                messages = json.load(file)
            if len(messages) > 20:
                messages = messages[-20:]
        else:
            messages = [{'role': 'system', 'content': 'You are a funny assistant.'}]

        # Добавление в историю переписки последнего сообщения пользователя и отправка в API
        messages.append({'role': 'user', 'content': message.text})
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )

        logger.warning(completion)

        # Сохранение в историю переписки ответ бота и запись в файл
        messages.append(
            {
                'role': 'assistant',
                'content': str(completion.choices[0].message.content),
            }
        )
        with open(path, 'w', encoding='UTF-8') as file:
            json.dump(messages, file, ensure_ascii=False)

        # Отправка ответа ChatGPT в чат
        await msg.edit_text(completion.choices[0].message.content, parse_mode='Markdown')
    # Обработка ошибки 429 о превышении лимитов или окончании бесплатного срока API ключа
    except RateLimitError:
        logger.error(RateLimitError)
        await msg.edit_text(f"Ошибка {str(RateLimitError.status_code)}, обратитесь за помощью к администратору.",
                            parse_mode='Markdown')


@dp.message()
async def chatgpt(message: types.Message):
    await message.reply('У вас нет доступа. Подробности: /help.')


async def main():
    logger.info(f'Path to log: {os.getcwd()}/logfile.log')
    logger.info('Start polling...')
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
