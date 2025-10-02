import telebot
import os
import requests

# === Получаем токены ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")  # Новый ключ

# Проверка
if not TELEGRAM_TOKEN:
    print("❌ ОШИБКА: Не найден TELEGRAM_TOKEN")
if not DEEPSEEK_API_KEY:
    print("❌ ОШИБКА: Не найден DEEPSEEK_API_KEY")

# Инициализация бота
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Обработчик /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "🤖 Привет! Я — SEO/UX-аудит бот.\n\n"
        "Отправь:\n"
        "`/аудит https://ваш-сайт.com`\n"
        "— и получи бесплатный отчёт за 1 минуту.",
        parse_mode="Markdown"
    )

# Обработчик /аудит
@bot.message_handler(commands=['аудит'])
def audit(message):
    try:
        url = message.text.split()[1]
    except IndexError:
        bot.reply_to(
            message,
            "❌ Укажите URL после команды.\nПример:\n`/аудит https://example.com`",
            parse_mode="Markdown"
        )
        return

    bot.send_message(message.chat.id, "🔍 Генерирую SEO/UX-аудит для сайта: " + url)

    # Генерация отчёта через DeepSeek
    try:
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": f"Проанализируй сайт {url} и дай 10 SEO/UX рекомендаций. "
                                           "Формат: Номер. [Категория] — Заголовок • Проблема: ... • Решение: ..."}
            ],
            "max_tokens": 800
        }
        response = requests.post("https://api.deepseek.com/v1/chat/completions", json=data, headers=headers)
        result = response.json()
        report = result['choices'][0]['message']['content']
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка при генерации отчёта: {e}")
        return

    # Отправка отчёта
    try:
        bot.send_message(message.chat.id, f"📌 *SEO/UX Аудит сайта {url}:*\n\n{report}", parse_mode="Markdown")
    except:
        for i in range(0, len(report), 3500):
            bot.send_message(message.chat.id, report[i:i+3500])

    # Призыв к действию
    bot.send_message(
        message.chat.id,
        "✅ Аудит завершён!\n\n"
        "📩 Хотите глубокий анализ?\n"
        "Напишите мне: @ваш_ник"
    )

print("🚀 Бот запущен...")
bot.polling(none_stop=True)
