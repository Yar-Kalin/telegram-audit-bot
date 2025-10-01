import telebot
from openai import OpenAI
import gspread
from oauth2client.service_account import SignedJwtAssertionCredentials
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
import json
import os

# === НАСТРОЙКИ ===
TELEGRAM_TOKEN = os.getenv("8324684049:AAHgau8u2GpP4yeiy_zmpq4ZMoo8FWIenUw")
OPENAI_API_KEY = os.getenv("")

# Получаем JSON-ключ из переменной окружения
google_creds_json = os.getenv("audit-bot@audit-bot-473810.iam.gserviceaccount.com")
if not google_creds_json:
    print("Ошибка: GOOGLE_CREDS не найден в Secrets")
else:
    try:
        google_creds_dict = json.loads(google_creds_json)
    except Exception as e:
        print(f"Ошибка парсинга GOOGLE_CREDS: {e}")

# Инициализация бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Подключение к Google Таблицам
def get_sheet():
    try:
        scopes = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(google_creds_dict, scopes=scopes)
        gc = gspread.authorize(creds)
        sh = gc.open("SEO_Audit_Logs").sheet1
        return sh
    except Exception as e:
        print(f"Ошибка подключения к Google Таблицам: {e}")
        return None

# === ОБРАБОТКА КОМАНД ===
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🤖 Привет! Я — AuditBot.\n\nОтправь команду:\n`/аудит https://ваш-сайт.com` — и получи SEO/UX-аудит за 1 минуту.", parse_mode="Markdown")

@bot.message_handler(commands=['аудит'])
def audit(message):
    try:
        url = message.text.split()[1]
    except IndexError:
        bot.reply_to(message, "❌ Ошибка: после `/аудит` укажите URL сайта.\nПример: `/аудит https://example.com`")
        return

    bot.send_message(message.chat.id, "🔍 Анализирую сайт... Это займёт 30–60 секунд.")

    # Генерация отчёта через ChatGPT
    prompt = f"""
    Ты — эксперт по SEO и UX для малого бизнеса. Проанализируй сайт {url} и дай 15 пунктов для роста конверсии.
    Формат:
    1. [Категория: SEO/UX/Контент] — [Короткое название]
    • Проблема: [1 предложение]
    • Решение: [1 предложение]
    • Срок: [менее 1 дня / 3 дня / неделя]
    • Инструмент: [бесплатный AI-инструмент]
    """

    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000
        )
        report = response.choices[0].message.content
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка генерации отчёта: {e}")
        return

    # Сохранение в Google Таблицу
    sheet = get_sheet()
    if sheet:
        try:
            sheet.append_row([
                message.from_user.id,
                message.from_user.username or "",
                url,
                message.date,
                report[:50000]  # Ограничение длины
            ])
            bot.send_message(message.chat.id, "📊 Данные сохранены в таблицу.")
        except Exception as e:
            bot.send_message(message.chat.id, f"⚠️ Не удалось сохранить в таблицу: {e}")

    # Отправка отчёта пользователю
    try:
        bot.send_message(message.chat.id, f"📌 *SEO/UX Аудит сайта {url}:*\n\n{report}", parse_mode="Markdown")
    except:
        # Если слишком длинный — разбиваем
        for i in range(0, len(report), 3500):
            part = report[i:i+3500]
            bot.send_message(message.chat.id, part)

    # Платёжная ссылка
    payment_link = "https://buy.stripe.com/ваша-ссылка"  # ← Замените на свою
    bot.send_message(message.chat.id, f"✅ Готово! Спасибо за доверие.\n👉 Оплатите аудит: {payment_link}")

# === ЗАПУСК БОТА ===
print("Бот запущен...")
bot.polling(none_stop=True)
