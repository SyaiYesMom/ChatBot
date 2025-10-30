import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import config
from parse import parshing

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
genai.configure(api_key=config.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! Aku chatbot berbasis AI\nYang dibikin kelompok 6 >///<\n"
        "Kalau kamu butuh bantuan, bilang yaa :3\n"
    )

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    try:
        response = model.generate_content(user_message)
        parsed_response = parshing.remove_bold_and_header(response.text)
        await update.message.reply_text(parsed_response)
    except Exception as e:
        await update.message.reply_text(f"❌ Maaf, terjadi error: {str(e)}")
        logging.error(f"Error in chat function: {str(e)}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Exception while handling an update: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("❌ Terjadi error yang tidak terduga. Silakan coba lagi.")

def main():
    app = Application.builder().token(config.TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.add_error_handler(error_handler)

    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
