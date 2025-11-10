import google.generativeai as genai
from config import config

# Konfigurasi API dan inisialisasi model Gemini
genai.configure(api_key=config.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")


