# ai_services/risk_assessment_services/input_preprocessor.py
import logging
logger = logging.getLogger(__name__)

def validate_and_prepare_risk_assessment_input(payload: dict) -> tuple[dict | None, str | None]:
    """
    Memvalidasi input untuk regional risk assessment.
    Payload diharapkan berisi: {"region_identifier": "ID_DAERAH", "bnpb_data_summary": "Teks data dari BNPB..."}
    """
    if "region_identifier" not in payload or "bnpb_data_summary" not in payload:
        return None, "Missing 'region_identifier' or 'bnpb_data_summary' in payload."
    
    prepared_data = {
        "region": payload["region_identifier"],
        "bnpb_summary": payload["bnpb_data_summary"]
    }
    logger.debug(f"Input preprocessed for risk assessment: {prepared_data.get('region')}")
    return prepared_data, None