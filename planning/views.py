# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
import csv
from datetime import datetime, timedelta, date
import json
from django.views.decorators.http import require_POST

from authentication.models import Faskes

from . import logic as planning_logic # Menggunakan logic.py
from .models import BudgetPlan # Jika menggunakan model BudgetPlan

# Asumsikan Faskes ID didapat dari user yang login atau parameter URL
def get_current_faskes_id(request):
    # Implementasi cara mendapatkan Faskes ID yang relevan
    # Misalnya, jika user login adalah representasi Faskes:
    # if hasattr(request.user, 'faskesprofile') and request.user.faskesprofile:
    #     return request.user.faskesprofile.faskes_id 
    return "FKS001-JKTSEL" # Placeholder, ganti dengan logika sebenarnya

#@login_required # Pastikan ini aktif jika sudah ada sistem login Faskes
def dashboard_view(request):
    faskes_id = get_current_faskes_id(request) # Ganti dengan ID Faskes yang login
    context = {
        'faskes_id': faskes_id,
        'error_message': None,
        'latest_forecast_summary': None,
        'upcoming_forecasts_summary': [], # Untuk beberapa hari/minggu ke depan
        'accuracy_trend': None, # Rata-rata akurasi
        'staffing_trend_chart_data_json': json.dumps({}),
        'historical_comparison_chart_data_json': json.dumps({}),
        'recent_alerts': [],
        'forecast_history_list': [] # Ganti nama dari forecast_history
    }

    # 1. Ambil Riwayat Forecast (misal 30 hari terakhir untuk tren & history list)
    # Anda mungkin perlu fungsi baru di logic untuk get data dengan rentang tanggal
    # Untuk sekarang kita ambil beberapa data terbaru saja
    history_data_result = planning_logic.get_faskes_forecast_history(faskes_id, limit=30) # Ambil 30 log terakhir

    if isinstance(history_data_result, dict) and "error" in history_data_result:
        context['error_message'] = f"Gagal memuat riwayat forecast: {history_data_result['error']}"
    elif isinstance(history_data_result, list):
        context['forecast_history_list'] = history_data_result[:7] # Tampilkan 7 terbaru di tabel

        if history_data_result:
            # 2. Ringkasan Forecast Terkini (ambil yang paling baru dengan tanggal mulai >= hari ini)
            today = date.today()
            future_forecasts = sorted(
                [fc for fc in history_data_result if fc.get("period_start") and datetime.strptime(fc.get("period_start"), "%Y-%m-%d").date() >= today],
                key=lambda x: x.get("period_start")
            )
            
            if future_forecasts:
                context['latest_forecast_summary'] = future_forecasts[0] # Paling dekat dengan hari ini
                # Ambil beberapa forecast mendatang untuk ringkasan
                context['upcoming_forecasts_summary'] = future_forecasts[:3]


            # 3. Tren Akurasi Keseluruhan (dari feedback yang ada)
            # Ini memerlukan query ke AiModelPerformanceFeedback atau join di logic.py
            # Untuk contoh:
            valid_accuracies = [
                fc['feedback_info']['overall_accuracy_score']
                for fc in history_data_result 
                if fc.get('feedback_info') and fc['feedback_info'].get('overall_accuracy_score') is not None
            ]
            if valid_accuracies:
                context['accuracy_trend'] = round(sum(valid_accuracies) / len(valid_accuracies), 1)

            # 4. Data untuk Grafik Tren Kebutuhan Staf (misal Dokter Umum & Perawat)
            staff_trend_labels = []
            predicted_doctors = []
            predicted_nurses = []
            # Ambil data dari history_data_result yang diurutkan berdasarkan tanggal (asumsi sudah urut)
            # Balik urutan agar dari terlama ke terbaru untuk grafik
            for forecast in reversed(history_data_result[:15]): # Ambil 15 data terakhir untuk tren
                staff_trend_labels.append(f"{forecast.get('period_start', 'N/A')}")
                demand = forecast.get('parsed_ai_output', {}).get('predicted_staffing_demand', {})
                predicted_doctors.append(demand.get('Dokter Umum', 0))
                predicted_nurses.append(demand.get('Perawat', 0))
            
            context['staffing_trend_chart_data_json'] = json.dumps({
                'labels': staff_trend_labels,
                'doctors': predicted_doctors,
                'nurses': predicted_nurses
            })

            # 5. Data untuk Grafik Perbandingan Prediksi vs Aktual (lebih interaktif)
            # Ini bisa sama dengan yang sebelumnya, atau Anda bisa buat lebih spesifik.
            # Kita akan menggunakan chart_data yang sama seperti sebelumnya untuk perbandingan Dokter Umum
            # tapi akan lebih baik jika bisa filter jenis nakes di frontend.
            comp_chart_labels = []
            comp_pred_doctors = []
            comp_actual_doctors = []
            for forecast in reversed(history_data_result[:10]): # Ambil 10 terbaru
                comp_chart_labels.append(forecast.get("period_start", "N/A"))
                demand = forecast.get('parsed_ai_output', {}).get('predicted_staffing_demand', {})
                comp_pred_doctors.append(demand.get('Dokter Umum', 0))
                feedback_summary = forecast.get("feedback_info", {}).get("actual_data_summary", {})
                comp_actual_doctors.append(feedback_summary.get('Dokter Umum', None)) # None jika tidak ada data aktual
            
            context['historical_comparison_chart_data_json'] = json.dumps({
                'labels': comp_chart_labels,
                'predicted_doctors': comp_pred_doctors,
                'actual_doctors': comp_actual_doctors
            })
            
            # 6. Alert & Rekomendasi Terbaru
            if context['latest_forecast_summary'] and context['latest_forecast_summary'].get('parsed_ai_output'):
                alerts = context['latest_forecast_summary']['parsed_ai_output'].get('peak_period_alerts_and_recommendations')
                if alerts and alerts.lower() not in ["tidak ada.", "tidak ada periode puncak signifikan yang teridentifikasi dari data yang tersedia."]:
                    context['recent_alerts'].append({
                        "period": context['latest_forecast_summary'].get('forecasting_period', 'Periode terkini'),
                        "message": alerts
                        })
            # Anda bisa juga mengambil alert dari beberapa forecast mendatang
            for fc_upcoming in context['upcoming_forecasts_summary']:
                 if fc_upcoming and fc_upcoming.get('parsed_ai_output'):
                    alerts_up = fc_upcoming['parsed_ai_output'].get('peak_period_alerts_and_recommendations')
                    if alerts_up and alerts_up.lower() not in ["tidak ada.", "tidak ada periode puncak signifikan yang teridentifikasi dari data yang tersedia."] and alerts_up not in [a['message'] for a in context['recent_alerts']]:
                         context['recent_alerts'].append({
                            "period": f"{fc_upcoming.get('period_start')} - {fc_upcoming.get('period_end')}",
                            "message": alerts_up
                         })


    else:
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
    # Dapatkan instance FaskesPartner untuk mengambil data default jika ada
    try:
        partner = Faskes.objects.get(faskes_id_internal=faskes_id)
    except Faskes.DoesNotExist:
        messages.error(request, f"Data Faskes Partner dengan ID {faskes_id} tidak ditemukan.")
        return redirect('planning:dashboard') # atau halaman lain

    context = {
        'faskes_id': faskes_id,
        'faskes_name': partner.nama_faskes, # Tambahkan nama faskes untuk UI
        'budget_summary': None,
        'form_data': {}, # Untuk prefill form jika ada error
        'page_title': 'Perencanaan Budget SDM Otomatis' # Untuk base template
    }

    if request.method == 'POST':
        # Input utama dari Faskes hanya periode dan mungkin catatan/penyesuaian umum
        start_period_str = request.POST.get('start_period_date') # Misal, YYYY-MM-DD awal periode budget (kuartal/semester)
        number_of_months_to_plan = int(request.POST.get('duration_months', 3)) # Default 3 bulan (kuartal)
        budget_notes = request.POST.get('budget_notes', "")
        
        # (Opsional) Faskes bisa memberikan persentase penyesuaian biaya umum
        cost_adjustment_percentage = float(request.POST.get('cost_adjustment_percentage', 0)) / 100.0

        context['form_data'] = request.POST # Simpan data form

        try:
            start_period_date = datetime.strptime(start_period_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            messages.error(request, "Format tanggal awal periode tidak valid. Gunakan YYYY-MM-DD.")
            return render(request, 'planning/budget_planning_form.html', context)

        if not 1 <= number_of_months_to_plan <= 12:
            messages.error(request, "Durasi perencanaan harus antara 1 hingga 12 bulan.")
            return render(request, 'planning/budget_planning_form.html', context)

        # Bagi periode menjadi sub-periode per bulan untuk forecasting
        monthly_periods_to_forecast = []
        current_month_start = start_period_date
        for _ in range(number_of_months_to_plan):
            # Tentukan akhir bulan
            if current_month_start.month == 12:
                current_month_end = current_month_start.replace(day=31)
            else:
                current_month_end = current_month_start.replace(month=current_month_start.month + 1, day=1) - timedelta(days=1)
            
            monthly_periods_to_forecast.append({
                "start": current_month_start, 
                "end": current_month_end,
            })
            
            # Pindah ke awal bulan berikutnya
            if current_month_start.month == 12:
                current_month_start = current_month_start.replace(year=current_month_start.year + 1, month=1, day=1)
            else:
                current_month_start = current_month_start.replace(month=current_month_start.month + 1, day=1)
        
        end_period_date = monthly_periods_to_forecast[-1]['end'] # Akhir periode budget keseluruhan

        aggregated_min_cost = 0
        aggregated_max_cost = 0
        monthly_forecast_details = []
        all_sub_forecasts_successful = True
        forecast_log_ids_for_budget = []

        for period in monthly_periods_to_forecast:
            # Payload untuk AI service menggunakan data default Faskes dari DB
            # Tidak ada input manual data eksternal di sini
            # Data historis dan seasonal diambil dari profil FaskesPartner
            
            # Ringkas data historis & seasonal dari FaskesPartner.model
            # Ini bisa dibuat lebih cerdas untuk mengambil yang relevan dengan periode.
            # Untuk demo, kita ambil yang ada di JSON field.
            historical_summary_text = f"Kunjungan rata-rata mingguan: {partner.rata_kunjungan_harian_seminggu_json}. Puncak diketahui: {partner.periode_puncak_diketahui_json}."
            seasonal_patterns_text = f"Pola musiman umum. Layanan utama: {partner.layanan_unggulan_json}."
            
            # Data eksternal akan diambil/disimulasikan oleh AI Service (Langchain Tool)
            # Jadi, kita tidak mengirimnya secara eksplisit dari sini.
            # AI Service akan menggunakan kota dari FaskesPartner untuk tool data eksternal.

            payload_for_ai = {
                "faskes_id": faskes_id, # ID Faskes Partner
                "period_start": period["start"].strftime("%Y-%m-%d"),
                "period_end": period["end"].strftime("%Y-%m-%d"),
                "historical_patient_summary": historical_summary_text, # Ringkasan dari DB Faskes Partner
                "seasonal_disease_patterns": seasonal_patterns_text, # Ringkasan dari DB Faskes Partner
                # Tidak perlu lagi mengirim bmkg_weather_forecast, local_events_calendar, mudik_calendar_info
                # karena akan diambil oleh Langchain Tool di ai_service
            }
            
            ai_result = planning_logic.generate_staffing_forecast(payload_for_ai)

            if "error" in ai_result and ai_result["error"]:
                messages.error(request, f"Gagal mendapatkan forecast untuk periode {period['start']} - {period['end']}: {ai_result.get('error', 'Unknown error')}")
                all_sub_forecasts_successful = False
                monthly_forecast_details.append({"period": f"{period['start']} - {period['end']}", "error": ai_result.get('error', 'Kesalahan tidak diketahui')})
                # Lanjutkan ke periode berikutnya, agar sebagian budget masih bisa dihitung
            elif "forecast_result" in ai_result:
                forecast_output = ai_result["forecast_result"]
                log_id = ai_result.get("ai_request_log_id")
                if log_id:
                    forecast_log_ids_for_budget.append(log_id)

                cost_range = forecast_output.get("estimated_cost_range_rp", {})
                current_min_cost = float(cost_range.get("min_cost", 0))
                current_max_cost = float(cost_range.get("max_cost", 0))

                aggregated_min_cost += current_min_cost
                aggregated_max_cost += current_max_cost
                
                monthly_forecast_details.append({
                    "period_label": period["start"].strftime("%B %Y"),
                    "period_start_iso": period["start"].isoformat(),
                    "period_end_iso": period["end"].isoformat(),
                    "log_id": log_id,
                    "predicted_staffing": forecast_output.get("predicted_staffing_demand", {}),
                    "estimated_min_cost": current_min_cost,
                    "estimated_max_cost": current_max_cost,
                    "alerts_recommendations": forecast_output.get("peak_period_alerts_and_recommendations", "")
                })
            else: # Respon tidak dikenali
                all_sub_forecasts_successful = False
                monthly_forecast_details.append({"period": f"{period['start']} - {period['end']}", "error": "Respon AI tidak valid."})


        if all_sub_forecasts_successful:
             messages.success(request, "Perencanaan budget berhasil dihitung berdasarkan forecast otomatis.")
        else:
             messages.warning(request, "Beberapa forecast bulanan gagal, estimasi budget mungkin tidak lengkap atau akurat.")

        # Terapkan penyesuaian biaya jika ada
        adjusted_min_cost = aggregated_min_cost * (1 + cost_adjustment_percentage)
        adjusted_max_cost = aggregated_max_cost * (1 + cost_adjustment_percentage)

        context['budget_summary'] = {
            "budget_period_start": start_period_date.strftime("%d %B %Y"),
            "budget_period_end": end_period_date.strftime("%d %B %Y"),
            "duration_months": number_of_months_to_plan,
            "aggregated_min_cost_raw_rp": aggregated_min_cost,
            "aggregated_max_cost_raw_rp": aggregated_max_cost,
            "cost_adjustment_percentage_input": cost_adjustment_percentage * 100,
            "total_adjusted_min_cost_rp": adjusted_min_cost,
            "total_adjusted_max_cost_rp": adjusted_max_cost,
            "monthly_breakdown": monthly_forecast_details,
            "all_sub_forecasts_successful": all_sub_forecasts_successful,
            "user_notes": budget_notes,
            # "related_ai_log_ids": forecast_log_ids_for_budget # Jika ingin disimpan
        }
        
        # Opsional: Simpan BudgetPlan ke DB
        if BudgetPlan._meta.app_label == 'planning': # Pastikan model BudgetPlan ada di app 'planning'
            try:
                budget_plan_name = f"Rencana Budget {partner.nama_faskes} ({start_period_date.strftime('%b %Y')} - {end_period_date.strftime('%b %Y')})"
                if budget_notes:
                    budget_plan_name += f" - {budget_notes[:30]}" 
                
                BudgetPlan.objects.create(
                    faskes_id_temp=faskes_id,
                    plan_name=budget_plan_name,
                    period_start=start_period_date,
                    period_end=end_period_date,
                    total_estimated_cost_min=adjusted_min_cost,
                    total_estimated_cost_max=adjusted_max_cost,
                    notes=f"Catatan Pengguna: {budget_notes}\nPenyesuaian Biaya: {cost_adjustment_percentage*100}%\n\nDetail Bulanan:\n{json.dumps(monthly_forecast_details, default=str)}",
                    # related_ai_log_ids_json=forecast_log_ids_for_budget
                )
                messages.info(request, "Rencana budget telah disimpan ke sistem.")
            except Exception as e:
                messages.error(request, f"Gagal menyimpan rencana budget ke database: {e}")

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

# @login_required # Sesuaikan dengan autentikasi Faskes/Perencana
def disaster_risk_dashboard_view(request):
    faskes_id = get_current_faskes_id(request) # Untuk konteks Faskes saat ini
    
    data = planning_logic.get_disaster_risk_dashboard_data()
    
    context = {
        'faskes_id': faskes_id, # Untuk base template jika perlu
        'active_disaster_events': data.get("active_disaster_events"),
        'page_title': "Dashboard Penilaian Risiko Bencana"
    }
    return render(request, 'disaster_risk_dashboard.html', context)

# @login_required
def disaster_event_detail_for_planning_view(request, event_id):
    faskes_id = get_current_faskes_id(request)
    
    event, error = planning_logic.get_disaster_event_planning_details(event_id)
    if error:
        messages.error(request, error)
        return redirect('planning:disaster_dashboard') # Kembali ke dashboard risiko

    context = {
        'faskes_id': faskes_id,
        'event': event,
        'page_title': f"Detail Risiko: {event.disaster_type if event else 'Error'}"
    }
    return render(request, 'disaster_event_detail.html', context)

# @login_required
@require_POST # Hanya izinkan trigger via POST
def trigger_disaster_analysis_view(request, event_id):
    faskes_id = get_current_faskes_id(request) # Validasi kepemilikan jika perlu
    
    result = planning_logic.trigger_emergency_event_ai_analysis(event_id)
    
    if result and result.get("success"):
        messages.success(request, result.get("message", "Analisis AI berhasil dijalankan."))
    elif result and result.get("error"):
        messages.error(request, result.get("error", "Gagal menjalankan analisis AI."))
    else:
        messages.warning(request, "Hasil analisis AI tidak diketahui.")
        
    return redirect('planning:disaster_event_detail', event_id=event_id)