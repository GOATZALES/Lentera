# Lentera/planning/logic.py
import logging
from django.utils import timezone
from ai_service.models import AiForecastRequestLog, AiModelPerformanceFeedback

# Ganti impor untuk preprocessor dan core_forecaster
from ai_service.forecasting_services import input_preprocessor as fcs_input_ai_module # Ganti nama alias
from ai_service.forecasting_services import core_forecaster as fcs_core_ai_module     # Ganti nama alias
from ai_service.forecasting_services import accuracy_evaluator as fcs_accuracy_ai

from emergency.logic import (
    get_active_emergency_events_with_details,
    get_emergency_event_detail_for_planning,
    trigger_ai_analysis_for_event as trigger_emergency_ai_logic # Alias agar tidak bentrok jika ada nama sama
)
from emergency.models import EmergencyEvent

logger = logging.getLogger(__name__)

def generate_staffing_forecast(payload: dict):
    """
    Memanggil layanan AI (Langchain) untuk staffing forecast.
    """
    # Gunakan preprocessor baru untuk input agent
    initial_agent_input, err = fcs_input_ai_module.validate_and_prepare_initial_agent_input(payload)
    if err:
        logger.warning(f"Input validation failed for Langchain agent: {err}")
        return {"error": err, "ai_request_log_id": None}

    caller_ref_id = initial_agent_input["faskes_id"]
    ai_model_name = payload.get("ai_model_name", "gemini-1.5-flash-latest")

    try:
        # Panggil fungsi Langchain yang baru
        forecast_json, error_msg, log_id = fcs_core_ai_module.generate_staffing_demand_forecast_with_langchain(
            caller_ref_id=caller_ref_id,
            input_data_for_initial_prompt=initial_agent_input,
            input_payload_for_log=payload,
            ai_model_name=ai_model_name
        )
        
        if error_msg:
            logger.error(f"Langchain AI forecaster returned error for {caller_ref_id}: {error_msg}")
            return {"error": error_msg, "ai_request_log_id": log_id}
        
        return {
            "message": "Staffing forecast generated successfully using Langchain.",
            "ai_request_log_id": log_id,
            "forecast_result": forecast_json
        }
    except Exception as e:
        logger.error(f"Exception calling Langchain core_forecaster: {e}", exc_info=True)
        return {"error": f"An unexpected error occurred during Langchain forecast generation: {str(e)}", "ai_request_log_id": None}

# Fungsi submit_forecast_feedback, get_faskes_forecast_history, get_forecast_detail_from_db
# TETAP SAMA seperti implementasi sebelumnya, karena mereka berinteraksi dengan model DB
# yang strukturnya tidak banyak berubah (AiForecastRequestLog, AiModelPerformanceFeedback).
# Pastikan saja path impor ke model tersebut sudah benar.

# (Salin implementasi fungsi submit_forecast_feedback, get_faskes_forecast_history,
# dan get_forecast_detail_from_db dari jawaban sebelumnya ke sini)
def submit_forecast_feedback(payload: dict):
    log_id = payload.get("ai_request_log_id")
    actual_data = payload.get("actual_data") 
    feedback_text = payload.get("qualitative_feedback", "")

    if not log_id or not isinstance(actual_data, dict):
        return {"error": "Missing 'ai_request_log_id' or 'actual_data' (must be a dict)."}

    try:
        ai_log_instance = AiForecastRequestLog.objects.get(id=log_id)
        if ai_log_instance.service_type != "staffing_demand_forecast_langchain" and ai_log_instance.service_type != "staffing_demand_forecast": # Akomodasi service type lama
             return {"error": "Feedback can only be submitted for 'staffing_demand_forecast' logs."}
    except AiForecastRequestLog.DoesNotExist:
        return {"error": f"AiForecastRequestLog with id {log_id} not found."}

    try:
        feedback_entry, created = AiModelPerformanceFeedback.objects.update_or_create(
            ai_request_log=ai_log_instance,
            defaults={
                'actual_data_json': actual_data,
                'qualitative_feedback': feedback_text,
                'feedback_provided_at': timezone.now()
            }
        )
        fcs_accuracy_ai.evaluate_staffing_forecast_accuracy(feedback_entry)
        action = "created" if created else "updated"
        return {
            "message": f"Forecast feedback {action} and accuracy evaluated.",
            "feedback_log_id": feedback_entry.id,
            "accuracy_results": feedback_entry.accuracy_metrics_json,
            "overall_accuracy_score": feedback_entry.overall_accuracy_score
        }
    except Exception as e:
        logger.error(f"Error during feedback submission or accuracy evaluation for log_id {log_id}: {e}", exc_info=True)
        return { "error": f"Failed to process feedback or evaluate accuracy: {str(e)}" }


def get_faskes_forecast_history(faskes_id: str, limit: int = 50):
    try:
        logs = AiForecastRequestLog.objects.filter(
            caller_reference_id=faskes_id,
            service_type__in=["staffing_demand_forecast", "staffing_demand_forecast_langchain"],
            processing_status="completed"
        ).select_related('performance_feedback').order_by('-requested_at')[:limit]
        results = []
        for log in logs:
            feedback_data = {}
            pf = getattr(log, 'performance_feedback', None) 
            if pf:
                feedback_data = {
                    "feedback_log_id": pf.id,
                    "actual_data_summary": pf.actual_data_json.get("staffing", {}),
                    "overall_accuracy_score": pf.overall_accuracy_score,
                    "qualitative_feedback": pf.qualitative_feedback,
                    "feedback_provided_at": pf.feedback_provided_at.isoformat() if pf.feedback_provided_at else None,
                }
            results.append({
                "ai_request_log_id": log.id,
                "caller_reference_id": log.caller_reference_id,
                "requested_at": log.requested_at.isoformat(),
                "period_start": log.input_payload_json.get("period_start"),
                "period_end": log.input_payload_json.get("period_end"),
                "parsed_ai_output": log.parsed_ai_output_json,
                "ai_model_name_used": log.ai_model_name_used,
                "feedback_info": feedback_data
            })
        return results
    except Exception as e:
        logger.error(f"Error fetching forecast history from DB for {faskes_id}: {e}", exc_info=True)
        return {"error": f"Error fetching data from database: {str(e)}"}


def get_forecast_detail_from_db(log_id: int):
    try:
        log_entry = AiForecastRequestLog.objects.select_related('performance_feedback').get(
            id=log_id, 
            service_type__in=["staffing_demand_forecast", "staffing_demand_forecast_langchain"]
        )
        feedback_data = {}
        pf = getattr(log_entry, 'performance_feedback', None)
        if pf:
            feedback_data = {
                "feedback_log_id": pf.id,
                "actual_data_json": pf.actual_data_json,
                "accuracy_metrics_json": pf.accuracy_metrics_json,
                "overall_accuracy_score": pf.overall_accuracy_score,
                "qualitative_feedback": pf.qualitative_feedback,
                "feedback_provided_at": pf.feedback_provided_at.isoformat() if pf.feedback_provided_at else None,
            }
        result = {
            "ai_request_log_id": log_entry.id,
            "caller_reference_id": log_entry.caller_reference_id,
            "requested_at": log_entry.requested_at.isoformat(),
            "input_payload_json": log_entry.input_payload_json,
            "parsed_ai_output_json": log_entry.parsed_ai_output_json,
            "ai_model_name_used": log_entry.ai_model_name_used,
            "processing_status": log_entry.processing_status,
            "error_message": log_entry.error_message,
            "completed_at": log_entry.completed_at.isoformat() if log_entry.completed_at else None,
            "feedback_info": feedback_data
        }
        return result
    except AiForecastRequestLog.DoesNotExist:
        logger.warning(f"Forecast log detail not found for ID: {log_id}")
        return {"error": "Forecast log not found."}
    except Exception as e:
        logger.error(f"Error fetching forecast detail from DB for ID {log_id}: {e}", exc_info=True)
        return {"error": f"Error fetching data from database: {str(e)}"}
    
def get_disaster_risk_dashboard_data():
    """
    Mengambil data untuk dashboard Disaster Risk Assessment di aplikasi planning.
    """
    active_events_with_details = get_active_emergency_events_with_details()
    
    # Proses data lebih lanjut jika perlu untuk tampilan di planning
    # Misalnya, meringkas rekomendasi atau mengambil metrik tertentu
    
    return {
        "active_disaster_events": active_events_with_details,
        # Anda bisa menambahkan data agregat lain di sini
    }

def get_disaster_event_planning_details(event_id):
    """
    Mengambil detail event bencana untuk ditampilkan di planning.
    """
    event = get_emergency_event_detail_for_planning(event_id)
    if not event:
        return None, "Kejadian darurat tidak ditemukan."
    
    # Data yang akan ditampilkan di planning bisa diformat di sini
    # atau langsung dari field model EmergencyEvent
    return event, None

def trigger_emergency_event_ai_analysis(event_id):
    """
    Memicu analisis AI untuk event bencana dari aplikasi planning.
    """
    logger.info(f"Planning app triggering AI analysis for emergency event ID: {event_id}")
    result = trigger_emergency_ai_logic(event_id) # Panggil fungsi dari emergency.logic
    return result