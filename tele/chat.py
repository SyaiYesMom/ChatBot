import logging
from telegram import Update
from telegram.ext import ContextTypes
from parse import parshing
from feature.ai import model


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    try:
        response = model.generate_content(user_message)
        parsed_response = parshing.remove_bold_and_header(response.text)
        await update.message.reply_text(parsed_response)
    except Exception as e:
        await update.message.reply_text(f"❌ Maaf, terjadi error: {str(e)}")
        logging.error(f"Error in chat function: {str(e)}")


