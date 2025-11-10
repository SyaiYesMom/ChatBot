import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.request import HTTPXRequest
from config import config
from tele.start import start
from feature.chat import chat
from tele.errors import error_handler
from feature.voice import voice_message
from feature.image import image_message
from feature.wiki import handle_wiki_command
from feature.cuaca import (
    handle_weather_command,
    handle_forecast_command,
    handle_astronomy_command
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

def main():
    # Perbesar timeout request ke Telegram agar tidak mudah TimedOut saat kirim pesan
    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=90.0,
        write_timeout=90.0,
    )
    app = Application.builder().token(config.TELEGRAM_TOKEN).request(request).build()

    app.add_handler(CommandHandler("start", start))
    
    # Wiki command
    app.add_handler(CommandHandler("wiki", handle_wiki_command))
    
    # Weather commands
    app.add_handler(CommandHandler("cuaca", handle_weather_command))
    app.add_handler(CommandHandler("ramalan", handle_forecast_command))
    app.add_handler(CommandHandler("astronomi", handle_astronomy_command))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.add_handler(MessageHandler(filters.VOICE, voice_message))
    # Handler untuk foto dan document gambar (JPG, PNG, RAW, dll)
    app.add_handler(MessageHandler(filters.PHOTO, image_message))
    app.add_handler(MessageHandler(filters.Document.IMAGE, image_message))
    app.add_error_handler(error_handler)

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
