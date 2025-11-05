import logging
from telegram import Update
from telegram.ext import ContextTypes


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Exception while handling an update: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("❌ Terjadi error yang tidak terduga. Silakan coba lagi.")


