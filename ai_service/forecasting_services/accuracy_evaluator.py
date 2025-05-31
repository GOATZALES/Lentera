# ai_services/forecasting_services/accuracy_evaluator.py
import logging
from django.utils import timezone
from ..models import AiModelPerformanceFeedback # , AiForecastRequestLog (jika perlu akses data input asli)

logger = logging.getLogger(__name__)

def evaluate_staffing_forecast_accuracy(feedback_instance: AiModelPerformanceFeedback):
    """
    Mengevaluasi akurasi prediksi staf berdasarkan data aktual.
    feedback_instance adalah instance dari AiModelPerformanceFeedback.
    """
    if not (feedback_instance.ai_request_log and \
            feedback_instance.ai_request_log.parsed_ai_output_json and \
            feedback_instance.actual_data_json):
        logger.warning(f"Missing data to evaluate accuracy for feedback ID {feedback_instance.id}")
        feedback_instance.accuracy_metrics_json = {"error": "Missing prediction or actual data."}
        feedback_instance.save()
        return

    try:
        # Ambil bagian prediksi staffing dari output AI yang tersimpan
        predicted_staffing = feedback_instance.ai_request_log.parsed_ai_output_json.get("predicted_staffing_demand", {})
        # Ambil data aktual staffing dari feedback
        actual_staffing = feedback_instance.actual_data_json.get("staffing", {}) # Asumsi formatnya {"staffing": {"Dokter Umum": X, ...}}

        if not isinstance(predicted_staffing, dict) or not isinstance(actual_staffing, dict):
            raise ValueError("Predicted or actual staffing data is not in the expected dictionary format.")

        accuracy_scores = {}
        total_predicted_staff = 0
        total_actual_staff = 0
        total_abs_error = 0
        roles_with_perfect_match = 0
        num_roles_evaluated = 0

        all_roles = set(predicted_staffing.keys()) | set(actual_staffing.keys())

        for role in all_roles:
            num_roles_evaluated +=1
            pred_val = int(predicted_staffing.get(role, 0)) # Pastikan integer
            act_val = int(actual_staffing.get(role, 0))   # Pastikan integer

            total_predicted_staff += pred_val
            total_actual_staff += act_val
            
            abs_error = abs(pred_val - act_val)
            total_abs_error += abs_error
            
            if pred_val == act_val:
                roles_with_perfect_match +=1

            if act_val > 0:
                mape = (abs_error / act_val) * 100
                accuracy_scores[role] = {"predicted": pred_val, "actual": act_val, "abs_error": abs_error, "mape_percent": round(mape, 2)}
            else:
                accuracy_scores[role] = {"predicted": pred_val, "actual": act_val, "abs_error": abs_error, "mape_percent": 0.0 if pred_val == 0 else None}
        
        overall_metric = None
        if total_actual_staff > 0:
            # Menggunakan 1 - (MAE / rata-rata aktual per role) atau metrik lain
            # Atau bisa juga % role yang prediksinya tepat
             overall_metric = (roles_with_perfect_match / num_roles_evaluated) * 100 if num_roles_evaluated > 0 else 0.0
        elif total_abs_error == 0 : # Jika total aktual 0 dan total error 0, maka 100% akurat
            overall_metric = 100.0
        
        feedback_instance.accuracy_metrics_json = accuracy_scores
        feedback_instance.overall_accuracy_score = round(overall_metric, 2) if overall_metric is not None else None
        feedback_instance.accuracy_calculated_at = timezone.now()
        feedback_instance.save()
        logger.info(f"Accuracy evaluated for feedback ID {feedback_instance.id}. Overall: {feedback_instance.overall_accuracy_score}%")

    except Exception as e:
        logger.error(f"Error evaluating accuracy for feedback ID {feedback_instance.id}: {e}", exc_info=True)
        feedback_instance.accuracy_metrics_json = {"error": f"Evaluation failed: {str(e)}"}
        feedback_instance.save()