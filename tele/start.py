import os
from telegram import Update
from telegram.ext import ContextTypes
from html import escape


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /start - menampilkan daftar command dari menu.txt"""
    try:
        # Path ke file menu.txt di folder tele
        menu_file_path = os.path.join(os.path.dirname(__file__), "menu.txt")
        
        # Baca isi file menu.txt
        with open(menu_file_path, "r", encoding="utf-8") as f:
            commands = f.read().strip()
        
        # Format pesan dengan header (escape HTML untuk menghindari parsing error)
        message = "<b>Halo! Aku chatbot berbasis AI</b>\n"
        message += f"<b>Yang dibikin kelompok 6 {escape('>///<')}</b>\n"
        message += "<b>Daftar Command yang Tersedia:</b>\n"
        message += escape(commands)
        
        await update.message.reply_text(message, parse_mode="HTML")
        
    except Exception as e:
        # Fallback jika ada error membaca file
        await update.message.reply_text(
            f"Error Command: {escape(str(e))}\n"
        )


