import os

print("DEBUG: TELEGRAM_TOKEN =", repr(os.getenv("TELEGRAM_TOKEN")))
print("DEBUG: OPENAI_API_KEY =", repr(os.getenv("OPENAI_API_KEY")))
print("DEBUG: GOOGLE_CREDS length =", len(os.getenv("GOOGLE_CREDS")) if os.getenv("GOOGLE_CREDS") else None)
