# ai_services/risk_assessment_services/core_risk_assessor.py
from ..client import get_gemini_text_response
import json
import logging
from django.utils import timezone
from ..models import RegionalRiskAnalysisResult # Untuk logging hasil analisis

logger = logging.getLogger(__name__)

def assess_regional_disaster_risk(
    caller_ref_id: str, # Ini adalah region_identifier
    input_data: dict, # Hasil dari input_preprocessor untuk risk assessment
    input_payload_for_log: dict,
    ai_model_name: str = "gemini-1.5-flash-latest"
) -> tuple[dict | None, str | None, int | None]:
    """
    Menggunakan LLM untuk menganalisis data risiko regional dari BNPB (atau sumber serupa).
    Mengembalikan (parsed_risk_assessment_json, error_message, analysis_log_id).
    """
    # Tidak ada log permintaan AiForecastRequestLog khusus, karena ini layanan berbeda.
    # Kita bisa buat model log terpisah atau langsung simpan ke RegionalRiskAnalysisResult.
    # Untuk konsistensi, kita buat entri log di RegionalRiskAnalysisResult.
    
    prompt = f"""
    Anda adalah Analis Risiko Bencana untuk HealthConnect Indonesia.
    Berdasarkan ringkasan data historis bencana dari BNPB untuk wilayah berikut, berikan penilaian risiko:
    1. Tingkat Risiko Keseluruhan (Pilih satu: Rendah, Sedang, Tinggi, Kritis).
    2. Justifikasi singkat untuk tingkat risiko tersebut.
    3. Daftar potensi jenis bencana utama yang paling mungkin terjadi.

    Wilayah Analisis: {input_data.get('region')}
    Ringkasan Data Historis Bencana (BNPB):
    {input_data.get('bnpb_summary')}

    Harap berikan output dalam format JSON yang ketat seperti contoh berikut:
    {{
      "region_analyzed": "{input_data.get('region')}",
      "overall_risk_level": "<Rendah|Sedang|Tinggi|Kritis>",
      "risk_justification": "<Penjelasan singkat mengenai alasan tingkat risiko tersebut>",
      "potential_major_hazards": ["<Jenis Bencana 1>", "<Jenis Bencana 2>", "..."]
    }}
    """
    logger.debug(f"Prompting LLM for regional risk assessment for {caller_ref_id}")
    raw_llm_response_text = get_gemini_text_response(prompt, model_name=ai_model_name)

    analysis_log_entry = RegionalRiskAnalysisResult.objects.create(
        caller_reference_id=caller_ref_id,
        input_data_summary_text=input_data.get('bnpb_summary'),
        raw_ai_response_text=raw_llm_response_text,
        ai_model_name_used=ai_model_name,
        analyzed_at=timezone.now()
    )

    if isinstance(raw_llm_response_text, dict) and "error" in raw_llm_response_text:
        analysis_log_entry.risk_justification_text = f"AI Error: {raw_llm_response_text['error']}"
        analysis_log_entry.save()
        logger.error(f"LLM client error for risk assessment {caller_ref_id}: {raw_llm_response_text['error']}")
        return None, raw_llm_response_text["error"], analysis_log_entry.id

    # Pembersihan JSON (sama seperti sebelumnya)
    clean_response_text = raw_llm_response_text.strip()
    # ... (logika pembersihan JSON sama) ...
    if clean_response_text.startswith("```json"):
        clean_response_text = clean_response_text[7:-3].strip() if clean_response_text.endswith("```") else clean_response_text[7:].strip()
    elif clean_response_text.startswith("```"):
        clean_response_text = clean_response_text[3:-3].strip() if clean_response_text.endswith("```") else clean_response_text[3:].strip()

    try:
        parsed_json = json.loads(clean_response_text)
        analysis_log_entry.parsed_ai_output_json = parsed_json # Simpan JSON lengkap jika mau
        analysis_log_entry.risk_level_predicted = parsed_json.get("overall_risk_level")
        analysis_log_entry.risk_justification_text = parsed_json.get("risk_justification")
        analysis_log_entry.potential_hazards_json = parsed_json.get("potential_major_hazards")
        analysis_log_entry.save()
        logger.info(f"Successfully assessed regional risk for {caller_ref_id}, Log ID: {analysis_log_entry.id}")
        return parsed_json, None, analysis_log_entry.id
    except json.JSONDecodeError as e:
        err_msg = f"Failed to parse LLM JSON response for risk assessment: {e}"
        analysis_log_entry.risk_justification_text = f"JSON Parse Error: {err_msg}. Raw: {clean_response_text[:200]}"
        analysis_log_entry.save()
        logger.error(err_msg, exc_info=True)
        return None, err_msg, analysis_log_entry.id