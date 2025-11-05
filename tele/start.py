from telegram import Update
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! Aku chatbot berbasis AI\nYang dibikin kelompok 6 >///<\n"
        "Kalau kamu butuh bantuan, bilang yaa :3\n"
    )


