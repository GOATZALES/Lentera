import logging
logger = logging.getLogger(__name__)

def validate_and_prepare_initial_agent_input(payload: dict) -> tuple[dict | None, str | None]:
    """
    Memvalidasi payload input dan menyiapkan data awal untuk prompt agent Langchain.
    """
    required_fields = ["faskes_id", "period_start", "period_end"]
    for field in required_fields:
        if field not in payload:
            return None, f"Missing required field in payload: {field}"

    # Data awal yang akan diberikan ke agent, sisanya akan diambil via tools
    prepared_agent_input_data = {
        "faskes_id": payload["faskes_id"],
        "period_start": payload["period_start"], # Pastikan format YYYY-MM-DD
        "period_end": payload["period_end"],     # Pastikan format YYYY-MM-DD
        "historical_summary": payload.get("historical_patient_summary", "Tidak ada ringkasan historis awal yang diberikan."),
        "seasonal_patterns": payload.get("seasonal_disease_patterns", "Tidak ada info pola musiman awal yang diberikan."),
    }
    logger.debug(f"Initial agent input preprocessed for Faskes ID: {prepared_agent_input_data.get('faskes_id')}")
    return prepared_agent_input_data, None