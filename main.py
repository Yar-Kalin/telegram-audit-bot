import telebot
import openai
import gspread
import os
import json
from google.oauth2.service_account import Credentials

# === Получаем токены из переменных окружения ===
TELEGRAM_TOKEN = os.getenv("8324684049:AAHgau8u2GpP4yeiy_zmpq4ZMoo8FWIenUw")
OPENAI_API_KEY = os.getenv("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")
GOOGLE_CREDS_JSON = os.getenv("audit-bot@audit-bot-473810.iam.gserviceaccount.com")

if not TELEGRAM_TOKEN:
    print("❌ ОШИБКА: Не найден TELEGRAM_TOKEN")
if not OPENAI_API_KEY:
    print("❌ ОШИБКА: Не найден OPENAI_API_KEY")
if not GOOGLE_CREDS_JSON:
    print("❌ ОШИБКА: Не найден GOOGLE_CREDS")
else:
    try:
        creds_dict = json.loads(GOOGLE_CREDS_JSON)
        print("✅ Google Credentials загружены")
    except Exception as e:
        print(f"❌ Ошибка парсинга JSON: {e}")

# Инициализация бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Функция для подключения к Google Таблице
def get_google_sheet():
    try:
        scopes = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        credentials = Credentials.from_service_account_info(json.loads(GOOGLE_CREDS_JSON), scopes=scopes)
        client = gspread.authorize(credentials)
        sheet = client.open("SEO_Audit_Logs").sheet1  # Убедитесь, что таблица называется именно так
        return sheet
    except Exception as e:
        print(f"❌ Ошибка подключения к Google Таблице: {e}")
        return None

# Обработчик /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "🤖 Привет! Я — SEO/UX-аудит бот.\n\n"
        "Отправь команду:\n"
        "`/аудит https://ваш-сайт.com`\n"
        "— и получи отчёт бесплатно за 1 минуту.",
        parse_mode="Markdown"
    )

# Обработчик /аудит
@bot.message_handler(commands=['аудит'])
def audit(message):
    try:
        url = message.text.split()[1]
    except IndexError:
        bot.reply_to(message, "❌ Укажите URL после команды. Пример:\n`/аудит https://example.com`", parse_mode="Markdown")
        return

    bot.send_message(message.chat.id, "🔍 Генерирую SEO/UX-аудит для сайта: " + url)

    # Генерация отчёта через ChatGPT
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "user",
                "content": f"Проанализируй сайт {url} и дай 10 SEO/UX рекомендаций. "
                           "Формат: Номер. [Категория] — Заголовок • Проблема: ... • Решение: ..."
            }],
            max_tokens=800
        )
        report = response.choices[0].message.content
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка при генерации отчёта: {e}")
        return

    # Сохранение в Google Таблицу
    sheet = get_google_sheet()
    if sheet:
        try:
            sheet.append_row([
                message.from_user.id,
                message.from_user.username or "",
                url,
                message.date,
                report[:5000]  # Ограничение длины
            ])
            bot.send_message(message.chat.id, "📊 Данные сохранены в Google Таблицу.")
        except Exception as e:
            bot.send_message(message.chat.id, f"⚠️ Не удалось сохранить в таблицу: {e}")

    # Отправка отчёта пользователю
    try:
        bot.send_message(message.chat.id, f"📌 *SEO/UX Аудит сайта {url}:*\n\n{report}", parse_mode="Markdown")
    except:
        for i in range(0, len(report), 3500):
            bot.send_message(message.chat.id, report[i:i+3500])

    # Призыв к действию (без оплаты)
    bot.send_message(
        message.chat.id,
        "✅ Аудит завершён!\n\n"
        "📩 Хотите PDF-версию или глубокий анализ?\n"
        "Напишите мне в личные сообщения: @ваш_ник\n"
        "Готов помочь с улучшением вашего сайта!"
    )

# === ЗАПУСК БОТА ===
print("🚀 Попытка запустить бота...")
bot.polling(none_stop=True)
