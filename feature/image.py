import logging
from io import BytesIO
from telegram import Update
from telegram.ext import ContextTypes
from parse import parshing
from feature.ai import model
from tele.utils import safe_reply


async def image_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk memproses gambar yang dikirim user dari Telegram"""
    if not update.message:
        return
    
    # Cek apakah ada foto atau document dengan format gambar
    photo = update.message.photo
    document = update.message.document
    
    try:
        image_bytes = None
        mime_type = None
        caption = update.message.caption or ""
        
        # Jika user mengirim foto langsung (Telegram otomatis compress)
        if photo:
            # Ambil foto dengan kualitas tertinggi (foto terakhir dalam array)
            file = await photo[-1].get_file()
            buffer = BytesIO()
            await file.download_to_memory(out=buffer)
            image_bytes = buffer.getvalue()
            mime_type = "image/jpeg"  # Telegram selalu compress foto ke JPEG
        
        # Jika user mengirim sebagai document (untuk format raw atau PNG asli)
        elif document:
            # Cek apakah document adalah file gambar JPG/PNG
            file_name = document.file_name or ""
            mime_type_doc = document.mime_type or ""
            
            # Daftar format gambar yang didukung
            supported_formats = {
                "image/jpeg": "image/jpeg",
                "image/jpg": "image/jpeg",
                "image/png": "image/png",
            }
            
            # Cek berdasarkan mime_type atau ekstensi file
            is_image = False
            if mime_type_doc in supported_formats:
                mime_type = supported_formats[mime_type_doc]
                is_image = True
            elif any(file_name.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png"]):
                # Tentukan mime_type berdasarkan ekstensi
                ext = file_name.lower().split(".")[-1]
                mime_map = {
                    "jpg": "image/jpeg",
                    "jpeg": "image/jpeg",
                    "png": "image/png",
                }
                mime_type = mime_map.get(ext, "image/jpeg")
                is_image = True
            
            if is_image:
                file = await document.get_file()
                buffer = BytesIO()
                await file.download_to_memory(out=buffer)
                image_bytes = buffer.getvalue()
            else:
                await safe_reply(
                    update,
                    "❌ Format file tidak didukung. Kirim gambar dalam format JPG atau PNG.",
                )
                return
        
        # Jika tidak ada gambar yang ditemukan
        if not image_bytes or not mime_type:
            return
        
        # Siapkan prompt untuk Gemini
        if caption:
            # Jika ada caption, gunakan sebagai instruksi tambahan
            prompt = (
                f"Analisis gambar ini dan ikuti instruksi berikut: {caption}\n\n"
                "Berikan jawaban yang detail dan informatif dalam bahasa Indonesia. "
                "Jika diminta untuk menjelaskan gambar, jelaskan dengan lengkap. "
                "Jika diminta untuk membaca teks dalam gambar, tuliskan semua teks yang terlihat."
            )
        else:
            # Jika tidak ada caption, analisis umum
            prompt = (
                "Analisis gambar ini secara detail. Jelaskan apa yang kamu lihat, "
                "termasuk objek, teks (jika ada), warna, komposisi, dan konteksnya. "
                "Berikan penjelasan yang informatif dalam bahasa Indonesia."
            )
        
        # Kirim ke Gemini Vision API
        response = model.generate_content([
            {
                "mime_type": mime_type,
                "data": image_bytes,
            },
            prompt,
        ])
        
        # Ambil response text
        text = response.text or "❌ Maaf, tidak dapat memproses gambar ini."
        
        # Bersihkan formatting markdown
        parsed_text = parshing.remove_bold_and_header(text)
        
        # Kirim response ke user (aman dari limit pesan)
        await safe_reply(update, parsed_text)
        
    except Exception as e:
        logging.error(f"Error handling image message: {e}", exc_info=True)
        await safe_reply(
            update,
            "❌ Maaf, terjadi error saat memproses gambar kamu. "
            "Pastikan gambar tidak terlalu besar atau formatnya didukung.",
        )

