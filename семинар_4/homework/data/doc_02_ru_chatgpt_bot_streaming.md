# ChatGPT в Telegram-ботах: скорость ответа, печать по буквам и асинхронность

- doc_id: doc_02_ru_chatgpt_bot_streaming
- Источник: ru.stackoverflow.com через Stack Exchange API
- Тредов внутри документа: 3
- Дата выгрузки: 2026-06-10
- Лицензия исходного контента: CC BY-SA 4.0

## Тред: Как ускорить ответы от API CHATGPT в телеграм боте?

- question_id: 1496647
- URL: https://ru.stackoverflow.com/questions/1496647/%d0%9a%d0%b0%d0%ba-%d1%83%d1%81%d0%ba%d0%be%d1%80%d0%b8%d1%82%d1%8c-%d0%be%d1%82%d0%b2%d0%b5%d1%82%d1%8b-%d0%be%d1%82-api-chatgpt-%d0%b2-%d1%82%d0%b5%d0%bb%d0%b5%d0%b3%d1%80%d0%b0%d0%bc-%d0%b1%d0%be%d1%82%d0%b5
- Теги: python, aiogram, gpt, chatgpt-api
- Автор вопроса: dimonrzhev (https://ru.stackoverflow.com/users/476980/dimonrzhev)
- Рейтинг вопроса: 2
- Ответов в исходном треде: 1
- Лицензия: CC BY-SA 4.0

### Вопрос

Имеется телеграм бот с api openai. Хочется сделать его для широкого круга пользователей, но бывает он одному человеку отвечает более 20 секунд и не смотря на то, что он написан на библиотеке aiogram, пока он не даст ответ, другими функциями бота пользоваться нельзя. как сделать ответ быстрым?
Функция ответа представлена следующим образом:

Блок кода:

elif message.from_user.username not in ban_list:
 response = openai.Completion.create(
 model="text-davinci-003",
 prompt=message.text,
 temperature=0.5,
 max_tokens=1024,
 top_p=1.0,
 frequency_penalty=0,
 presence_penalty=0,
 )
 await message.answer(response['choices'][0]['text'])

### Ответ 1497726

- Автор ответа: Сергей Ш (https://ru.stackoverflow.com/users/470333/%d0%a1%d0%b5%d1%80%d0%b3%d0%b5%d0%b9-%d0%a8)
- Рейтинг ответа: 3
- Принят: да
- URL ответа: https://ru.stackoverflow.com/a/1497726
- Лицензия: CC BY-SA 4.0

Блок кода:

import openai
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

bot = Bot(token="2145840652")
openai.api_key = 'f2yzRnGGH'
dp = Dispatcher(bot)

@dp.message_handler()
async def generate_response(message: types.Message):
 response = await openai.Completion.acreate(
 engine="text-davinci-003",
 prompt=message.text,
 temperature=0.5,
 max_tokens=1024,
 top_p=1.0,
 frequency_penalty=0,
 presence_penalty=0,
 )
 await message.answer(response['choices'][0]['text'])

if __name__ == "__main__":
 executor.start_polling(dp, skip_updates=True)

## Тред: Как сделать так, чтобы бот в телеграмме на Aiogram писал сообщение пользователю по буквам как ChatGPT?

- question_id: 1544586
- URL: https://ru.stackoverflow.com/questions/1544586/%d0%9a%d0%b0%d0%ba-%d1%81%d0%b4%d0%b5%d0%bb%d0%b0%d1%82%d1%8c-%d1%82%d0%b0%d0%ba-%d1%87%d1%82%d0%be%d0%b1%d1%8b-%d0%b1%d0%be%d1%82-%d0%b2-%d1%82%d0%b5%d0%bb%d0%b5%d0%b3%d1%80%d0%b0%d0%bc%d0%bc%d0%b5-%d0%bd%d0%b0-aiogram-%d0%bf%d0%b8%d1%81%d0%b0%d0%bb-%d1%81%d0%be%d0%be%d0%b1%d1%89%d0%b5%d0%bd%d0%b8%d0%b5-%d0%bf%d0%be%d0%bb%d1%8c%d0%b7%d0%be%d0%b2%d0%b0%d1%82%d0%b5%d0%bb%d1%8e
- Теги: python, telegram-bot, aiogram, chatgpt
- Автор вопроса: Кирилл Суров (https://ru.stackoverflow.com/users/568634/%d0%9a%d0%b8%d1%80%d0%b8%d0%bb%d0%bb-%d0%a1%d1%83%d1%80%d0%be%d0%b2)
- Рейтинг вопроса: 0
- Ответов в исходном треде: 1
- Лицензия: CC BY-SA 4.0

### Вопрос

У меня есть бот в телеграмме, он работает, но отправляет сообщение после того, как сервер OpenAI отдаст ответ в `response`.

 Я бы хотел, чтобы сообщение отправлялось как у ChatGPT, по буквам, постепенно генерировалось на глазах у пользователя.

Блок кода:

@dp.message_handler()
async def handle_messages(message: types.Message):
 global user_message
 global voicer_text
 global text
 global photo_text
 global user_is_replying
 user_id = message.from_user.id
 await bot.send_message(chat_id=user_id, text="Карсон печатает . . .")
 await bot.send_chat_action(chat_id=user_id, action=types.ChatActions.TYPING) 
 try:

 if user_id in user_is_replying and user_is_replying[user_id]:
 await message.answer("Подождите, Карсон немного перегружен.")
 return

 if photo_text == True:
 user_message = message.text + "\n" + text
 
 elif voicer_text == True:
 user_message = text
 
 else:
 user_message = message.text
 # Проверяем длину сообщения пользователя
 if len(user_message) > max_allowed_message_length:
 await message.reply("Извините, ваше сообщение слишком большое, и я не могу на него ответить.")
 photo_text = False
 return

 if photo_text == True:
 update(user_id, 'user', message.text + "\n" + text)
 
 elif voicer_text == True:
 update(user_id, 'user', text)
 
 else:
 update(user_id, 'user', message.text)

 user_is_replying[user_id] = True
 #user_messages[user_id].append({"role": "user", "content": f"Язык: ru"})
 
 response_content, response = await call_openai(message)
 #response_content = response['choices'][0]['message']['content']
 if len(response_content) + len(user_message) >= 15500:
 await message.reply("Слишком большой запрос . . .\nОшибка на сервере :(")
 photo_text = False
 return
 if response['usage']['total_tokens'] >= 15000:
 await message.reply(
 f'В данный момент вы использовали максимум токенов в рамках контекста: {response["usage"]["total_tokens"]}, будет произведена очистка памяти'
 )
 reset_messages(user_id)

 await bot.send_chat_action(chat_id=user_id, action=types.ChatActions.TYPING)
 if voicer_text == True:
 await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id + 2)
 await message.reply(response_content, parse_mode="markdown")
 
 else:
 await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id + 1)
 await message.reply(response_content, parse_mode="markdown")
 
 photo_text = False
 voicer_text = False
 text = ""
 except aiogram.utils.exceptions.CantParseEntities as ex:
 await message.answer("Извините, произошла ошибка, пожалуйста, попробуйте повторить запрос.")
 except aiogram.utils.exceptions.MessageToDeleteNotFound as ex:
 await message.answer("Произошёл сбой, повторите запрос")
 except openai.error.InvalidRequestError as ex:
 await message.answer(error_2)
 photo_text = False
 except openai.error.RateLimitError as ex:
 await message.answer(error)
 photo_text = False
 finally:
 user_is_replying[user_id] = False
 return False

 
# Функция для асинхронного вызова OpenAI
async def call_openai(message) -> str:
 global user_message
 user_id = message.from_user.id
 # Или какой-то другой способ получения сообщения от пользователя
 user_messages[user_id].append({"role": "user", "content": user_message})
 openai.aiosession.set(ClientSession())
 response = await openai.ChatCompletion.acreate(
 model="gpt-3.5-turbo-16k",
 messages=user_messages[user_id],
 temperature=0.8,
 frequency_penalty=0,
 presence_penalty=0.3,
 max_tokens=max_token_count,
 )

 response_content = response['choices'][0]['message']['content']
 await openai.aiosession.get().close()
 return response_content, response

### Ответ 1544600

- Автор ответа: u n e a s 1 n e s s (https://ru.stackoverflow.com/users/468004/u-n-e-a-s-1-n-e-s-s)
- Рейтинг ответа: 0
- Принят: да
- URL ответа: https://ru.stackoverflow.com/a/1544600
- Лицензия: CC BY-SA 4.0

Вот код:

Блок кода:

message = await message.reply("Загрузка...")
str_ = ''
for i in message.text:
 str_ += i
 await message.edit_text(str_)
 time.sleep(0.1)

 Не уверен в правильности именно названий функций, написал скорее алгоритм.

## Тред: Почему бот отправляет сообщение "подождите" и когда уже отправляет ответ, то сообщение изменяется и удаляется?

- question_id: 1541585
- URL: https://ru.stackoverflow.com/questions/1541585/%d0%9f%d0%be%d1%87%d0%b5%d0%bc%d1%83-%d0%b1%d0%be%d1%82-%d0%be%d1%82%d0%bf%d1%80%d0%b0%d0%b2%d0%bb%d1%8f%d0%b5%d1%82-%d1%81%d0%be%d0%be%d0%b1%d1%89%d0%b5%d0%bd%d0%b8%d0%b5-%d0%bf%d0%be%d0%b4%d0%be%d0%b6%d0%b4%d0%b8%d1%82%d0%b5-%d0%b8-%d0%ba%d0%be%d0%b3%d0%b4%d0%b0-%d1%83%d0%b6%d0%b5-%d0%be%d1%82%d0%bf%d1%80%d0%b0%d0%b2%d0%bb%d1%8f%d0%b5%d1%82-%d0%be%d1%82%d0%b2%d0%b5%d1%82-%d1%82%d0%be-%d1%81%d0%be%d0%be
- Теги: python, асинхронность, python-openai
- Автор вопроса: gemf (https://ru.stackoverflow.com/users/561138/gemf)
- Рейтинг вопроса: 0
- Ответов в исходном треде: 1
- Лицензия: CC BY-SA 4.0

### Вопрос

У меня есть бот chatgpt в телеграмм и есть функция генерации ответа:

Блок кода:

async def ai(prompt):
 global state
 completion = openai.ChatCompletion.create(
 model="gpt-3.5-turbo-16k",
 temperature = 0.8,
 presence_penalty = 0.6,
 frequency_penalty = 0.6,
 messages=[
 {"role": "user", "content": prompt}
 ]
 )
 state = False
 return completion.choices[0].message.content

 Данная функция генерирует ответ на запрос пользователя, и я хочу сделать анимацию при ожидании ответа. То есть когда пользователь отправляет вопрос в чат-бот, отправляет сообщение "подождите" и каждые 0.5с бот должен изменять сообщение и добавлять по 1 точке до трёх:

Блок кода:

async def edit_message(message):
 loop_counter = 0
 while state:
 await message.edit_text(f"ㅤ\n ⌛️ Ожидание ответа{'.' * (loop_counter % 4)}\nㅤ")
 loop_counter += 1
 await asyncio.sleep(0.5)
 await message.delete()

 Но это не работает, бот отправляет сообщение "подождите" и когда бот уже отправляет ответ, то сообщение изменяется и удаляется, но стоит мне функцию ai() заменить на эту:

Блок кода:

async def ai(prompt):
 global state
 count = 0
 for i in range(25):
 count += 1
 print(count)
 await asyncio.sleep(0.1)
 state=False
 return "Отлично!"

 тогда всё работает, в консоль печатаются числа, бот изменяет сообщение затем удаляет его и отправляет ответ.

 Вызов функций выглядит так:

Блок кода:

@dp.message_handler()
async def gpt_answer(message: types.Message):
 global state
 state = True
 editing_message = await message.answer("ㅤ\n ✅ Запрос отправлен!\nㅤ")
 task_edit_msg = asyncio.create_task(edit_message(editing_message))
 task_gpt = asyncio.create_task(ai(message.text))

 await asyncio.gather(task_edit_msg, task_gpt)
 result = await task_gpt
 await message.reply(result, parse_mode="Markdown")

### Ответ 1541715

- Автор ответа: gemf (https://ru.stackoverflow.com/users/561138/gemf)
- Рейтинг ответа: 0
- Принят: нет
- URL ответа: https://ru.stackoverflow.com/a/1541715
- Лицензия: CC BY-SA 4.0

Благодаря комментарию Сергея я узнал о openai.Completion.acreate - что является асинхронной версии openai.Completion.create
