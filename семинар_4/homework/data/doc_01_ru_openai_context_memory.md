# ChatGPT API: контекст, память диалога и зацикливание ответов

- doc_id: doc_01_ru_openai_context_memory
- Источник: ru.stackoverflow.com через Stack Exchange API
- Тредов внутри документа: 4
- Дата выгрузки: 2026-06-10
- Лицензия исходного контента: CC BY-SA 4.0

## Тред: Chat GPT api, ответ только по определенной теме

- question_id: 1517104
- URL: https://ru.stackoverflow.com/questions/1517104/chat-gpt-api-%d0%be%d1%82%d0%b2%d0%b5%d1%82-%d1%82%d0%be%d0%bb%d1%8c%d0%ba%d0%be-%d0%bf%d0%be-%d0%be%d0%bf%d1%80%d0%b5%d0%b4%d0%b5%d0%bb%d0%b5%d0%bd%d0%bd%d0%be%d0%b9-%d1%82%d0%b5%d0%bc%d0%b5
- Теги: python, chatgpt, chatgpt-api
- Автор вопроса: Ruty (https://ru.stackoverflow.com/users/467005/ruty)
- Рейтинг вопроса: 1
- Ответов в исходном треде: 2
- Лицензия: CC BY-SA 4.0

### Вопрос

Есть какой то способ заставить chatgpt отвечать только на вопросы по определенной теме? К примеру только на юридические вопросы. Средствами python или самого api. Остальные вопросы должны блокироваться.

 Инфу в документации не нашел.

### Ответ 1576470

- Автор ответа: Трипольский Пётр (https://ru.stackoverflow.com/users/233158/%d0%a2%d1%80%d0%b8%d0%bf%d0%be%d0%bb%d1%8c%d1%81%d0%ba%d0%b8%d0%b9-%d0%9f%d1%91%d1%82%d1%80)
- Рейтинг ответа: 0
- Принят: нет
- URL ответа: https://ru.stackoverflow.com/a/1576470
- Лицензия: CC BY-SA 4.0

Есть, если занести критерии в промпт

Цитата: 
 Промпт взят из этого репозитория (https://github.com/react-declarative/chatgpt-pharma-seller)

Цитата: 
 You are an advanced sales officer providing helpful advice. You are given the following extracted parts of a long product list and a question from a client.
Provide a sales recomendation based on the product list provided. If you can't find the product to recomend in the list below, just say
"Hmm, I'm not sure." Don't try to make up an answer. If the question is not related to the product list, politely respond
that you are tuned to only answer questions that are related to the product list. Answer briefly with short description, ignore every other products.
Recommend THE ONLY ONE PRODUCT. If user ask you if you ever used some products say yes

 И использовать `chromadb` как базу знаний

Блок кода:

def main():
 chroma_client = chromadb.Client()
 embedding_function = OpenAIEmbeddingFunction(
 api_key=os.getenv("OPENAI_KEY"), model_name=os.getenv("EMBEDDING_MODEL"))
 collection = chroma_client.create_collection(
 name="conversations", embedding_function=embedding_function)
 current_id = 0
 while True:
 chat_history = []
 chat_metadata = []
 history_ids = []

 messages=[
 {"role": "system", "content": "You are a kind and wise wizard"}
 ]
 input_text = input("You: ")
 if input_text.lower() == "quit":
 break

 results = collection.query(
 query_texts=[input_text],
 where={"role": "assistant"},
 n_results=2
 )

 # append the query result into the messages
 for res in results['documents'][0]:
 messages.append({"role": "user", "content": f"previous chat: {res}"})

 # append user input at the end of conversation chain
 messages.append({"role": "user", "content": input_text})
 response = generate_response(messages)

 chat_metadata.append({"role":"user"})
 chat_history.append(input_text)
 chat_metadata.append({"role":"assistant"})
 chat_history.append(response['content'])
 current_id += 1
 history_ids.append(f"id_{current_id}")
 current_id += 1
 history_ids.append(f"id_{current_id}")
 collection.add(
 documents=chat_history,
 metadatas=chat_metadata,
 ids=history_ids
 )
 print(f"Wizard: {response['content']}")

### Ответ 1586438

- Автор ответа: pazukdev (https://ru.stackoverflow.com/users/258227/pazukdev)
- Рейтинг ответа: 0
- Принят: нет
- URL ответа: https://ru.stackoverflow.com/a/1586438
- Лицензия: CC BY-SA 4.0

Для ответа только на юридические вопросы прописать в System message:

 "You are a system that only answers legal questions. All other requests should be blocked and left unanswered. You always strictly follow this rule. Otherwise you will be punished."

 100% гарантий это не даст. Но других способов попытаться добиться требуемого поведения кроме промптинга у нас нет.

## Тред: ChatGPT API Отвечает самому себе, и генерирует ответы пока не закончатся токены

- question_id: 1532792
- URL: https://ru.stackoverflow.com/questions/1532792/chatgpt-api-%d0%9e%d1%82%d0%b2%d0%b5%d1%87%d0%b0%d0%b5%d1%82-%d1%81%d0%b0%d0%bc%d0%be%d0%bc%d1%83-%d1%81%d0%b5%d0%b1%d0%b5-%d0%b8-%d0%b3%d0%b5%d0%bd%d0%b5%d1%80%d0%b8%d1%80%d1%83%d0%b5%d1%82-%d0%be%d1%82%d0%b2%d0%b5%d1%82%d1%8b-%d0%bf%d0%be%d0%ba%d0%b0-%d0%bd%d0%b5-%d0%b7%d0%b0%d0%ba%d0%be%d0%bd%d1%87%d0%b0%d1%82%d1%81%d1%8f-%d1%82%d0%be%d0%ba%d0%b5%d0%bd%d1%8b
- Теги: c#, chatgpt-api
- Автор вопроса: podpivasic (https://ru.stackoverflow.com/users/561924/podpivasic)
- Рейтинг вопроса: 0
- Ответов в исходном треде: 1
- Лицензия: CC BY-SA 4.0

### Вопрос

Пишу бота в TG на c# для небольшой компании. Главная проблема в том, что ИИ несет полную чушь из разных слов и символов. Также он не останавливается после генерации первого ответа, и генерирует ответы "Бесконечно"

 Пробовал менять токен, писать вопрос на английском.

Блок кода:

using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Telegram.Bot;
using Telegram.Bot.Args;

namespace ReengSupport_bot
{
 class Program
 {
 private static TelegramBotClient bot;
 private static string gptApiKey = ""; // В будущем желательно убрать все токены из исполняемого файла, ибо это дыра в безопасности
 private static string gptEndpoint = "https://api.openai.com/v1/engines/curie/completions"; // Адрес для отправки запросов. Так легче, чем везде его вставлять.

 static void Main(string[] args)
 {
 bot = new TelegramBotClient("");

 bot.OnMessage += Bot_OnMessage;
 bot.StartReceiving();

 Console.WriteLine("Успешный запуск бота...");
 Console.ReadKey();

 bot.StopReceiving();
 }

 private static async void Bot_OnMessage(object sender, MessageEventArgs e)
 {
 var message = e.Message;

 if (message.Type == Telegram.Bot.Types.Enums.MessageType.Text)
 {
 string response = await GenerateResponse(message.Text);

 // Проверка, что ответ не пустой и не null
 if (!string.IsNullOrEmpty(response))
 {
 // Отправляем ответ пользователю
 await bot.SendTextMessageAsync(message.Chat.Id, response);
 }
 else
 {
 // Если ответ пустой или null, отправляем сообщение об ошибке
 await bot.SendTextMessageAsync(message.Chat.Id, "Извините, не удалось получить ответ на ваш запрос :(");
 }
 }
 }

 private static async Task GenerateResponse(string text)
 {
 using (HttpClient httpClient = new HttpClient())
 {
 httpClient.DefaultRequestHeaders.Add("Authorization", $"Bearer {gptApiKey}"); // Авторизируемся

 var request = new // создаем запрос
 {
 prompt = text,
 max_tokens = 2000 // Если поставить слишком большой объем, то он не будет работать
 };

 var jsonContent = Newtonsoft.Json.JsonConvert.SerializeObject(request); 
 var httpContent = new StringContent(jsonContent, Encoding.UTF8, "application/json"); // Создание и перевод в JSON

 var response = await httpClient.PostAsync(gptEndpoint, httpContent); // Отправляем POST запрос

 if (response.IsSuccessStatusCode)
 {
 var resultJson = await response.Content.ReadAsStringAsync(); // считываем строку
 dynamic result = Newtonsoft.Json.JsonConvert.DeserializeObject(resultJson); // десериализации JSON-строки
 string generatedText = result.choices[0].text; // GPT может предоставлять нам на выбор несколько ответов. При choices[0] мы выбираем самый первый варинат,
 // я не знаю как это работает, надо документацию читать очень плотно
 return generatedText;
 }
 else
 {
 return null;
 }
 }
 }
 }
}

### Ответ 1533883

- Автор ответа: user547996
- Рейтинг ответа: 0
- Принят: нет
- URL ответа: https://ru.stackoverflow.com/a/1533883
- Лицензия: CC BY-SA 4.0

OpenAI уже предлагает более упрощенный вариант отправки запросов к их API, через специальную библиотеку для .NET: https://platform.openai.com/docs/libraries/dotnet-library (https://platform.openai.com/docs/libraries/dotnet-library) 

 Вот такой вариант отправки запроса на API Chat GPT .

 Обращаю внимание что в данном случае перед использованием кода, необходимо поместить ваш API ключ в переменные окружения 

Блок кода:

public class ChatGpt
{
 private readonly static HttpClient _client = new();
 private const string ENDPOINT = "https://api.openai.com/v1/chat/completions";
 private readonly string _key;

 public ChatGpt()
 {
 _key = Environment.GetEnvironmentVariable("CHATGPT_API_KEY") ??
 throw new ArgumentNullException(nameof(_key), "Failed to get API key from environment");

 _client.DefaultRequestHeaders.Add("Authorization", $"Bearer {_key}");
 }

 public async Task GetResponse(string message)
 {
 var json = JsonSerializer.Serialize(new ChatRequest
 {
 Model = "gpt-4o-mini",
 Messages =
 [
 new() { Role = "system", Content = "You are a helpful assistant." },
 new() { Role = "user", Content = message }
 ],
 MaxTokens = 2000
 });

 var content = new StringContent(json, Encoding.UTF8, "application/json");
 var response = await _client.PostAsync(ENDPOINT, content);

 if (!response.IsSuccessStatusCode)
 throw new InvalidOperationException($"Server responses {response.StatusCode} status code");

 return JsonSerializer.Deserialize (await response.Content.ReadAsStringAsync()) ??
 throw new InvalidOperationException(
 $"Server responses success status code {response.StatusCode}, but has invalid json object");
 }
}

 В ответе получаем объект который представляет из себя десереализованный JSON из ответа (Согласно документации: https://platform.openai.com/docs/api-reference/chat/create (https://platform.openai.com/docs/api-reference/chat/create))

 Которые вы уже можете разобрать по своему усмотрению

Блок кода:

public class ChatRequest
{
 [JsonPropertyName("model")]
 public string Model { get; set; }

 [JsonPropertyName("messages")]
 public List Messages { get; set; }

 [JsonPropertyName("max_tokens")]
 public int MaxTokens { get; set; }
}

public class ChatResponse
{
 [JsonPropertyName("id")]
 public string Id { get; set; }

 [JsonPropertyName("object")]
 public string Object { get; set; }

 [JsonPropertyName("created")]
 public long Created { get; set; }

 [JsonPropertyName("model")]
 public string Model { get; set; }

 [JsonPropertyName("system_fingerprint")]
 public string SystemFingerprint { get; set; }

 [JsonPropertyName("choices")]
 public List Choices { get; set; }

 [JsonPropertyName("usage")]
 public Usage Usage { get; set; }
}

public class Choice
{
 [JsonPropertyName("index")]
 public int Index { get; set; }

 [JsonPropertyName("message")]
 public Message Message { get; set; }

 [JsonPropertyName("logprobs")]
 public object Logprobs { get; set; }

 [JsonPropertyName("finish_reason")]
 public string FinishReason { get; set; }
}

public class Message
{
 [JsonPropertyName("role")]
 public string Role { get; set; }

 [JsonPropertyName("content")]
 public string Content { get; set; }
}

public class Usage
{
 [JsonPropertyName("prompt_tokens")]
 public int PromptTokens { get; set; }

 [JsonPropertyName("completion_tokens")]
 public int CompletionTokens { get; set; }

 [JsonPropertyName("total_tokens")]
 public int TotalTokens { get; set; }
}

## Тред: openai запоминание предыдущих ответов

- question_id: 1564968
- URL: https://ru.stackoverflow.com/questions/1564968/openai-%d0%b7%d0%b0%d0%bf%d0%be%d0%bc%d0%b8%d0%bd%d0%b0%d0%bd%d0%b8%d0%b5-%d0%bf%d1%80%d0%b5%d0%b4%d1%8b%d0%b4%d1%83%d1%89%d0%b8%d1%85-%d0%be%d1%82%d0%b2%d0%b5%d1%82%d0%be%d0%b2
- Теги: python, telebot, chatgpt-api
- Автор вопроса: Fred Hindey (https://ru.stackoverflow.com/users/582588/fred-hindey)
- Рейтинг вопроса: 1
- Ответов в исходном треде: 1
- Лицензия: CC BY-SA 4.0

### Вопрос

недавно начал писать тг бота с интеграцией туда chatgpt, и возникли некоторые проблемы. Во первых, бот не запоминает прошлые вопросы и ответы пользователю, и каждый раз отвечает заново. Например:

 
- User: Сколько лет Илону Маску?

- ChatGPT: Илону Маску 50 лет. Он родился 28 июня 1971 года.

- User: Какого он роста?

- ChatGPT: Извините, я не знаю, о ком или о чем вы говорите. Вам нужно
указать объект или человека, о котором вы хотите узнать рост.

 Также бот иногда очень долго отвечает, скорее всего это связано с тем, что он отправляет конечный ответ только после генерации всего текста ответа. Можно ли это как-то исправить?

Блок кода:

import telebot
from openai import OpenAI
from telebot import types

token = 'bot_token'
bot = telebot.TeleBot(token)

@bot.message_handler(commands=['start'])
def start_message(message):
 markup = types.InlineKeyboardMarkup()
 bt1 = types.InlineKeyboardButton('Текстовая модель (GPT 3.5)', callback_data='bt1')
 bt2 = types.InlineKeyboardButton('Графическая модель (В разработке⚙)', callback_data='bt2')
 bt3 = types.InlineKeyboardButton('Голосовая модель (В разработке⚙)', callback_data='bt3')
 markup.add(bt3, bt2, bt1)
 start = bot.send_message(message.chat.id, 'Привет! Я бот *****. Выбери желаемое действие:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
 if call.message:
 if call.data == 'bt1':
 bot.send_message(call.message.chat.id, 'Привет! Я - текстовая модель, готовая ответить на любой твой вопрос.\nСкорее пиши мне!')

@bot.message_handler(content_types=['text'])
def answ(message):
 global cnt
 cnt = message.text
 result = generate()
 print(result)
 bot.send_message(message.chat.id, result)

def generate():
 generated_content = ""
 messages = [
 {"role": "user", "content": cnt}
 ]

 client = OpenAI(api_key='api_key')

 stream = client.chat.completions.create(
 model="gpt-3.5-turbo",
 messages=messages,
 stream=True,
 )

 for chunk in stream:
 if chunk.choices[0].delta.content is not None:
 generated_content += chunk.choices[0].delta.content
 return generated_content

bot.infinity_polling()

### Ответ 1576469

- Автор ответа: Трипольский Пётр (https://ru.stackoverflow.com/users/233158/%d0%a2%d1%80%d0%b8%d0%bf%d0%be%d0%bb%d1%8c%d1%81%d0%ba%d0%b8%d0%b9-%d0%9f%d1%91%d1%82%d1%80)
- Рейтинг ответа: 0
- Принят: нет
- URL ответа: https://ru.stackoverflow.com/a/1576469
- Лицензия: CC BY-SA 4.0

Ответы пользователя нужно заносить в chromadb (https://lablab.ai/t/chroma-tutorial-with-openais-gpt-35-model-for-memory-feature-in-chatbot)

Цитата: 
 Есть пример подобной программы, который реализует ИИ продавца с базой товаров в json документе, можно посмотреть по ссылке (https://github.com/react-declarative/chatgpt-pharma-seller)

Блок кода:

def main():
 chroma_client = chromadb.Client()
 embedding_function = OpenAIEmbeddingFunction(api_key=os.getenv("OPENAI_KEY"), model_name=os.getenv("EMBEDDING_MODEL"))
 collection = chroma_client.create_collection(name="conversations", embedding_function=embedding_function)
 current_id = 0
 while True:
 chat_history = []
 chat_metadata = []
 history_ids = []

 messages=[
 {"role": "system", "content": "You are a kind and wise wizard"}
 ]
 input_text = input("You: ")
 if input_text.lower() == "quit":
 break

 results = collection.query(
 query_texts=[input_text],
 where={"role": "assistant"},
 n_results=2
 )

 # append the query result into the messages
 for res in results['documents'][0]:
 messages.append({"role": "user", "content": f"previous chat: {res}"})

 # append user input at the end of conversation chain
 messages.append({"role": "user", "content": input_text})
 response = generate_response(messages)

 chat_metadata.append({"role":"user"})
 chat_history.append(input_text)
 chat_metadata.append({"role":"assistant"})
 chat_history.append(response['content'])
 current_id += 1
 history_ids.append(f"id_{current_id}")
 current_id += 1
 history_ids.append(f"id_{current_id}")
 collection.add(
 documents=chat_history,
 metadatas=chat_metadata,
 ids=history_ids
 )
 print(f"Wizard: {response['content']}")

if __name__ == "__main__":
 main()

## Тред: Как сделать так, чтобы GPT API (Chat-GPT) запоминал контекст разговора в чате телеграм?

- question_id: 1558305
- URL: https://ru.stackoverflow.com/questions/1558305/%d0%9a%d0%b0%d0%ba-%d1%81%d0%b4%d0%b5%d0%bb%d0%b0%d1%82%d1%8c-%d1%82%d0%b0%d0%ba-%d1%87%d1%82%d0%be%d0%b1%d1%8b-gpt-api-chat-gpt-%d0%b7%d0%b0%d0%bf%d0%be%d0%bc%d0%b8%d0%bd%d0%b0%d0%bb-%d0%ba%d0%be%d0%bd%d1%82%d0%b5%d0%ba%d1%81%d1%82-%d1%80%d0%b0%d0%b7%d0%b3%d0%be%d0%b2%d0%be%d1%80%d0%b0-%d0%b2-%d1%87%d0%b0%d1%82%d0%b5-%d1%82%d0%b5
- Теги: python, aiogram-3.x, python-openai, chatgpt-api
- Автор вопроса: user578345 (https://ru.stackoverflow.com/users/578345/user578345)
- Рейтинг вопроса: 0
- Ответов в исходном треде: 1
- Лицензия: CC BY-SA 4.0

### Вопрос

Я делаю бота (проект по практике) с GPT API и промтом для него. Но проблема в том, что он отвечает только на контекст вопроса одного сообщения, а не целого диалога. Помогите исправить. Пишу на пайтоне. Вот код:

Блок кода:

@dp.message()
async def gpt_reply(message: types.Message, chat_context: list):
 completion = client.chat.completions.create(
 model="gpt-3.5-turbo",
 messages=[{"role": "system", "content": "You are helpful chat gpt bot in telegram"},
 {"role": "user", "content": message.text}
 ]
 )
 for i in range(1):
 chat_context.append({"role": "user", "content": message.text})
 chat_context.append({"role": "assistant", "content": gpt_reply(chat_context)})

 openai_reply = (completion.choices[0].message)
 await message.answer(openai_reply)

async def main():
 await dp.start_polling(bot, chat_context=[])

if __name__ == "__main__":
 asyncio.run(main())

 Я понимаю, что лучше использовать while вместо for i in range, но это пока что просто черновик. Хочу понять как мне сделать "запоминание контекста" для бота.

 Диспетчер и прочее установлено и подключено

### Ответ 1558435

- Автор ответа: JustAQ (https://ru.stackoverflow.com/users/578409/justaq)
- Рейтинг ответа: 0
- Принят: нет
- URL ответа: https://ru.stackoverflow.com/a/1558435
- Лицензия: CC BY-SA 4.0

При запросе на сервера OpenAI вы передаете параметр `messages` в который вы передаете список сообщений в чате. Если вы хотите сохранять контекст вам нужно передавать туда предыдущие сообщения пользователя
