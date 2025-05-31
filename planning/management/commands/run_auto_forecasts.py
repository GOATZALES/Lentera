# planning/management/commands/run_auto_forecasts.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
# Ganti dengan path model FaskesPartner Anda
from authentication.models import Faskes 
from planning.logic import generate_staffing_forecast # Panggil logic dari planning
# Anda perlu fungsi untuk mengambil data eksternal

class Command(BaseCommand):
    help = 'Runs automated demand forecasting for active Faskes Partners'
    def handle(self, *args, **kwargs):
        active_partners = Faskes.objects.filter(is_active_partner=True)
        self.stdout.write(f"Found {active_partners.count()} active Faskes Partners to forecast.")

        # Tentukan periode forecast (misal, 7 hari ke depan dari besok)
        forecast_start_date = (timezone.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        forecast_end_date = (timezone.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        for partner in active_partners:
            self.stdout.write(f"Processing forecast for: {partner.nama_faskes} ({partner.faskes_id_internal})")

            # 1. Kumpulkan data historis dari FaskesPartner model
            # (Ini sudah ada di model, kita hanya perlu memformatnya jika perlu)
            # Untuk dummy, kita asumsikan format di JSONField sudah cukup baik
            # Namun, untuk historis_kunjungan_bulanan, AI mungkin butuh ringkasan atau tren
            
            historical_summary_text = f"Rata-rata kunjungan harian: Senin={partner.rata_kunjungan_harian_seminggu_json.get('Senin',0)}, Selasa={partner.rata_kunjungan_harian_seminggu_json.get('Selasa',0)}, dst. "
            # Tambahkan info dari kunjungan bulanan jika perlu diringkas
            # ...
            
            # 2. (SIMULASI) Ambil data eksternal (BMKG, event, dll.)
            # Untuk Hackathon, Anda bisa hardcode atau buat fungsi dummy
            # bmkg_data = get_dummy_bmkg_forecast(partner.koordinat_latitude, partner.koordinat_longitude, forecast_start_date, forecast_end_date)
            # local_events_data = get_dummy_local_events(partner.alamat_kota_kabupaten, forecast_start_date, forecast_end_date)
            bmkg_data_dummy = f"Prakiraan cuaca untuk {partner.alamat_kota_kabupaten}: Cerah berawan, suhu 28-32C."
            local_events_dummy = "Tidak ada event besar tercatat."
            mudik_info_dummy = "Tidak dalam periode mudik." # Bisa cek kalender

            payload = {
                "faskes_id": partner.faskes_id_internal,
                "period_start": forecast_start_date,
                "period_end": forecast_end_date,
                "historical_patient_summary": historical_summary_text + f" Layanan utama: {', '.join(partner.layanan_unggulan_json)}. Periode puncak diketahui: {', '.join(partner.periode_puncak_diketahui_json)}.",
                "seasonal_disease_patterns": "Perhatikan pola penyakit musiman umum untuk area ini.", # Bisa lebih spesifik jika ada data per region
                "bmkg_weather_forecast": bmkg_data_dummy,
                "local_events_calendar": local_events_dummy,
                "mudik_calendar_info": mudik_info_dummy,
                # "ai_model_name": "gemini-1.5-flash-latest" # Bisa default di logic
            }

            result = generate_staffing_forecast(payload)

            if "error" in result and result["error"]:
                self.stderr.write(self.style.ERROR(f"Failed forecast for {partner.nama_faskes}: {result['error']}"))
            elif "ai_request_log_id" in result:
                self.stdout.write(self.style.SUCCESS(f"Forecast generated for {partner.nama_faskes}. Log ID: {result['ai_request_log_id']}"))
            else:
                self.stderr.write(self.style.WARNING(f"Unknown response for {partner.nama_faskes}"))

        
        self.stdout.write(self.style.SUCCESS('Automated forecasting process finished.'))

def get_dummy_bmkg_forecast(city_name, start_date, end_date):
    if "bandung" in city_name.lower():
        return f"Prakiraan Bandung ({start_date} s/d {end_date}): Berawan, potensi hujan ringan sore hari, suhu sejuk."
    return f"Prakiraan {city_name} ({start_date} s/d {end_date}): Cerah hingga berawan."

def get_dummy_local_events(city_name, start_date, end_date):
    if "jakarta" in city_name.lower() and "2024-08-17" >= start_date and "2024-08-17" <= end_date :
        return "Perayaan HUT RI ke-79 di Monas dan berbagai area publik."
    return "Tidak ada event besar tercatat untuk periode ini."