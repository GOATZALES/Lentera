# planning/views.py
from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth.decorators import login_required # Replaced by role_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
import csv
from datetime import datetime, timedelta, date
import json
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied


from authentication.models import Faskes # Faskes model
# Departemen model not directly needed if role_required provides request.departemen and request.faskes
from authentication.views import role_required # Import the custom decorator

from . import logic as planning_logic 
from .models import BudgetPlan

# The get_current_faskes_id function is no longer needed as request.faskes will be used.

@role_required(['departemen'])
def dashboard_view(request):
    faskes_obj = request.faskes # Attached by role_required decorator
    faskes_id = faskes_obj.faskes_id_internal
    faskes_name = faskes_obj.nama_faskes

    context = {
        'faskes_id': faskes_id,
        'faskes_name': faskes_name,
        'error_message': None,
        'latest_forecast_summary': None,
        'upcoming_forecasts_summary': [],
        'accuracy_trend': None,
        'staffing_trend_chart_data_json': json.dumps({}),
        'historical_comparison_chart_data_json': json.dumps({}),
        'recent_alerts': [],
        'forecast_history_list': []
    }

    history_data_result = planning_logic.get_faskes_forecast_history(faskes_id, limit=30)

    if isinstance(history_data_result, dict) and "error" in history_data_result:
        context['error_message'] = f"Gagal memuat riwayat forecast: {history_data_result['error']}"
    elif isinstance(history_data_result, list):
        context['forecast_history_list'] = history_data_result[:7]

        if history_data_result:
            today = date.today()
            future_forecasts = sorted(
                [fc for fc in history_data_result if fc.get("period_start") and datetime.strptime(fc.get("period_start"), "%Y-%m-%d").date() >= today],
                key=lambda x: x.get("period_start")
            )
            
            if future_forecasts:
                context['latest_forecast_summary'] = future_forecasts[0]
                context['upcoming_forecasts_summary'] = future_forecasts[:3]

            valid_accuracies = [
                fc['feedback_info']['overall_accuracy_score']
                for fc in history_data_result 
                if fc.get('feedback_info') and fc['feedback_info'].get('overall_accuracy_score') is not None
            ]
            if valid_accuracies:
                context['accuracy_trend'] = round(sum(valid_accuracies) / len(valid_accuracies), 1)

            staff_trend_labels, predicted_doctors, predicted_nurses = [], [], []
            for forecast in reversed(history_data_result[:15]):
                staff_trend_labels.append(f"{forecast.get('period_start', 'N/A')}")
                demand = forecast.get('parsed_ai_output', {}).get('predicted_staffing_demand', {})
                predicted_doctors.append(demand.get('Dokter Umum', 0))
                predicted_nurses.append(demand.get('Perawat', 0))
            
            context['staffing_trend_chart_data_json'] = json.dumps({
                'labels': staff_trend_labels, 'doctors': predicted_doctors, 'nurses': predicted_nurses
            })

            comp_chart_labels, comp_pred_doctors, comp_actual_doctors = [], [], []
            for forecast in reversed(history_data_result[:10]):
                comp_chart_labels.append(forecast.get("period_start", "N/A"))
                demand = forecast.get('parsed_ai_output', {}).get('predicted_staffing_demand', {})
                comp_pred_doctors.append(demand.get('Dokter Umum', 0))
                feedback_summary = forecast.get("feedback_info", {}).get("actual_data_summary", {})
                comp_actual_doctors.append(feedback_summary.get('Dokter Umum', None))
            
            context['historical_comparison_chart_data_json'] = json.dumps({
                'labels': comp_chart_labels, 'predicted_doctors': comp_pred_doctors, 'actual_doctors': comp_actual_doctors
            })
            
            current_alerts_messages = set()
            if context['latest_forecast_summary'] and context['latest_forecast_summary'].get('parsed_ai_output'):
                alerts = context['latest_forecast_summary']['parsed_ai_output'].get('peak_period_alerts_and_recommendations')
                period_label = f"{context['latest_forecast_summary'].get('period_start')} - {context['latest_forecast_summary'].get('period_end')}"
                if alerts and alerts.lower() not in ["tidak ada.", "tidak ada periode puncak signifikan yang teridentifikasi dari data yang tersedia."]:
                    alert_msg_obj = {"period": period_label, "message": alerts}
                    if alert_msg_obj["message"] not in current_alerts_messages:
                        context['recent_alerts'].append(alert_msg_obj)
                        current_alerts_messages.add(alert_msg_obj["message"])
            
            for fc_upcoming in context['upcoming_forecasts_summary']:
                 if fc_upcoming and fc_upcoming.get('parsed_ai_output'):
                    alerts_up = fc_upcoming['parsed_ai_output'].get('peak_period_alerts_and_recommendations')
                    period_label_up = f"{fc_upcoming.get('period_start')} - {fc_upcoming.get('period_end')}"
                    if alerts_up and alerts_up.lower() not in ["tidak ada.", "tidak ada periode puncak signifikan yang teridentifikasi dari data yang tersedia."]:
                        alert_msg_obj_up = {"period": period_label_up, "message": alerts_up}
                        if alert_msg_obj_up["message"] not in current_alerts_messages:
                             context['recent_alerts'].append(alert_msg_obj_up)
                             current_alerts_messages.add(alert_msg_obj_up["message"])
    else:
        context['error_message'] = "Format data riwayat forecast tidak dikenali."
        
    return render(request, 'dashboard.html', context)

@role_required(['departemen'])
def forecast_detail_view(request, forecast_log_id):
    faskes_obj = request.faskes
    faskes_id = faskes_obj.faskes_id_internal
    faskes_name = faskes_obj.nama_faskes

    context = {'faskes_id': faskes_id, 'faskes_name': faskes_name, 'forecast_log_id': forecast_log_id, 'error_message': None}

    forecast_data_result = planning_logic.get_forecast_detail_from_db(forecast_log_id)

    if isinstance(forecast_data_result, dict) and "error" in forecast_data_result:
        context['error_message'] = f"Gagal memuat detail forecast: {forecast_data_result['error']}"
        context['forecast_detail'] = None
    elif isinstance(forecast_data_result, dict):
        if forecast_data_result.get('caller_reference_id') != faskes_id:
            messages.error(request, "Anda tidak berhak melihat detail forecast ini.")
            return redirect('planning:dashboard')
        context['forecast_detail'] = forecast_data_result
        
        existing_feedback = forecast_data_result.get('feedback_info', {})
        actual_data_json = existing_feedback.get('actual_data_json', {})
        if isinstance(actual_data_json, str):
            try:
                actual_data_json = json.loads(actual_data_json)
            except json.JSONDecodeError:
                actual_data_json = {}
        actual_staffing_data = actual_data_json.get('staffing', {})
        context['actual_staffing_json_for_template'] = json.dumps(actual_staffing_data)
        context['qualitative_feedback_for_template'] = existing_feedback.get('qualitative_feedback', '')
    else:
        context['error_message'] = "Data detail forecast tidak valid."
        context['forecast_detail'] = None

    return render(request, 'forecast_detail.html', context)

@role_required(['departemen'])
@require_POST
def submit_actual_data_view(request, forecast_log_id):
    faskes_obj = request.faskes
    faskes_id = faskes_obj.faskes_id_internal
    
    log_check_result = planning_logic.get_forecast_detail_from_db(forecast_log_id)
    if "error" in log_check_result or log_check_result.get("caller_reference_id") != faskes_id:
        messages.error(request, "Forecast tidak ditemukan atau Anda tidak berhak.")
        return redirect('planning:dashboard')

    actual_staffing = {}
    predicted_roles = log_check_result.get("parsed_ai_output_json", {}).get("predicted_staffing_demand", {}).keys()
    for role in predicted_roles:
        # Use safe_slugify logic from templatetag for consistency if it complexifies role names
        # For simple role names like "Dokter Umum", this direct replacement is okay.
        form_field_name = f"actual_{role.lower().replace(' ', '_').replace('(', '').replace(')', '')}"
        try:
            actual_staffing[role] = int(request.POST.get(form_field_name, 0))
        except ValueError:
            actual_staffing[role] = 0

    qualitative_feedback = request.POST.get('qualitative_feedback', "")

    if not actual_staffing and not qualitative_feedback:
        messages.error(request, "Data aktual staffing atau catatan feedback tidak boleh kosong semua.")
        return redirect('planning:forecast_detail', forecast_log_id=forecast_log_id)

    payload = {
        "ai_request_log_id": int(forecast_log_id),
        "actual_data": {"staffing": actual_staffing},
        "qualitative_feedback": qualitative_feedback
    }
    result = planning_logic.submit_forecast_feedback(payload)

    if "error" in result and result["error"]:
        messages.error(request, f"Gagal submit feedback: {result['error']}")
    elif "message" in result:
        messages.success(request, result['message'])
    else:
        messages.warning(request, "Respon tidak dikenali saat submit feedback.")
    return redirect('planning:forecast_detail', forecast_log_id=forecast_log_id)

@role_required(['departemen'])
def budget_planning_view(request):
    partner = request.faskes # Faskes instance from decorator
    faskes_id = partner.faskes_id_internal
    faskes_name = partner.nama_faskes

    context = {
        'faskes_id': faskes_id,
        'faskes_name': faskes_name,
        'budget_summary': None,
        'form_data': {},
        'page_title': 'Perencanaan Budget SDM Otomatis'
    }

    if request.method == 'POST':
        start_period_str = request.POST.get('start_period_date')
        number_of_months_to_plan = int(request.POST.get('duration_months', 3))
        budget_notes = request.POST.get('budget_notes', "")
        cost_adjustment_percentage = float(request.POST.get('cost_adjustment_percentage', 0)) / 100.0
        context['form_data'] = request.POST

        try:
            start_period_date = datetime.strptime(start_period_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            messages.error(request, "Format tanggal awal periode tidak valid. Gunakan YYYY-MM-DD.")
            return render(request, 'budget_planning_form.html', context)

        if not 1 <= number_of_months_to_plan <= 12:
            messages.error(request, "Durasi perencanaan harus antara 1 hingga 12 bulan.")
            return render(request, 'budget_planning_form.html', context)

        monthly_periods_to_forecast = []
        current_month_start = start_period_date
        for _ in range(number_of_months_to_plan):
            if current_month_start.month == 12:
                current_month_end = current_month_start.replace(day=31)
            else:
                current_month_end = current_month_start.replace(month=current_month_start.month + 1, day=1) - timedelta(days=1)
            monthly_periods_to_forecast.append({"start": current_month_start, "end": current_month_end})
            if current_month_start.month == 12:
                current_month_start = current_month_start.replace(year=current_month_start.year + 1, month=1, day=1)
            else:
                current_month_start = current_month_start.replace(month=current_month_start.month + 1, day=1)
        end_period_date = monthly_periods_to_forecast[-1]['end']

        aggregated_min_cost, aggregated_max_cost = 0, 0
        monthly_forecast_details = []
        all_sub_forecasts_successful = True
        # forecast_log_ids_for_budget = [] # Uncomment if storing log IDs

        for period in monthly_periods_to_forecast:
            # Construct historical_summary_text and seasonal_patterns_text from partner object
            historical_summary_text = f"Kunjungan rata-rata mingguan: {partner.rata_kunjungan_harian_seminggu_json}. Puncak diketahui: {partner.periode_puncak_diketahui_json}."
            seasonal_patterns_text = f"Pola musiman umum. Layanan utama: {partner.layanan_unggulan_json}."
            
            payload_for_ai = {
                "faskes_id": faskes_id,
                "period_start": period["start"].strftime("%Y-%m-%d"),
                "period_end": period["end"].strftime("%Y-%m-%d"),
                "historical_patient_summary": historical_summary_text,
                "seasonal_disease_patterns": seasonal_patterns_text,
            }
            ai_result = planning_logic.generate_staffing_forecast(payload_for_ai)

            if "error" in ai_result and ai_result["error"]:
                messages.error(request, f"Gagal forecast {period['start']} - {period['end']}: {ai_result.get('error', 'Error')}")
                all_sub_forecasts_successful = False
                monthly_forecast_details.append({"period": f"{period['start']} - {period['end']}", "error": ai_result.get('error', 'Kesalahan tidak diketahui')})
            elif "forecast_result" in ai_result:
                forecast_output = ai_result["forecast_result"]
                log_id = ai_result.get("ai_request_log_id")
                # if log_id: forecast_log_ids_for_budget.append(log_id) # Uncomment if storing
                cost_range = forecast_output.get("estimated_cost_range_rp", {})
                current_min_cost, current_max_cost = float(cost_range.get("min_cost", 0)), float(cost_range.get("max_cost", 0))
                aggregated_min_cost += current_min_cost
                aggregated_max_cost += current_max_cost
                monthly_forecast_details.append({
                    "period_label": period["start"].strftime("%B %Y"), "log_id": log_id,
                    "predicted_staffing": forecast_output.get("predicted_staffing_demand", {}),
                    "estimated_min_cost": current_min_cost, "estimated_max_cost": current_max_cost,
                    "alerts_recommendations": forecast_output.get("peak_period_alerts_and_recommendations", "")
                })
            else:
                all_sub_forecasts_successful = False
                monthly_forecast_details.append({"period": f"{period['start']} - {period['end']}", "error": "Respon AI tidak valid."})

        if all_sub_forecasts_successful:
             messages.success(request, "Perencanaan budget berhasil dihitung.")
        else:
             messages.warning(request, "Beberapa forecast bulanan gagal, estimasi budget mungkin tidak lengkap.")

        adjusted_min_cost = aggregated_min_cost * (1 + cost_adjustment_percentage)
        adjusted_max_cost = aggregated_max_cost * (1 + cost_adjustment_percentage)

        context['budget_summary'] = {
            "budget_period_start": start_period_date.strftime("%d %B %Y"),
            "budget_period_end": end_period_date.strftime("%d %B %Y"),
            "total_adjusted_min_cost_rp": adjusted_min_cost,
            "total_adjusted_max_cost_rp": adjusted_max_cost,
            "monthly_breakdown": monthly_forecast_details,
            "all_sub_forecasts_successful": all_sub_forecasts_successful,
            "user_notes": budget_notes,
            "cost_adjustment_percentage_input": cost_adjustment_percentage * 100,
            # "related_ai_log_ids": forecast_log_ids_for_budget # Uncomment if storing
        }
        
        if BudgetPlan._meta.app_label == 'planning':
            try:
                budget_plan_name = f"Budget {partner.nama_faskes} ({start_period_date.strftime('%b %Y')}-{end_period_date.strftime('%b %Y')})"
                BudgetPlan.objects.create(
                    faskes_id_temp=faskes_id, plan_name=budget_plan_name,
                    period_start=start_period_date, period_end=end_period_date,
                    total_estimated_cost_min=adjusted_min_cost, total_estimated_cost_max=adjusted_max_cost,
                    notes=f"Catatan: {budget_notes}\nAdj: {cost_adjustment_percentage*100}%\nDetail:\n{json.dumps(monthly_forecast_details, default=str)}",
                    # related_ai_log_ids_json=forecast_log_ids_for_budget # Uncomment if storing
                )
                messages.info(request, "Rencana budget telah disimpan.")
            except Exception as e:
                messages.error(request, f"Gagal menyimpan rencana budget: {e}")
    return render(request, 'budget_planning_form.html', context)

@role_required(['departemen'])
def export_forecast_data_csv(request):
    faskes_obj = request.faskes
    faskes_id = faskes_obj.faskes_id_internal
    
    forecast_logs_result = planning_logic.get_faskes_forecast_history(faskes_id, limit=200)

    if isinstance(forecast_logs_result, dict) and "error" in forecast_logs_result:
        messages.error(request, f"Gagal mengambil data untuk export: {forecast_logs_result['error']}")
        return redirect('planning:dashboard')
    if not isinstance(forecast_logs_result, list) or not forecast_logs_result:
        messages.warning(request, "Tidak ada data forecast untuk diexport.")
        return redirect('planning:dashboard')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="forecast_data_{faskes_id}_{date.today().strftime("%Y%m%d")}.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'Log ID', 'Faskes ID', 'Periode Mulai', 'Periode Selesai', 'Diminta Pada', 
        'Prediksi Dokter Umum', 'Prediksi Perawat', 'Prediksi Bidan',
        'Estimasi Biaya Min (Rp)', 'Estimasi Biaya Max (Rp)', 
        'Alert & Rekomendasi', 'Model AI',
        'Aktual Dokter Umum', 'Aktual Perawat', 'Aktual Bidan', 
        'Skor Akurasi Keseluruhan (%)', 'Feedback Kualitatif'
    ])
    for log in forecast_logs_result:
        parsed_output = log.get('parsed_ai_output', {})
        predicted_staff = parsed_output.get('predicted_staffing_demand', {}) if parsed_output else {}
        cost_range = parsed_output.get('estimated_cost_range_rp', {}) if parsed_output else {}
        feedback = log.get('feedback_info', {})
        actual_staff = feedback.get('actual_data_summary', {})
        writer.writerow([
            log.get('ai_request_log_id'), log.get('caller_reference_id'),
            log.get('period_start'), log.get('period_end'), log.get('requested_at'),
            predicted_staff.get('Dokter Umum'), predicted_staff.get('Perawat'), predicted_staff.get('Bidan'),
            cost_range.get('min_cost'), cost_range.get('max_cost'),
            parsed_output.get('peak_period_alerts_and_recommendations') if parsed_output else '',
            log.get('ai_model_name_used'),
            actual_staff.get('Dokter Umum'), actual_staff.get('Perawat'), actual_staff.get('Bidan'),
            feedback.get('overall_accuracy_score'), feedback.get('qualitative_feedback')
        ])
    return response

@role_required(['departemen'])
def disaster_risk_dashboard_view(request):
    faskes_obj = request.faskes
    faskes_id = faskes_obj.faskes_id_internal
    faskes_name = faskes_obj.nama_faskes
    
    data = planning_logic.get_disaster_risk_dashboard_data()
    context = {
        'faskes_id': faskes_id,
        'faskes_name': faskes_name,
        'active_disaster_events': data.get("active_disaster_events"),
        'page_title': "Dashboard Penilaian Risiko Bencana"
    }
    return render(request, 'disaster_risk_dashboard.html', context)

@role_required(['departemen'])
def disaster_event_detail_for_planning_view(request, event_id):
    faskes_obj = request.faskes
    faskes_id = faskes_obj.faskes_id_internal
    faskes_name = faskes_obj.nama_faskes
    
    event, error = planning_logic.get_disaster_event_planning_details(event_id)
    if error:
        messages.error(request, error)
        return redirect('planning:disaster_dashboard')

    context = {
        'faskes_id': faskes_id,
        'faskes_name': faskes_name,
        'event': event,
        'page_title': f"Detail Risiko: {event.disaster_type if event else 'Error'}"
    }
    return render(request, 'disaster_event_detail.html', context)

@role_required(['departemen'])
@require_POST
def trigger_disaster_analysis_view(request, event_id):
    # faskes_id = request.faskes.faskes_id_internal # Available if needed for logging or validation
    result = planning_logic.trigger_emergency_event_ai_analysis(event_id)
    
    if result and result.get("success"):
        messages.success(request, result.get("message", "Analisis AI berhasil dijalankan."))
    elif result and result.get("error"):
        messages.error(request, result.get("error", "Gagal menjalankan analisis AI."))
    else:
        messages.warning(request, "Hasil analisis AI tidak diketahui.")
    return redirect('planning:disaster_event_detail', event_id=event_id)