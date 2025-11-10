import logging
from telegram import Update
from telegram.ext import ContextTypes
from parse import parshing
from feature.ai import model
from tele.utils import safe_reply


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    try:
        response = model.generate_content(user_message)
        text = response.text or ""
        parsed_response = parshing.remove_bold_and_header(text)
        await safe_reply(update, parsed_response)
    except Exception as e:
        await safe_reply(update, f"❌ Maaf, terjadi error: {str(e)}")
        logging.error(f"Error in chat function: {str(e)}")


