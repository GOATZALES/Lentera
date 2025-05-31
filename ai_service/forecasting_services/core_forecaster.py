# ai_services/forecasting_services/core_forecaster.py
from ..client import get_gemini_text_response
import json
import logging
from django.utils import timezone
from ..models import AiForecastRequestLog # Untuk logging permintaan

logger = logging.getLogger(__name__)

# Tarif bisa tetap di sini atau dipindahkan ke konfigurasi/database lain di luar ai_services
DEFAULT_RATES_PER_SHIFT = {
    "Dokter Umum": {"min": 500000, "max": 1000000},
    "Dokter Spesialis": {"min": 750000, "max": 1500000},
    "Perawat": {"min": 250000, "max": 500000},
    "Bidan": {"min": 250000, "max": 450000},
    "Volunteer Medis (Supervised)": {"min": 100000, "max": 200000}
}

def generate_staffing_demand_forecast(
    caller_ref_id: str, 
    input_data: dict, # Hasil dari input_preprocessor
    input_payload_for_log: dict, # Payload asli untuk disimpan di log
    ai_model_name: str = "gemini-1.5-flash-latest"
) -> tuple[dict | None, str | None, int | None]:
    """
    Menghasilkan prediksi kebutuhan staf menggunakan LLM.
    Mengembalikan (parsed_forecast_json, error_message, log_id).
    """
    log_entry = AiForecastRequestLog.objects.create(
        caller_reference_id=caller_ref_id,
        service_type="staffing_demand_forecast",
        input_payload_json=input_payload_for_log,
        ai_model_name_used=ai_model_name,
        processing_status="processing"
    )

    rates_info = "Tarif Profesional per Shift (IDR):\n"
    for role, rate in DEFAULT_RATES_PER_SHIFT.items():
        rates_info += f"- {role}: {rate['min']:,} - {rate['max']:,}\n"

    # Prompt tetap sama seperti sebelumnya, menggunakan input_data
    prompt = f"""
    Anda adalah "HealthConnect AI Forecaster", seorang spesialis perencana kebutuhan tenaga medis di Indonesia.
    Tugas Anda adalah menganalisis data berikut untuk Fasilitas Kesehatan (Faskes) dan menghasilkan:
    1. Prediksi Kebutuhan Staf: Jumlah profesional per jenis (Dokter Umum, Perawat, Bidan, jika relevan Dokter Spesialis [sebutkan jenis jika ada info], Volunteer Medis).
    2. Estimasi Biaya Staf: Kisaran biaya (Min-Max) untuk periode tersebut.
    3. Peringatan Periode Puncak & Rekomendasi: Identifikasi potensi lonjakan permintaan dan berikan rekomendasi singkat.

    Data Faskes:
    - ID Faskes (Caller Ref): {input_data.get('faskes_id')}
    - Periode Peramalan: {input_data.get('period_start')} hingga {input_data.get('period_end')}

    Informasi Pendukung:
    - Ringkasan Data Pasien Historis: {input_data.get('historical_summary')}
    - Pola Penyakit Musiman yang Diketahui: {input_data.get('seasonal_patterns')}
    - Prakiraan Cuaca (BMKG): {input_data.get('weather_forecast')}
    - Kalender Event Lokal: {input_data.get('local_events')}
    - Info Kalender Mudik (jika relevan): {input_data.get('mudik_info')}

    {rates_info}

    Harap berikan output dalam format JSON yang ketat seperti contoh berikut.
    Pastikan semua angka adalah integer atau float, bukan string.

    Format Output JSON (WAJIB DIPATUHI):
    {{
      "predicted_staffing_demand": {{
        "Dokter Umum": <integer>,
        "Perawat": <integer>,
        "Bidan": <integer_atau_0>,
        "Dokter Spesialis Anak": <integer_atau_0>,
        "Volunteer Medis": <integer_atau_0>
      }},
      "estimated_cost_range_rp": {{
        "min_cost": <float>,
        "max_cost": <float>,
        "currency": "IDR",
        "notes": "Estimasi berdasarkan jumlah shift sama dengan jumlah hari dalam periode forecast."
      }},
      "peak_period_alerts_and_recommendations": "<string_analisis_dan_rekomendasi_singkat>"
    }}
    """
    logger.debug(f"Prompting LLM for staffing forecast for {caller_ref_id}")
    raw_llm_response_text = get_gemini_text_response(prompt, model_name=ai_model_name)
    log_entry.raw_ai_response_text = raw_llm_response_text # Simpan raw response

    if isinstance(raw_llm_response_text, dict) and "error" in raw_llm_response_text:
        log_entry.processing_status = "failed"
        log_entry.error_message = raw_llm_response_text["error"]
        log_entry.completed_at = timezone.now()
        log_entry.save()
        logger.error(f"LLM client error for {caller_ref_id}: {raw_llm_response_text['error']}")
        return None, raw_llm_response_text["error"], log_entry.id

    # Pembersihan JSON (sama seperti sebelumnya)
    clean_response_text = raw_llm_response_text.strip()
    if clean_response_text.startswith("```json"):
        clean_response_text = clean_response_text[7:-3].strip() if clean_response_text.endswith("```") else clean_response_text[7:].strip()
    elif clean_response_text.startswith("```"):
        clean_response_text = clean_response_text[3:-3].strip() if clean_response_text.endswith("```") else clean_response_text[3:].strip()
    
    try:
        parsed_json = json.loads(clean_response_text)
        log_entry.parsed_ai_output_json = parsed_json
        log_entry.processing_status = "completed"
        log_entry.completed_at = timezone.now()
        log_entry.save()
        logger.info(f"Successfully generated staffing forecast for {caller_ref_id}, Log ID: {log_entry.id}")
        return parsed_json, None, log_entry.id
    except json.JSONDecodeError as e:
        err_msg = f"Failed to parse LLM JSON response: {e}. Cleaned text: {clean_response_text[:200]}"
        log_entry.processing_status = "failed"
        log_entry.error_message = err_msg
        log_entry.completed_at = timezone.now()
        log_entry.save()
        logger.error(err_msg, exc_info=True)
        return None, err_msg, log_entry.id