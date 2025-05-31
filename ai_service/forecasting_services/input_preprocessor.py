# ai_services/forecasting_services/input_preprocessor.py
import logging
logger = logging.getLogger(__name__)

def validate_and_prepare_staffing_forecast_input(payload: dict) -> tuple[dict | None, str | None]:
    """
    Memvalidasi payload input untuk staffing forecast dan menyiapkannya.
    Mengembalikan (prepared_input, error_message).
    prepared_input adalah dictionary yang akan digunakan untuk membuat prompt.
    """
    required_top_level = ["faskes_id", "period_start", "period_end"] # Dari sistem pemanggil
    required_data_points = [ # Data yang akan digunakan AI
        "historical_patient_summary", 
        "seasonal_disease_patterns",
        "bmkg_weather_forecast",
        "local_events_calendar",
        "mudik_calendar_info"
    ]
    
    # Validasi field wajib dari sistem pemanggil
    for field in required_top_level:
        if field not in payload:
            return None, f"Missing required field in payload: {field}"

    # Siapkan data untuk prompt, gunakan default jika tidak ada
    prepared_data = {
        "faskes_id": payload["faskes_id"],
        "period_start": payload["period_start"], # Asumsikan sudah dalam format YYYY-MM-DD
        "period_end": payload["period_end"],
    }
    for dp_field in required_data_points:
        prepared_data[dp_field] = payload.get(dp_field, "Tidak ada informasi.")
    
    logger.debug(f"Input preprocessed for staffing forecast: {prepared_data.get('faskes_id')}")
    return prepared_data, None