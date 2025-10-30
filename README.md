ChatBot ini memanfaatkan teknologi Google Gemini AI untuk percakapan cerdas, natural, dan responsif. Terintegrasi langsung dengan Telegram, serta mampu menghilangkan formatting **bold** dan header dari output Gemini sebelum mengirim ke user.

## Fitur Utama

🎯 Respons kontekstual & pintar (Google Gemini)

📱 Integrasi Telegram

✅ Hasil respons langsung difilter (tanpa bold dan header)

🔧 Mudah dikustomisasi dan diperluas.

## Struktur Direktori (Terbaru)

```bash
ChatBot/
├── chatbot.py            # Logika utama bot & alur percakapan
├── requirement.txt       # Daftar dependensi project
├── README.md
├── config/
│   └── config.py         # Pengaturan API, token, dan konfigurasi
├── parse/
│   └── parshing.py       # Fungsi filter bold + header (hilangkan formatting markdown)
└── ...                   # File dan folder tambahan
```

## Prasyarat

- Token Telegram Bot dari BotFather
- API Key Google Gemini
- Python 3.8+

## Instalasi & Konfigurasi

### 1. Clone repositori
```bash
git clone https://github.com/SyaiYesMom/ChatBot.git
cd ChatBot
```

### 2. (Opsional) Buat virtual environment
```bash
python -m venv venv
# Linux/Mac
source venv/bin/activate
# Windows
venv\Scripts\activate
```

### 3. Install semua dependensi
```bash
pip install -r requirement.txt
```

### 4. Konfigurasi kredensial
Edit file:
- `config/config.py` → masukkan TELEGRAM_TOKEN dan GEMINI_API_KEY

### 5. Jalankan bot
```bash
python chatbot.py
```

## Penjelasan Fitur Filtering (Parse)
Hasil respons Gemini akan otomatis di-filter menggunakan fungsi di `parse/parshing.py` agar bold (`**...**`, `*...*`) dan header markdown (`# ...`) dihapus sebelum dikirim ke user Telegram.

## Cara Penggunaan
- Start bot di Telegram → kirim pesan apa saja, bot akan balas dengan teks yang sudah difilter formatting-nya.

## Pengembangan lebih lanjut
- Tambahkan command/fitur baru di `chatbot.py`
- Modifikasi logika filter di `parse/parshing.py` jika ingin aturan pemformatan berbeda
- Dapat diintegrasikan dengan layanan eksternal (API cuaca, dsb.) sesuai kebutuhan
