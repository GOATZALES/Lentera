# Lentera/ai_service/forecasting_services/tools.py
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Optional, Any # Tambahkan Any jika perlu
import json
import datetime

# Impor model Faskes Anda. Pastikan path impor ini benar.
from authentication.models import Faskes as FaskesPartner 
class FaskesInfoInput(BaseModel):
    faskes_id: str = Field(description="ID unik internal Faskes Partner yang datanya ingin diambil. Contoh: FKS001-JKTSEL")

class FaskesDataProviderTool(BaseTool):
    name: str = "get_faskes_partner_data"
    description: str = (
        "Berguna untuk mendapatkan data detail sebuah Faskes Partner berdasarkan ID internalnya. "
        "Data ini mencakup informasi historis kunjungan, layanan, kapasitas, dan staffing baseline. "
        "Gunakan ID faskes yang diberikan dalam permintaan awal."
    )
    args_schema: Optional[Type[BaseModel]] = FaskesInfoInput

    def _run(self, faskes_id: str) -> str: # Menerima faskes_id langsung
        try:
            partner = FaskesPartner.objects.get(faskes_id_internal=faskes_id)
            relevant_data = {
                "faskes_id": partner.faskes_id_internal,
                "nama_faskes": partner.nama_faskes,
                "jenis_faskes": partner.jenis_faskes,
                "kota_kabupaten": partner.alamat_kota_kabupaten,
                "layanan_unggulan": partner.layanan_unggulan_json,
                "kapasitas_info": partner.kapasitas_info_json,
                "historis_kunjungan_bulanan_terakhir": partner.historis_kunjungan_bulanan_json[-6:] if partner.historis_kunjungan_bulanan_json else [],
                "rata_kunjungan_harian_seminggu": partner.rata_kunjungan_harian_seminggu_json,
                "pola_kunjungan_layanan_harian": partner.pola_kunjungan_layanan_json,
                "periode_puncak_diketahui": partner.periode_puncak_diketahui_json,
                "baseline_staffing": partner.baseline_staffing_json,
                "historis_klb_lokal": partner.historis_klb_lokal_json,
            }
            return json.dumps(relevant_data, default=str, ensure_ascii=False)
        except FaskesPartner.DoesNotExist:
            return f"Error: Faskes Partner dengan ID '{faskes_id}' tidak ditemukan."
        except Exception as e:
            return f"Error saat mengambil data Faskes '{faskes_id}': {str(e)}"

    async def _arun(self, faskes_id: str) -> str:
        return self._run(faskes_id)

# --- ExternalDataProviderTool DENGAN SATU INPUT STRING JSON ---
class ExternalToolStringInput(BaseModel):
    json_input_string: str = Field(description="String JSON yang berisi 'city_name' dan 'target_date_or_range'. Contoh: '{{\"city_name\": \"Jakarta\", \"target_date_or_range\": \"2024-07-01\"}}'")

class ExternalInfoInput(BaseModel):
    city_name: str = Field(description="Nama kota di Indonesia. Contoh: 'Tangerang Selatan', 'Kota Bandung'")
    target_date_or_range: str = Field(description="Tanggal target (YYYY-MM-DD) atau rentang tanggal (YYYY-MM-DD hingga YYYY-MM-DD) untuk informasi.")

def get_simulated_external_data_func(city_name: str, target_date_or_range: str) -> str:
    """Simulasi pengambilan data cuaca, event, dan mudik."""
    try:
        target_date_str = target_date_or_range.split(" hingga ")[0].strip()
        target_dt = datetime.datetime.strptime(target_date_str, "%Y-%m-%d").date()
    except ValueError:
        return json.dumps({"error": "Format tanggal tidak valid. Gunakan YYYY-MM-DD atau YYYY-MM-DD hingga YYYY-MM-DD."})

    weather_forecast = f"Prakiraan cuaca untuk {city_name} sekitar {target_date_str}: Cerah berawan, suhu 27-32°C."
    if "bandung" in city_name.lower():
        weather_forecast = f"Prakiraan cuaca untuk {city_name} sekitar {target_date_str}: Sejuk dan berawan, suhu 19-25°C, potensi hujan ringan."
    elif "surabaya" in city_name.lower() or "jakarta" in city_name.lower():
        weather_forecast = f"Prakiraan cuaca untuk {city_name} sekitar {target_date_str}: Panas dan cerah, suhu 30-34°C."


    local_events = "Tidak ada event besar yang signifikan tercatat."
    if ("jakarta" in city_name.lower() or "bali" in city_name.lower()) and (target_dt.month == 12 or target_dt.month == 6 or target_dt.month == 7):
        local_events = "Potensi peningkatan aktivitas turis karena musim liburan."
    if target_dt.month == 8 and target_dt.day > 10 and target_dt.day < 20: # Untuk 17 Agustus
         local_events = "Perayaan HUT Kemerdekaan RI dengan berbagai acara di area publik."
    
    mudik_info = "Tidak dalam periode mudik utama."
    if target_dt.month in [4, 5] or (target_dt.month == 12 and target_dt.day > 15) or (target_dt.month == 1 and target_dt.day < 10):
        mudik_info = "Periode mudik atau libur panjang, perhatikan peningkatan perjalanan dan aktivitas."

    return json.dumps({
        "city_processed": city_name,
        "date_processed": target_date_or_range,
        "weather_forecast": weather_forecast,
        "local_events": local_events,
        "mudik_info": mudik_info
    })


class ExternalDataProviderTool(BaseTool):
    name: str = "get_external_weather_event_mudik_data"
    description: str = (
        "Berguna untuk mendapatkan prakiraan cuaca, informasi event lokal, dan info mudik. "
        "Input ke alat ini HARUS berupa string JSON tunggal yang valid, yang berisi keys 'city_name' dan 'target_date_or_range'. "
        "Contoh Action Input: '{{\"city_name\": \"Jakarta\", \"target_date_or_range\": \"2024-07-01 hingga 2024-07-07\"}}'"
    )
    args_schema: Optional[Type[BaseModel]] = ExternalToolStringInput # Menerima satu string

    def _run(self, json_input_string: str) -> str: # Menerima string input
        try:
            data = json.loads(json_input_string)
            city_name = data.get("city_name")
            target_date_or_range = data.get("target_date_or_range")

            if not city_name or not target_date_or_range:
                return json.dumps({"error": "JSON input harus memiliki field 'city_name' dan 'target_date_or_range'."})
            
            return get_simulated_external_data_func(city_name, target_date_or_range)
        except json.JSONDecodeError:
            return json.dumps({"error": f"Input bukan JSON string yang valid: '{json_input_string[:100]}...'"})
        except Exception as e:
            return json.dumps({"error": f"Error internal pada tool: {str(e)}"})

    async def _arun(self, json_input_string: str) -> str:
        return self._run(json_input_string)