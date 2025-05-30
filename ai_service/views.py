# ai_services/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST # Bisa juga GET untuk mengambil hasil log
import json
import logging
from django.utils import timezone

from .models import AiForecastRequestLog, AiModelPerformanceFeedback # , RegionalRiskAnalysisResult
from .forecasting_services import input_preprocessor as fcs_input, core_forecaster, accuracy_evaluator
from .risk_assesment_services import input_preprocessor as ras_input, core_risk_assessor

logger = logging.getLogger(__name__)

@csrf_exempt # Ganti dengan autentikasi yang aman
@require_POST
def api_invoke_staffing_forecast_service(request):
    """
    Service endpoint untuk memicu AI staffing demand forecast.
    Input JSON payload: (lihat input_preprocessor.py)
    {
        "faskes_id": "PKM-XYZ-001", // Ini akan menjadi caller_reference_id
        "period_start": "YYYY-MM-DD",
        "period_end": "YYYY-MM-DD",
        "historical_patient_summary": "...",
        // ... data lainnya ...
        "ai_model_name": "gemini-1.5-pro-latest" // opsional
    }
    Output: Hasil JSON dari AI atau pesan error.
    """
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)

    prepared_input, err = fcs_input.validate_and_prepare_staffing_forecast_input(payload)
    if err:
        return JsonResponse({"error": err}, status=400)

    caller_ref_id = prepared_input["faskes_id"] # Menggunakan faskes_id sebagai referensi pemanggil
    ai_model_name = payload.get("ai_model_name", "gemini-1.5-flash-latest")

    # Panggil core forecaster
    # Di produksi, ini sebaiknya dijalankan sebagai background task (Celery)
    # Untuk saat ini, kita panggil secara sinkron
    forecast_json, error_msg, log_id = core_forecaster.generate_staffing_demand_forecast(
        caller_ref_id=caller_ref_id,
        input_data=prepared_input,
        input_payload_for_log=payload, # Simpan payload asli
        ai_model_name=ai_model_name
    )

    if error_msg:
        return JsonResponse({"error": error_msg, "ai_request_log_id": log_id}, status=500) # Atau status code dari AI

    return JsonResponse({
        "message": "Staffing forecast service invoked successfully.",
        "ai_request_log_id": log_id,
        "forecast_result": forecast_json
    }, status=200) # 200 OK karena hasil langsung ada, atau 202 Accepted jika async

@csrf_exempt # Ganti dengan autentikasi
@require_POST
def api_submit_forecast_feedback_service(request):
    """
    Service endpoint untuk submit data aktual dan feedback terhadap suatu forecast.
    Input JSON payload:
    {
        "ai_request_log_id": <id_dari_AiForecastRequestLog>,
        "actual_data": {
            "staffing": { "Dokter Umum": 5, "Perawat": 12, ... }, // Struktur data aktual staffing
            // bisa ada data aktual lain jika relevan dengan output AI
        },
        "qualitative_feedback": "Prediksi biaya terlalu tinggi..."
    }
    Output: Konfirmasi dan hasil evaluasi akurasi.
    """
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)

    log_id = payload.get("ai_request_log_id")
    actual_data = payload.get("actual_data") # Ini akan menjadi actual_data_json
    feedback_text = payload.get("qualitative_feedback", "")

    if not log_id or not isinstance(actual_data, dict):
        return JsonResponse({"error": "Missing 'ai_request_log_id' or 'actual_data' is not a dict"}, status=400)

    try:
        ai_log_instance = AiForecastRequestLog.objects.get(id=log_id)
        if ai_log_instance.service_type != "staffing_demand_forecast": # Validasi service type
             return JsonResponse({"error": "Feedback can only be submitted for 'staffing_demand_forecast' logs."}, status=400)
    except AiForecastRequestLog.DoesNotExist:
        return JsonResponse({"error": f"AiForecastRequestLog with id {log_id} not found."}, status=404)

    feedback_entry, created = AiModelPerformanceFeedback.objects.update_or_create(
        ai_request_log=ai_log_instance,
        defaults={
            'actual_data_json': actual_data,
            'qualitative_feedback': feedback_text,
            'feedback_provided_at': timezone.now()
        }
    )
    
    # Picu evaluasi akurasi
    try:
        accuracy_evaluator.evaluate_staffing_forecast_accuracy(feedback_entry)
        action = "created" if created else "updated"
        return JsonResponse({
            "message": f"Forecast feedback {action} and accuracy evaluated.",
            "feedback_log_id": feedback_entry.id,
            "accuracy_results": feedback_entry.accuracy_metrics_json,
            "overall_accuracy_score": feedback_entry.overall_accuracy_score
        }, status=201 if created else 200)
    except Exception as e:
        logger.error(f"Error during accuracy evaluation post-feedback for log_id {log_id}: {e}", exc_info=True)
        return JsonResponse({
            "message": "Feedback submitted, but accuracy evaluation encountered an error.",
            "error_details": str(e)
        }, status=207) # Multi-Status


@csrf_exempt # Ganti dengan autentikasi
@require_POST
def api_invoke_regional_risk_assessment_service(request):
    """
    Service endpoint untuk memicu AI Regional Disaster Risk Assessment.
    Input JSON payload:
    {
        "region_identifier": "KAB-XYZ", // ID wilayah, akan jadi caller_reference_id
        "bnpb_data_summary": "Ringkasan data dari BNPB...",
        "ai_model_name": "gemini-1.5-pro-latest" // opsional
    }
    Output: Hasil JSON dari AI atau pesan error.
    """
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)

    prepared_input, err = ras_input.validate_and_prepare_risk_assessment_input(payload)
    if err:
        return JsonResponse({"error": err}, status=400)

    caller_ref_id = prepared_input["region"]
    ai_model_name = payload.get("ai_model_name", "gemini-1.5-flash-latest")

    risk_assessment_json, error_msg, analysis_log_id = core_risk_assessor.assess_regional_disaster_risk(
        caller_ref_id=caller_ref_id,
        input_data=prepared_input,
        input_payload_for_log=payload,
        ai_model_name=ai_model_name
    )

    if error_msg:
        return JsonResponse({"error": error_msg, "analysis_log_id": analysis_log_id}, status=500)

    return JsonResponse({
        "message": "Regional risk assessment service invoked successfully.",
        "analysis_log_id": analysis_log_id,
        "assessment_result": risk_assessment_json
    }, status=200)