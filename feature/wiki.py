import logging
import wikipedia
from telegram import Update
from telegram.ext import ContextTypes


# Set bahasa Wikipedia ke Indonesia
wikipedia.set_lang("id")


async def handle_wiki_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /wiki - mencari di Wikipedia"""
    try:
        if not context.args:
            await update.message.reply_text(
                "📚 <b>Search Wikipedia</b>\n\n"
                "Gunakan format:\n"
                "/wiki [pertanyaan]\n\n"
                "Contoh:\n"
                "/wiki Python\n"
                "/wiki Jakarta\n"
                "/wiki Artificial Intelligence",
                parse_mode="HTML"
            )
            return
        
        query = " ".join(context.args)
        await update.message.reply_text(f"⏳ Mencari '{query}' di Wikipedia...")
        
        try:
            # Cari halaman Wikipedia
            page = wikipedia.page(query, auto_suggest=False)
            
            # Ambil summary
            summary = page.summary
            
            # Batasi panjang teks untuk Telegram (max ~4096 karakter)
            max_length = 3500
            if len(summary) > max_length:
                summary = summary[:max_length] + "..."
            
            # Format pesan
            message = f"📚 <b>{page.title}</b>\n\n"
            message += f"{summary}\n\n"
            message += f"🔗 <a href='{page.url}'>Baca lebih lanjut di Wikipedia</a>"
            
            await update.message.reply_text(message, parse_mode="HTML", disable_web_page_preview=False)
            
        except wikipedia.exceptions.DisambiguationError as e:
            # Jika ada beberapa pilihan
            options = e.options[:10]  # Ambil 10 pilihan pertama
            message = f"🔍 <b>Beberapa hasil ditemukan untuk '{query}':</b>\n\n"
            for i, option in enumerate(options, 1):
                message += f"{i}. {option}\n"
            message += f"\n💡 Coba gunakan kata kunci yang lebih spesifik!"
            
            await update.message.reply_text(message, parse_mode="HTML")
            
        except wikipedia.exceptions.PageError:
            await update.message.reply_text(
                f"❌ Halaman '{query}' tidak ditemukan di Wikipedia.\n\n"
                f"💡 Coba gunakan kata kunci yang berbeda atau lebih spesifik."
            )
            
        except Exception as e:
            logging.error(f"Error in handle_wiki_command: {str(e)}")
            await update.message.reply_text(
                f"❌ Terjadi error saat mencari di Wikipedia: {str(e)}"
            )
            
    except Exception as e:
        logging.error(f"Error in handle_wiki_command: {str(e)}")
        await update.message.reply_text(f"❌ Error: {str(e)}")

