# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
import csv
from datetime import datetime, timedelta, date
import json
from django.views.decorators.http import require_POST

from . import logic as planning_logic # Menggunakan logic.py
from .models import BudgetPlan # Jika menggunakan model BudgetPlan

# Asumsikan Faskes ID didapat dari user yang login atau parameter URL
def get_current_faskes_id(request):
    # Implementasi cara mendapatkan Faskes ID yang relevan
    # Misalnya, jika user login adalah representasi Faskes:
    # if hasattr(request.user, 'faskesprofile') and request.user.faskesprofile:
    #     return request.user.faskesprofile.faskes_id 
    return "FKS001-JKTSEL" # Placeholder, ganti dengan logika sebenarnya

# @login_required
def dashboard_view(request):
    faskes_id = get_current_faskes_id(request)
    context = {'faskes_id': faskes_id, 'forecast_history': [], 'error_message': None}
    
    # Panggil fungsi logic
    history_data_result = planning_logic.get_faskes_forecast_history(faskes_id)

    if isinstance(history_data_result, dict) and "error" in history_data_result:
        context['error_message'] = f"Gagal memuat riwayat forecast: {history_data_result['error']}"
    elif isinstance(history_data_result, list):
        context['forecast_history'] = history_data_result
        # Proses data untuk chart (sama seperti sebelumnya)
        chart_labels = []
        predicted_doctors_data = []
        actual_doctors_data = []

        for forecast in history_data_result[:10]: # Ambil 10 terbaru untuk grafik
            chart_labels.append(forecast.get("period_start", "N/A"))
            parsed_output = forecast.get("parsed_ai_output", {})
            predicted_staffing = parsed_output.get("predicted_staffing_demand", {}) if parsed_output else {}
            predicted_doctors_data.append(predicted_staffing.get("Dokter Umum", 0))
            
            feedback_staffing = forecast.get("feedback_info", {}).get("actual_data_summary", {})
            actual_doctors_data.append(feedback_staffing.get("Dokter Umum", None))

        context['chart_data'] = {
            'labels': chart_labels[::-1],
            'predicted_doctors': predicted_doctors_data[::-1],
            'actual_doctors': actual_doctors_data[::-1]
        }
        context['chart_data_json'] = json.dumps(context['chart_data'])
    else: # Handle jika bukan list atau dict error (tidak diharapkan)
        context['error_message'] = "Format data riwayat forecast tidak dikenali."

    return render(request, 'dashboard.html', context)

# @login_required
def forecast_detail_view(request, forecast_log_id):
    faskes_id = get_current_faskes_id(request)
    context = {'faskes_id': faskes_id, 'forecast_log_id': forecast_log_id, 'error_message': None}

    # Panggil fungsi logic
    forecast_data_result = planning_logic.get_forecast_detail_from_db(forecast_log_id)

    if isinstance(forecast_data_result, dict) and "error" in forecast_data_result:
        context['error_message'] = f"Gagal memuat detail forecast: {forecast_data_result['error']}"
        context['forecast_detail'] = None
    elif isinstance(forecast_data_result, dict):
        if forecast_data_result.get('caller_reference_id') != faskes_id:
            messages.error(request, "Anda tidak berhak melihat detail forecast ini.")
            return redirect('planning:dashboard')
        context['forecast_detail'] = forecast_data_result
        
        # Untuk prefill form feedback (jika ada)
        existing_feedback = forecast_data_result.get('feedback_info', {})

        # Pastikan actual_data_json adalah dict, bukan string JSON
        actual_data_json = existing_feedback.get('actual_data_json', {})

        if isinstance(actual_data_json, str):
            try:
                actual_data_json = json.loads(actual_data_json)
            except json.JSONDecodeError:
                actual_data_json = {}

        actual_staffing_data = actual_data_json.get('staffing', {})
        context['actual_staffing_json_for_template'] = json.dumps(actual_staffing_data) # Untuk JS prefill
        context['qualitative_feedback_for_template'] = existing_feedback.get('qualitative_feedback', '')
    else:
        context['error_message'] = "Data detail forecast tidak valid."
        context['forecast_detail'] = None

    return render(request, 'forecast_detail.html', context)


# @login_required
@require_POST
def submit_actual_data_view(request, forecast_log_id):
    faskes_id = get_current_faskes_id(request)
    
    log_check_result = planning_logic.get_forecast_detail_from_db(forecast_log_id)
    if "error" in log_check_result or log_check_result.get("caller_reference_id") != faskes_id:
        messages.error(request, "Forecast tidak ditemukan atau Anda tidak berhak.")
        return redirect('planning:dashboard')

    actual_staffing = {}
    # Asumsikan parsed_ai_output_json dan predicted_staffing_demand ada
    predicted_roles = log_check_result.get("parsed_ai_output_json", {}).get("predicted_staffing_demand", {}).keys()
    for role in predicted_roles:
        form_field_name = f"actual_{role.lower().replace(' ', '_').replace('(', '').replace(')', '')}"
        try:
            actual_staffing[role] = int(request.POST.get(form_field_name, 0))
        except ValueError:
            actual_staffing[role] = 0

    qualitative_feedback = request.POST.get('qualitative_feedback', "")

    if not actual_staffing and not qualitative_feedback: # Minimal salah satu harus ada
        messages.error(request, "Data aktual staffing atau catatan feedback tidak boleh kosong semua.")
        return redirect('planning:forecast_detail', forecast_log_id=forecast_log_id)

    payload = {
        "ai_request_log_id": int(forecast_log_id),
        "actual_data": {
            "staffing": actual_staffing
        },
        "qualitative_feedback": qualitative_feedback
    }

    # Panggil fungsi logic
    result = planning_logic.submit_forecast_feedback(payload)

    if "error" in result and result["error"]:
        messages.error(request, f"Gagal submit feedback: {result['error']}")
    elif "message" in result:
        messages.success(request, result['message'])
    else:
        messages.warning(request, "Respon tidak dikenali saat submit feedback.")

    return redirect('planning:forecast_detail', forecast_log_id=forecast_log_id)


# @login_required
def budget_planning_view(request):
    faskes_id = get_current_faskes_id(request)
    context = {'faskes_id': faskes_id, 'budget_details': None, 'form_data': {}}

    if request.method == 'POST':
        quarter_start_str = request.POST.get('quarter_start_date')
        historical_summary_q = request.POST.get('historical_summary_quarterly', "Data historis umum untuk kuartal ini.")
        seasonal_patterns_q = request.POST.get('seasonal_patterns_quarterly', "Pola musiman umum untuk kuartal ini.")
        bmkg_weather_q = request.POST.get('bmkg_weather_forecast_quarterly', '') # Tambahkan ini
        local_events_q = request.POST.get('local_events_calendar_quarterly', '') # Tambahkan ini
        mudik_info_q = request.POST.get('mudik_calendar_info_quarterly', '') # Tambahkan ini


        context['form_data'] = request.POST

        try:
            quarter_start_date = datetime.strptime(quarter_start_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            messages.error(request, "Format tanggal awal kuartal tidak valid.")
            return render(request, 'budget_planning_form.html', context)

        periods = []
        current_start = quarter_start_date
        for i_month in range(3): # Untuk 3 bulan
            month_num_for_form = current_start.month # Untuk mengambil input spesifik bulan
            
            # Tentukan akhir bulan
            if current_start.month == 12:
                current_end = current_start.replace(day=31)
            else:
                current_end = current_start.replace(month=current_start.month + 1, day=1) - timedelta(days=1)
            
            periods.append({
                "start": current_start, 
                "end": current_end, 
                "month_form_key_suffix": f"month_{month_num_for_form}" # Untuk ambil data form per bulan
            })
            
            if current_start.month == 12: # Pindah ke bulan berikutnya
                current_start = current_start.replace(year=current_start.year+1, month=1, day=1)
            else:
                current_start = current_start.replace(month=current_start.month + 1, day=1)

        total_min_cost_quarter = 0
        total_max_cost_quarter = 0
        monthly_forecasts_details = []
        all_ai_requests_successful = True
        related_log_ids = [] # Untuk BudgetPlan model

        for period in periods:
            # Ambil input spesifik bulan jika ada, jika tidak pakai input kuartalan
            hist_summary_period = request.POST.get(f'historical_summary_{period["month_form_key_suffix"]}', '').strip() or historical_summary_q
            seas_pattern_period = request.POST.get(f'seasonal_patterns_{period["month_form_key_suffix"]}', '').strip() or seasonal_patterns_q
            # Tambahkan untuk field lain juga jika ada input per bulan
            
            payload = {
                "faskes_id": faskes_id,
                "period_start": period["start"].strftime("%Y-%m-%d"),
                "period_end": period["end"].strftime("%Y-%m-%d"),
                "historical_patient_summary": hist_summary_period,
                "seasonal_disease_patterns": seas_pattern_period,
                "bmkg_weather_forecast": bmkg_weather_q, # Sementara pakai yg kuartalan, bisa dibuat per bulan juga
                "local_events_calendar": local_events_q,
                "mudik_calendar_info": mudik_info_q,
            }
            
            # Panggil fungsi logic
            result = planning_logic.generate_staffing_forecast(payload)

            if "error" in result and result["error"]:
                messages.error(request, f"Gagal mendapatkan forecast untuk periode {period['start']} - {period['end']}: {result.get('error', 'Unknown error')}")
                all_ai_requests_successful = False
                monthly_forecasts_details.append({"period": f"{period['start']} to {period['end']}", "error": result.get('error', 'Unknown error')})
                continue
            
            forecast_output = result.get("forecast_result",{})
            log_id = result.get("ai_request_log_id")
            if log_id:
                related_log_ids.append(log_id)

            monthly_forecasts_details.append({
                "period": f"{period['start']} to {period['end']}",
                "log_id": log_id,
                "details": forecast_output
            })

            cost_range = forecast_output.get("estimated_cost_range_rp", {})
            total_min_cost_quarter += float(cost_range.get("min_cost", 0))
            total_max_cost_quarter += float(cost_range.get("max_cost", 0))

        if all_ai_requests_successful:
             messages.success(request, "Perencanaan budget kuartalan berhasil dihitung.")
        else:
             messages.warning(request, "Beberapa forecast gagal, estimasi budget mungkin tidak lengkap.")

        context['budget_details'] = {
            "quarter_start": quarter_start_date.strftime("%Y-%m-%d"),
            "total_min_cost_rp": total_min_cost_quarter,
            "total_max_cost_rp": total_max_cost_quarter,
            "monthly_breakdown": monthly_forecasts_details,
            "all_successful": all_ai_requests_successful
        }
        
        if BudgetPlan._meta.app_label == 'planning' and all_ai_requests_successful: # Pastikan model ada dan semua berhasil
            try:
                BudgetPlan.objects.create(
                    faskes_id_temp=faskes_id,
                    plan_name=f"Budget Kuartal {quarter_start_date.strftime('%B %Y')}",
                    period_start=quarter_start_date,
                    period_end=periods[-1]['end'],
                    total_estimated_cost_min=total_min_cost_quarter,
                    total_estimated_cost_max=total_max_cost_quarter,
                    notes=f"Agregasi forecast. Rincian: {json.dumps(monthly_forecasts_details, default=str)}",
                    # related_ai_log_ids_json=related_log_ids # Jika ada field ini di model
                )
                messages.info(request, "Rencana budget telah disimpan.")
            except Exception as e:
                messages.error(request, f"Gagal menyimpan rencana budget: {e}")

    return render(request, 'budget_planning_form.html', context)


# @login_required
def export_forecast_data_csv(request):
    faskes_id = get_current_faskes_id(request)
    
    # Panggil fungsi logic
    forecast_logs_result = planning_logic.get_faskes_forecast_history(faskes_id, limit=200) # Ambil lebih banyak untuk export

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
        'Prediksi Dokter Umum', 'Prediksi Perawat', 'Prediksi Bidan', # Tambah role lain
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
            log.get('ai_request_log_id'),
            log.get('caller_reference_id'),
            log.get('period_start'),
            log.get('period_end'),
            log.get('requested_at'),
            predicted_staff.get('Dokter Umum'),
            predicted_staff.get('Perawat'),
            predicted_staff.get('Bidan'),
            cost_range.get('min_cost'),
            cost_range.get('max_cost'),
            parsed_output.get('peak_period_alerts_and_recommendations') if parsed_output else '',
            log.get('ai_model_name_used'),
            actual_staff.get('Dokter Umum'),
            actual_staff.get('Perawat'),
            actual_staff.get('Bidan'),
            feedback.get('overall_accuracy_score'),
            feedback.get('qualitative_feedback')
        ])
    return response