import logging
import httpx
import asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from config import config

# Timeout configuration untuk httpx (dalam detik)
TIMEOUT = 30.0


class WeatherAPI:
    """Class untuk mengelola semua fungsi WeatherAPI.com"""
    
    BASE_URL = "https://api.weatherapi.com/v1"
    
    def __init__(self):
        self.api_key = config.WEATHER_API_KEY
        self.timeout = TIMEOUT
        # Buat client httpx dengan konfigurasi default
        self.client = httpx.AsyncClient(
            timeout=TIMEOUT,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            },
            follow_redirects=True,
            verify=True  # SSL verification enabled by default
        )
    
    async def close(self):
        """Menutup client httpx"""
        await self.client.aclose()
    
    async def _make_request(self, url: str, params: dict, retry_count: int = 3) -> dict:
        """Helper method untuk membuat HTTP request dengan retry logic menggunakan httpx"""
        last_error = None
        
        for attempt in range(retry_count + 1):
            try:
                # Jika ada masalah SSL pada percobaan sebelumnya, coba tanpa verification
                if attempt > 0 and last_error:
                    error_str = str(last_error).lower()
                    if any(keyword in error_str for keyword in ["ssl", "certificate", "443", "connect"]):
                        logging.warning(f"Masalah koneksi terdeteksi, mencoba tanpa SSL verification (percobaan {attempt + 1}/{retry_count + 1})...")
                        # Buat client sementara tanpa SSL verification
                        temp_client = httpx.AsyncClient(
                            timeout=self.timeout,
                            headers={
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                                'Accept': 'application/json'
                            },
                            follow_redirects=True,
                            verify=False  # Disable SSL verification sebagai fallback
                        )
                        try:
                            response = await temp_client.get(url, params=params)
                            response.raise_for_status()
                            return response.json()
                        finally:
                            await temp_client.aclose()
                
                # Request normal dengan SSL verification
                response = await self.client.get(url, params=params)
                response.raise_for_status()  # Raise exception untuk status code error
                return response.json()
                
            except httpx.ConnectError as e:
                last_error = e
                if attempt < retry_count:
                    wait_time = 1 + attempt
                    logging.warning(f"Koneksi gagal, mencoba lagi dalam {wait_time} detik ({attempt + 1}/{retry_count + 1}): {str(e)}")
                    await asyncio.sleep(wait_time)
                    continue
                raise Exception(f"Koneksi gagal setelah {retry_count + 1} percobaan: Tidak dapat terhubung ke server WeatherAPI. Pastikan koneksi internet server stabil dan firewall mengizinkan koneksi ke api.weatherapi.com:443")
            
            except httpx.TimeoutException as e:
                last_error = e
                if attempt < retry_count:
                    wait_time = 1 + attempt
                    logging.warning(f"Timeout, mencoba lagi dalam {wait_time} detik ({attempt + 1}/{retry_count + 1}): {str(e)}")
                    await asyncio.sleep(wait_time)
                    continue
                raise Exception(f"Timeout setelah {retry_count + 1} percobaan: Server WeatherAPI tidak merespons. Silakan coba lagi nanti.")
            
            except httpx.HTTPStatusError as e:
                # Error dari API (bukan koneksi)
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                except:
                    error_msg = e.response.text
                raise Exception(f"API Error: {error_msg}")
            
            except Exception as e:
                last_error = e
                if attempt < retry_count:
                    wait_time = 1 + attempt
                    logging.warning(f"Error, mencoba lagi dalam {wait_time} detik ({attempt + 1}/{retry_count + 1}): {str(e)}")
                    await asyncio.sleep(wait_time)
                    continue
                raise Exception(f"Error setelah {retry_count + 1} percobaan: {str(e)}")
        
        raise Exception(f"Gagal mendapatkan data setelah {retry_count + 1} percobaan: {str(last_error)}")
    
    async def get_current_weather(self, location: str, retry_count: int = 3) -> dict:
        """Mendapatkan cuaca saat ini untuk lokasi tertentu"""
        url = f"{self.BASE_URL}/current.json"
        params = {
            "key": self.api_key,
            "q": location,
            "aqi": "yes",  # Include air quality data
            "alerts": "yes"  # Include weather alerts
        }
        return await self._make_request(url, params, retry_count)
    
    async def get_forecast(self, location: str, days: int = 3, retry_count: int = 3) -> dict:
        """Mendapatkan ramalan cuaca untuk beberapa hari ke depan (1-14 hari)"""
        url = f"{self.BASE_URL}/forecast.json"
        params = {
            "key": self.api_key,
            "q": location,
            "days": min(days, 14),  # Max 14 days
            "aqi": "yes",
            "alerts": "yes"
        }
        return await self._make_request(url, params, retry_count)
    
    async def get_history(self, location: str, date: str, retry_count: int = 3) -> dict:
        """Mendapatkan data cuaca historis untuk tanggal tertentu"""
        url = f"{self.BASE_URL}/history.json"
        params = {
            "key": self.api_key,
            "q": location,
            "dt": date,  # Format: YYYY-MM-DD
            "aqi": "yes"
        }
        return await self._make_request(url, params, retry_count)
    
    async def get_astronomy(self, location: str, date: str = None, retry_count: int = 3) -> dict:
        """Mendapatkan data astronomi (sunrise, sunset, moon phase, dll)"""
        url = f"{self.BASE_URL}/astronomy.json"
        params = {
            "key": self.api_key,
            "q": location
        }
        if date:
            params["dt"] = date
        return await self._make_request(url, params, retry_count)
    
    async def search_location(self, query: str, retry_count: int = 2) -> list:
        """Mencari lokasi berdasarkan nama kota/lokasi"""
        url = f"{self.BASE_URL}/search.json"
        params = {
            "key": self.api_key,
            "q": query
        }
        
        try:
            return await self._make_request(url, params, retry_count)
        except Exception as e:
            logging.error(f"Search error: {str(e)}")
            return []
    
    async def get_marine_weather(self, location: str, days: int = 3, retry_count: int = 3) -> dict:
        """Mendapatkan data cuaca maritim (untuk lokasi pantai/laut)"""
        url = f"{self.BASE_URL}/marine.json"
        params = {
            "key": self.api_key,
            "q": location,
            "days": min(days, 3)
        }
        return await self._make_request(url, params, retry_count)


# Instance global untuk digunakan di handler
weather_api = WeatherAPI()




def format_current_weather(data: dict) -> str:
    """Format data cuaca saat ini menjadi format yang mudah dibaca"""
    try:
        location = data.get("location", {})
        current = data.get("current", {})
        condition = current.get("condition", {})
        aqi = current.get("air_quality", {})
        
        # Format location
        loc_name = location.get("name", "Unknown")
        loc_region = location.get("region", "")
        loc_country = location.get("country", "")
        localtime = location.get("localtime", "")
        
        # Format cuaca
        temp_c = current.get("temp_c", "N/A")
        temp_f = current.get("temp_f", "N/A")
        feelslike_c = current.get("feelslike_c", "N/A")
        condition_text = condition.get("text", "Unknown")
        humidity = current.get("humidity", "N/A")
        wind_kph = current.get("wind_kph", "N/A")
        wind_dir = current.get("wind_dir", "N/A")
        pressure_mb = current.get("pressure_mb", "N/A")
        uv = current.get("uv", "N/A")
        vis_km = current.get("vis_km", "N/A")
        precip_mm = current.get("precip_mm", "N/A")
        
        # Format air quality
        air_quality_text = ""
        if aqi:
            us_epa_index = aqi.get("us-epa-index", 0)
            quality_levels = ["Baik", "Sedang", "Tidak Sehat untuk Sensitif", "Tidak Sehat", "Sangat Tidak Sehat", "Berbahaya"]
            quality_level = quality_levels[min(us_epa_index, 5)] if us_epa_index else "Tidak tersedia"
            pm2_5 = aqi.get("pm2_5", "N/A")
            pm10 = aqi.get("pm10", "N/A")
            air_quality_text = f"\n🌬️ Kualitas Udara: {quality_level}"
            air_quality_text += f"\n   PM2.5: {pm2_5} μg/m³ | PM10: {pm10} μg/m³"
        
        # Build message
        message = f"🌤️ <b>CUACA SAAT INI</b>\n"
        message += f"📍 <b>{loc_name}</b>"
        if loc_region:
            message += f", {loc_region}"
        message += f", {loc_country}\n"
        message += f"🕐 {localtime}\n"
        message += f"\n🌡️ <b>Suhu:</b> {temp_c}°C ({temp_f}°F)"
        message += f"\n❄️ <b>Terasa:</b> {feelslike_c}°C"
        message += f"\n{condition_text}"
        message += f"\n💧 <b>Kelembaban:</b> {humidity}%"
        message += f"\n💨 <b>Angin:</b> {wind_kph} km/h ({wind_dir})"
        message += f"\n📊 <b>Tekanan:</b> {pressure_mb} mb"
        message += f"\n☀️ <b>UV Index:</b> {uv}"
        message += f"\n👁️ <b>Visibilitas:</b> {vis_km} km"
        if float(precip_mm) > 0:
            message += f"\n🌧️ <b>Curah Hujan:</b> {precip_mm} mm"
        
        if air_quality_text:
            message += air_quality_text
        
        return message
        
    except Exception as e:
        logging.error(f"Error formatting current weather: {str(e)}")
        return f"❌ Error memformat data cuaca: {str(e)}"


def format_forecast(data: dict) -> str:
    """Format data ramalan cuaca menjadi format yang mudah dibaca"""
    try:
        location = data.get("location", {})
        forecast = data.get("forecast", {})
        forecastday = forecast.get("forecastday", [])
        
        loc_name = location.get("name", "Unknown")
        loc_country = location.get("country", "")
        
        message = f"📅 <b>RAMALAN CUACA</b>\n"
        message += f"📍 <b>{loc_name}</b>, {loc_country}\n\n"
        
        for day_data in forecastday[:7]:  # Tampilkan maksimal 7 hari
            date = day_data.get("date", "")
            day = day_data.get("day", {})
            condition = day.get("condition", {})
            
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            day_name = date_obj.strftime("%A")
            
            maxtemp_c = day.get("maxtemp_c", "N/A")
            mintemp_c = day.get("mintemp_c", "N/A")
            condition_text = condition.get("text", "")
            chance_of_rain = day.get("daily_chance_of_rain", 0)
            humidity = day.get("avghumidity", "N/A")
            
            message += f"📆 <b>{day_name}</b> ({date})\n"
            message += f"   🌡️ {mintemp_c}°C - {maxtemp_c}°C"
            message += f"\n   {condition_text}"
            message += f"\n   🌧️ Curah Hujan: {chance_of_rain}%"
            message += f" | 💧 Kelembaban: {humidity}%"
            message += f"\n\n"
        
        return message
        
    except Exception as e:
        logging.error(f"Error formatting forecast: {str(e)}")
        return f"❌ Error memformat ramalan cuaca: {str(e)}"


def format_astronomy(data: dict) -> str:
    """Format data astronomi menjadi format yang mudah dibaca"""
    try:
        location = data.get("location", {})
        astronomy = data.get("astronomy", {})
        astro = astronomy.get("astro", {})
        
        loc_name = location.get("name", "Unknown")
        localtime = location.get("localtime", "")
        
        sunrise = astro.get("sunrise", "N/A")
        sunset = astro.get("sunset", "N/A")
        moonrise = astro.get("moonrise", "N/A")
        moonset = astro.get("moonset", "N/A")
        moon_phase = astro.get("moon_phase", "N/A")
        moon_illumination = astro.get("moon_illumination", "N/A")
        
        message = f"🌙 <b>DATA ASTRONOMI</b>\n"
        message += f"📍 <b>{loc_name}</b>\n"
        message += f"🕐 {localtime}\n\n"
        message += f"☀️ <b>Matahari:</b>\n"
        message += f"   Terbit: {sunrise}\n"
        message += f"   Terbenam: {sunset}\n\n"
        message += f"🌙 <b>Bulan:</b>\n"
        message += f"   Terbit: {moonrise}\n"
        message += f"   Terbenam: {moonset}\n"
        message += f"   Fase: {moon_phase}\n"
        message += f"   Iluminasi: {moon_illumination}%"
        
        return message
        
    except Exception as e:
        logging.error(f"Error formatting astronomy: {str(e)}")
        return f"❌ Error memformat data astronomi: {str(e)}"


async def handle_weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /cuaca - menampilkan cuaca saat ini"""
    try:
        if not context.args:
            await update.message.reply_text(
                "🌤️ <b>Informasi Cuaca</b>\n\n"
                "Gunakan format:\n"
                "/cuaca [nama kota]\n\n"
                "Contoh:\n"
                "/cuaca Jakarta\n"
                "/cuaca Bandung\n"
                "/cuaca Surabaya",
                parse_mode="HTML"
            )
            return
        
        location = " ".join(context.args)
        await update.message.reply_text(f"⏳ Mengambil data cuaca untuk {location}...")
        
        data = await weather_api.get_current_weather(location)
        formatted = format_current_weather(data)
        await update.message.reply_text(formatted, parse_mode="HTML")
        
    except Exception as e:
        logging.error(f"Error in handle_weather_command: {str(e)}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def handle_forecast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /ramalan - menampilkan ramalan cuaca"""
    try:
        if not context.args:
            await update.message.reply_text(
                "📅 <b>Ramalan Cuaca</b>\n\n"
                "Gunakan format:\n"
                "/ramalan [nama kota] [jumlah hari]\n\n"
                "Contoh:\n"
                "/ramalan Jakarta 3\n"
                "/ramalan Bandung 7",
                parse_mode="HTML"
            )
            return
        
        # Parse arguments
        args = context.args
        if len(args) >= 2 and args[-1].isdigit():
            location = " ".join(args[:-1])
            days = int(args[-1])
        else:
            location = " ".join(args)
            days = 3
        
        await update.message.reply_text(f"⏳ Mengambil ramalan cuaca untuk {location}...")
        
        data = await weather_api.get_forecast(location, days)
        formatted = format_forecast(data)
        await update.message.reply_text(formatted, parse_mode="HTML")
        
    except Exception as e:
        logging.error(f"Error in handle_forecast_command: {str(e)}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def handle_astronomy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /astronomi - menampilkan data astronomi"""
    try:
        if not context.args:
            await update.message.reply_text(
                "🌙 <b>Data Astronomi</b>\n\n"
                "Gunakan format:\n"
                "/astronomi [nama kota]\n\n"
                "Contoh:\n"
                "/astronomi Jakarta\n"
                "/astronomi Bandung",
                parse_mode="HTML"
            )
            return
        
        location = " ".join(context.args)
        await update.message.reply_text(f"⏳ Mengambil data astronomi untuk {location}...")
        
        data = await weather_api.get_astronomy(location)
        formatted = format_astronomy(data)
        await update.message.reply_text(formatted, parse_mode="HTML")
        
    except Exception as e:
        logging.error(f"Error in handle_astronomy_command: {str(e)}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def handle_search_location_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /cari - mencari lokasi"""
    try:
        if not context.args:
            await update.message.reply_text(
                "🔍 <b>Cari Lokasi</b>\n\n"
                "Gunakan format:\n"
                "/cari [nama kota]\n\n"
                "Contoh:\n"
                "/cari London\n"
                "/cari New York",
                parse_mode="HTML"
            )
            return
        
        query = " ".join(context.args)
        await update.message.reply_text(f"⏳ Mencari lokasi '{query}'...")
        
        results = await weather_api.search_location(query)
        
        if not results:
            await update.message.reply_text(f"❌ Lokasi '{query}' tidak ditemukan.")
            return
        
        message = f"🔍 <b>Hasil Pencarian:</b> '{query}'\n\n"
        for i, result in enumerate(results[:10], 1):  # Tampilkan maksimal 10 hasil
            name = result.get("name", "Unknown")
            country = result.get("country", "")
            message += f"{i}. {name}, {country}\n"
        
        await update.message.reply_text(message, parse_mode="HTML")
        
    except Exception as e:
        logging.error(f"Error in handle_search_location_command: {str(e)}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def handle_history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /history - menampilkan cuaca historis"""
    try:
        if not context.args:
            await update.message.reply_text(
                "📜 <b>Cuaca Historis</b>\n\n"
                "Gunakan format:\n"
                "/history [nama kota] [tanggal]\n\n"
                "Contoh:\n"
                "/history Jakarta 2024-01-15\n"
                "/history Bandung 2024-12-01",
                parse_mode="HTML"
            )
            return
        
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("❌ Format salah! Gunakan: /history [kota] [tanggal YYYY-MM-DD]")
            return
        
        # Parse date (last argument)
        date_str = args[-1]
        location = " ".join(args[:-1])
        
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            await update.message.reply_text("❌ Format tanggal salah! Gunakan format: YYYY-MM-DD")
            return
        
        await update.message.reply_text(f"⏳ Mengambil data historis untuk {location} pada {date_str}...")
        
        data = await weather_api.get_history(location, date_str)
        
        # Format similar to current weather
        formatted = format_current_weather(data)
        formatted = formatted.replace("CUACA SAAT INI", f"CUACA HISTORIS ({date_str})")
        
        await update.message.reply_text(formatted, parse_mode="HTML")
        
    except Exception as e:
        logging.error(f"Error in handle_history_command: {str(e)}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def handle_marine_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /maritim - menampilkan cuaca maritim"""
    try:
        if not context.args:
            await update.message.reply_text(
                "🌊 <b>Cuaca Maritim</b>\n\n"
                "Gunakan format:\n"
                "/maritim [nama kota pantai]\n\n"
                "Contoh:\n"
                "/maritim Sanur\n"
                "/maritim Kuta",
                parse_mode="HTML"
            )
            return
        
        location = " ".join(context.args)
        await update.message.reply_text(f"⏳ Mengambil data cuaca maritim untuk {location}...")
        
        data = await weather_api.get_marine_weather(location)
        
        # Format marine weather data
        location_info = data.get("location", {})
        forecast = data.get("forecast", {})
        forecastday = forecast.get("forecastday", [])
        
        message = f"🌊 <b>CUACA MARITIM</b>\n"
        message += f"📍 <b>{location_info.get('name', 'Unknown')}</b>\n\n"
        
        for day_data in forecastday[:3]:
            date = day_data.get("date", "")
            day = day_data.get("day", {})
            
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            day_name = date_obj.strftime("%A")
            
            maxtemp_c = day.get("maxtemp_c", "N/A")
            mintemp_c = day.get("mintemp_c", "N/A")
            
            message += f"📆 <b>{day_name}</b> ({date})\n"
            message += f"   🌡️ {mintemp_c}°C - {maxtemp_c}°C\n\n"
        
        await update.message.reply_text(message, parse_mode="HTML")
        
    except Exception as e:
        logging.error(f"Error in handle_marine_command: {str(e)}")
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def handle_weather_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk command /bantuan_cuaca - menampilkan semua command cuaca"""
    help_text = """
🌤️ <b>BANTUAN COMMAND CUACA</b>

<b>Command yang tersedia:</b>

1️⃣ <b>/cuaca [kota]</b>
   Menampilkan cuaca saat ini
   Contoh: /cuaca Jakarta

2️⃣ <b>/ramalan [kota] [hari]</b>
   Menampilkan ramalan cuaca (1-14 hari)
   Contoh: /ramalan Jakarta 7

3️⃣ <b>/astronomi [kota]</b>
   Menampilkan data astronomi (sunrise, sunset, moon phase)
   Contoh: /astronomi Jakarta

4️⃣ <b>/history [kota] [tanggal]</b>
   Menampilkan cuaca historis
   Contoh: /history Jakarta 2024-01-15

5️⃣ <b>/cari [kota]</b>
   Mencari lokasi
   Contoh: /cari London

6️⃣ <b>/maritim [kota pantai]</b>
   Menampilkan cuaca maritim
   Contoh: /maritim Sanur

7️⃣ <b>/bantuan_cuaca</b>
   Menampilkan bantuan ini

<b>Fitur:</b>
✅ Cuaca real-time dengan kualitas udara
✅ Ramalan hingga 14 hari
✅ Data historis dari 2010
✅ Informasi astronomi lengkap
✅ Pencarian lokasi otomatis
✅ Data cuaca maritim
    """
    await update.message.reply_text(help_text, parse_mode="HTML")

