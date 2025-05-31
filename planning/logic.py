# planning/logic.py
import logging
from django.utils import timezone
from django.db.models import Q # Untuk query yang lebih kompleks jika perlu

# Impor langsung dari aplikasi ai_services
from ai_service.forecasting_services import input_preprocessor as fcs_input_ai
from ai_service.forecasting_services import core_forecaster as fcs_core_ai
from ai_service.forecasting_services import accuracy_evaluator as fcs_accuracy_ai
# from ai_services.risk_assessment_services import input_preprocessor as ras_input_ai # Jika diperlukan
# from ai_services.risk_assessment_services import core_risk_assessor as ras_core_ai # Jika diperlukan
from ai_service.models import AiForecastRequestLog, AiModelPerformanceFeedback # Untuk query log

logger = logging.getLogger(__name__)

def generate_staffing_forecast(payload: dict):
    """
    Memanggil layanan AI untuk staffing forecast melalui panggilan fungsi langsung.
    Mengembalikan dictionary hasil atau error.
    """
    prepared_input, err = fcs_input_ai.validate_and_prepare_staffing_forecast_input(payload)
    if err:
        logger.warning(f"Input validation failed for staffing forecast: {err}")
        return {"error": err, "ai_request_log_id": None}

    caller_ref_id = prepared_input["faskes_id"] # faskes_id dari payload
    ai_model_name = payload.get("ai_model_name", "gemini-1.5-flash-latest")

    try:
        forecast_json, error_msg, log_id = fcs_core_ai.generate_staffing_demand_forecast(
            caller_ref_id=caller_ref_id,
            input_data=prepared_input,
            input_payload_for_log=payload, # Payload asli untuk log
            ai_model_name=ai_model_name
        )

        if error_msg: # Jika core_forecaster mengembalikan pesan error
            logger.error(f"Core AI forecaster returned error for {caller_ref_id}: {error_msg}")
            return {"error": error_msg, "ai_request_log_id": log_id}
        
        return {
            "message": "Staffing forecast generated successfully.",
            "ai_request_log_id": log_id,
            "forecast_result": forecast_json
        }
    except Exception as e: # Menangkap exception tak terduga dari pemanggilan fungsi
        logger.error(f"Exception calling core_forecaster: {e}", exc_info=True)
        # Pertimbangkan membuat log AiForecastRequestLog dengan status 'failed' di sini
        # jika exception terjadi di luar logic core_forecaster yang sudah membuat log.
        return {"error": f"An unexpected error occurred during forecast generation: {str(e)}", "ai_request_log_id": None}


def submit_forecast_feedback(payload: dict):
    """
    Mengirim feedback dan data aktual, lalu memicu evaluasi akurasi.
    """
    log_id = payload.get("ai_request_log_id")
    actual_data = payload.get("actual_data") # Ini akan disimpan di AiModelPerformanceFeedback.actual_data_json
    feedback_text = payload.get("qualitative_feedback", "")

    if not log_id or not isinstance(actual_data, dict):
        return {"error": "Missing 'ai_request_log_id' or 'actual_data' (must be a dict)."}

    try:
        ai_log_instance = AiForecastRequestLog.objects.get(id=log_id)
        if ai_log_instance.service_type != "staffing_demand_forecast":
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
        
        # Picu evaluasi akurasi
        fcs_accuracy_ai.evaluate_staffing_forecast_accuracy(feedback_entry) # Panggil fungsi dari ai_services
        
        action = "created" if created else "updated"
        return {
            "message": f"Forecast feedback {action} and accuracy evaluated.",
            "feedback_log_id": feedback_entry.id,
            "accuracy_results": feedback_entry.accuracy_metrics_json,
            "overall_accuracy_score": feedback_entry.overall_accuracy_score
        }
    except Exception as e:
        logger.error(f"Error during feedback submission or accuracy evaluation for log_id {log_id}: {e}", exc_info=True)
        return {
            "error": f"Failed to process feedback or evaluate accuracy: {str(e)}"
        }


def get_faskes_forecast_history(faskes_id: str, limit: int = 50):
    """
    Mengambil riwayat forecast untuk faskes tertentu langsung dari database.
    """
    try:
        logs = AiForecastRequestLog.objects.filter(
            caller_reference_id=faskes_id,
            service_type="staffing_demand_forecast",
            processing_status="completed" # Hanya yang berhasil
        ).select_related('performance_feedback').order_by('-requested_at')[:limit]

        results = []
        for log in logs:
            feedback_data = {}
            # Akses related object performance_feedback
            # Perlu dicek apakah ada, karena bisa jadi OneToOneField masih null
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
        return results # Kembalikan list, bisa kosong
    except Exception as e:
        logger.error(f"Error fetching forecast history from DB for {faskes_id}: {e}", exc_info=True)
        return {"error": f"Error fetching data from database: {str(e)}"}


def get_forecast_detail_from_db(log_id: int):
    """ Mengambil detail forecast tunggal langsung dari database. """
    try:
        log_entry = AiForecastRequestLog.objects.select_related('performance_feedback').get(
            id=log_id, 
            service_type="staffing_demand_forecast"
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
            # "raw_ai_response_text": log_entry.raw_ai_response_text, # Mungkin tidak perlu
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