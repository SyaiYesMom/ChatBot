import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import config
from tele.start import start
from tele.chat import chat
from tele.errors import error_handler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

def main():
    app = Application.builder().token(config.TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.add_error_handler(error_handler)

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
