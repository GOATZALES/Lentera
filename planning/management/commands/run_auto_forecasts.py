from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from authentication.models import Faskes as FaskesPartner # Pastikan path ini benar
from planning.logic import generate_staffing_forecast 

class Command(BaseCommand):
    help = 'Runs automated demand forecasting for active Faskes Partners'

    def handle(self, *args, **kwargs):
        active_partners = FaskesPartner.objects.filter(is_active_partner=True)
        self.stdout.write(f"Found {active_partners.count()} active Faskes Partners to forecast.")

        forecast_start_date = (timezone.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        forecast_end_date = (timezone.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        for partner in active_partners:
            self.stdout.write(f"Processing forecast for: {partner.nama_faskes} ({partner.faskes_id_internal})")

            # --- PERBAIKAN DI SINI ---
            rata_kunjungan_harian_str = "Data rata-rata kunjungan harian tidak tersedia."
            if partner.rata_kunjungan_harian_seminggu_json: # Cek jika tidak None
                rata_kunjungan_harian_str = (
                    f"Senin={partner.rata_kunjungan_harian_seminggu_json.get('Senin',0)}, "
                    f"Selasa={partner.rata_kunjungan_harian_seminggu_json.get('Selasa',0)}, "
                    f"Rabu={partner.rata_kunjungan_harian_seminggu_json.get('Rabu',0)}, "
                    f"Kamis={partner.rata_kunjungan_harian_seminggu_json.get('Kamis',0)}, "
                    f"Jumat={partner.rata_kunjungan_harian_seminggu_json.get('Jumat',0)}, "
                    f"Sabtu={partner.rata_kunjungan_harian_seminggu_json.get('Sabtu',0)}, "
                    f"Minggu={partner.rata_kunjungan_harian_seminggu_json.get('Minggu',0)}"
                )
            
            layanan_unggulan_str = "Tidak ada info layanan unggulan."
            if partner.layanan_unggulan_json and isinstance(partner.layanan_unggulan_json, list):
                layanan_unggulan_str = ', '.join(partner.layanan_unggulan_json)

            periode_puncak_str = "Tidak ada info periode puncak."
            if partner.periode_puncak_diketahui_json and isinstance(partner.periode_puncak_diketahui_json, list):
                periode_puncak_str = ', '.join(partner.periode_puncak_diketahui_json)

            historical_summary_text = (
                f"Rata-rata kunjungan harian: {rata_kunjungan_harian_str}. "
                f"Layanan utama: {layanan_unggulan_str}. "
                f"Periode puncak diketahui: {periode_puncak_str}."
            )
            # -------------------------
            
            bmkg_data_dummy = f"Prakiraan cuaca untuk {partner.alamat_kota_kabupaten or 'lokasi tidak diketahui'}: Cerah berawan, suhu 28-32C."
            local_events_dummy = "Tidak ada event besar tercatat."
            mudik_info_dummy = "Tidak dalam periode mudik."

            payload = {
                "faskes_id": partner.faskes_id_internal,
                "period_start": forecast_start_date,
                "period_end": forecast_end_date,
                "historical_patient_summary": historical_summary_text,
                "seasonal_disease_patterns": "Perhatikan pola penyakit musiman umum untuk area ini.",
                "bmkg_weather_forecast": bmkg_data_dummy,
                "local_events_calendar": local_events_dummy,
                "mudik_calendar_info": mudik_info_dummy,
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