import logging
from io import BytesIO
from telegram import Update
from telegram.ext import ContextTypes
from parse import parshing
from tele.ai import model


async def voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.voice:
        return

    try:
        file = await update.message.voice.get_file()
        buffer = BytesIO()
        await file.download_to_memory(out=buffer)
        audio_bytes = buffer.getvalue()

        response = model.generate_content([
            {
                "mime_type": "audio/ogg",
                "data": audio_bytes,
            },
            (
                "Transkripsikan audio, pahami maksudnya, lalu berikan HANYA jawaban akhir. "
                "Jangan tampilkan label seperti 'Transkripsi:', 'Maksud:', atau 'Jawaban:'. "
                "Balas secara terperinci, dan dalam bahasa Indonesia."
            ),
        ])

        text = response.text or "(tidak ada hasil)"
        final_text = _extract_final_answer(text)
        parsed_text = parshing.remove_bold_and_header(final_text)
        await update.message.reply_text(parsed_text)

    except Exception as e:
        logging.error(f"Error handling voice message: {e}")
        await update.message.reply_text("❌ Maaf, terjadi error saat memproses pesan suara kamu.")


def _extract_final_answer(text: str) -> str:
    """Ambil hanya jawaban akhir, hilangkan label Transkripsi/Maksud/Jawaban.
    Prioritas: jika ada 'Jawaban:', ambil bagian setelahnya. Jika tidak, bersihkan label-label tersebut.
    """
    try:
        import re

        # Jika ada 'Jawaban:' → ambil sesudahnya
        parts = re.split(r"(?i)jawaban\s*:\s*", text, maxsplit=1)
        if len(parts) == 2:
            candidate = parts[1].strip().strip('"\'`').strip()
            return candidate or text

        # Jika tidak ada, hapus baris label di awal baris
        cleaned = re.sub(r"(?im)^\s*(transkripsi|maksud|jawaban)\s*:\s*", "", text)
        cleaned = cleaned.strip().strip('"\'`').strip()
        return cleaned or text
    except Exception:
        return text

