from datetime import timedelta
import logging
from django.utils import timezone

# Impor dari ai_services
from ai_service.risk_assesment_services import input_preprocessor as ras_input_ai
from ai_service.risk_assesment_services import core_risk_assessor as ras_core_ai
from ai_service.models import RegionalRiskAnalysisResult # Untuk logging jika dipanggil langsung

def generate_forecast(payload_emergency_forecast):
    from planning.logic import generate_staffing_forecast
    return generate_staffing_forecast(payload_emergency_forecast)

# Impor model emergency Anda
from .models import EmergencyEvent
# Impor model FaskesPartner Anda
from authentication.models import Faskes as FaskesPartner # Sesuaikan

logger = logging.getLogger(__name__)

def get_ai_regional_risk_assessment(region_name: str, bnpb_data_summary: str, ai_model_name: str = "gemini-1.5-flash-latest"):
    """
    Memanggil AI service untuk mendapatkan penilaian risiko regional.
    """
    payload = {
        "region_identifier": region_name,
        "bnpb_data_summary": bnpb_data_summary
        # "ai_model_name" bisa ditambahkan jika diperlukan
    }
    prepared_input, err = ras_input_ai.validate_and_prepare_risk_assessment_input(payload)
    if err:
        logger.error(f"Validasi input gagal untuk risk assessment {region_name}: {err}")
        return None, err, None
    
    # Panggil core risk assessor
    assessment_json, error_msg, analysis_log_id = ras_core_ai.assess_regional_disaster_risk(
        caller_ref_id=region_name,
        input_data=prepared_input,
        input_payload_for_log=payload, # Simpan payload asli
        ai_model_name=ai_model_name
    )
    
    if error_msg:
        logger.error(f"AI risk assessment error untuk {region_name}: {error_msg}")
        return None, error_msg, analysis_log_id
    
    return assessment_json, None, analysis_log_id

def generate_pre_positioning_alert_and_staff_recommendation(event: EmergencyEvent):
    """
    Menganalisis risiko, membuat alert pre-positioning, dan merekomendasikan staf.
    Ini adalah fungsi yang lebih kompleks.
    """
    if not event.is_active:
        return {"error": "Kejadian darurat tidak aktif."}

    all_region_assessments = []
    pre_positioning_alerts = []
    overall_staff_recommendation = {} # Agregat atau per region

    # 1. Dapatkan Risk Scoring untuk setiap affected region
    # Asumsi affected_regions_input adalah string dipisah koma
    affected_regions = [region.strip() for region in event.affected_regions_input.split(',') if region.strip()]
    
    # Untuk demo, summary BNPB bisa dummy atau diambil dari deskripsi event
    bnpb_summary_dummy = f"Laporan awal untuk {event.disaster_type} di {event.location_description}. {event.description or ''}"

    for region_name in affected_regions:
        assessment, err, _ = get_ai_regional_risk_assessment(region_name, bnpb_summary_dummy)
        if assessment and not err:
            all_region_assessments.append(assessment)
            if assessment.get("overall_risk_level") in ["Tinggi", "Kritis"]:
                pre_positioning_alerts.append(
                    f"RISIKO TINGGI/KRITIS di {region_name} untuk {event.disaster_type}. "
                    f"Potensi bahaya utama: {', '.join(assessment.get('potential_major_hazards', ['N/A']))}. "
                    f"Justifikasi: {assessment.get('risk_justification', 'N/A')}. "
                    "Rekomendasi: Segera siapkan tim respons awal dan sumber daya."
                )
        else:
            pre_positioning_alerts.append(f"Gagal mendapatkan penilaian risiko untuk {region_name}: {err}")
    
    # Simpan hasil risk assessment ke event jika mau
    event.ai_regional_risk_assessment_results_json = all_region_assessments
    # event.save() # Jangan save di sini jika ini dipanggil dalam loop/transaksi lain

    # 2. Generate Staffing Recommendation untuk area berisiko tinggi
    # Ini bisa memanggil AI forecast dengan konteks darurat
    # Kita perlu mencari Faskes Partner di wilayah terdampak
    high_risk_regions_for_staffing = [
        assess.get("region_analyzed") for assess in all_region_assessments 
        if assess.get("overall_risk_level") in ["Tinggi", "Kritis"]
    ]

    staffing_recommendations_for_alerts = []

    if high_risk_regions_for_staffing:
        # Cari Faskes Partner di region tersebut (perlu matching nama region dengan data Faskes)
        # Ini penyederhanaan, di produksi perlu sistem pemetaan geospasial atau normalisasi nama daerah
        # Untuk demo, kita bisa asumsikan `region_name` cocok dengan `alamat_kota_kabupaten`
        
        target_faskes_partners = FaskesPartner.objects.filter(
            alamat_kota_kabupaten__in=high_risk_regions_for_staffing, 
            is_active_partner=True
        ) # Atau filter berdasarkan koordinat jika ada radius

        if not target_faskes_partners.exists() and high_risk_regions_for_staffing:
             pre_positioning_alerts.append(
                 f"Tidak ditemukan Faskes Partner aktif di wilayah berisiko tinggi ({', '.join(high_risk_regions_for_staffing)}) untuk penempatan staf awal."
             )
        
        for partner in target_faskes_partners:
            # Buat payload forecast dengan konteks darurat
            forecast_start_date = (timezone.now() + timedelta(days=0)).strftime("%Y-%m-%d") # Mulai segera
            forecast_end_date = (timezone.now() + timedelta(days=3)).strftime("%Y-%m-%d") # Untuk 3 hari awal

            historical_summary_emergency = (
                f"SITUASI DARURAT: {event.disaster_type} di {partner.alamat_kota_kabupaten}. "
                f"Data historis reguler Faskes: Kunjungan rata-rata mingguan: {partner.rata_kunjungan_harian_seminggu_json}. "
                f"Layanan utama: {', '.join(partner.layanan_unggulan_json)}. "
                "PERTIMBANGKAN PENINGKATAN KUNJUNGAN SIGNIFIKAN AKIBAT BENCANA."
            )
            seasonal_patterns_emergency = (
                f"Konteks Bencana: {event.description or event.disaster_type}. "
                "Abaikan pola musiman reguler, fokus pada kebutuhan darurat dan potensi lonjakan korban."
            )
            # Data eksternal untuk AI forecast akan diambil oleh tool berdasarkan lokasi partner dan periode
            
            payload_emergency_forecast = {
                "faskes_id": partner.faskes_id_internal,
                "period_start": forecast_start_date,
                "period_end": forecast_end_date,
                "historical_patient_summary": historical_summary_emergency,
                "seasonal_disease_patterns": seasonal_patterns_emergency,
                # Tidak kirim bmkg, event, mudik karena akan diambil tool AI
            }
            
            forecast_result = generate_forecast(payload_emergency_forecast)
            
            if forecast_result and "forecast_result" in forecast_result:
                demand = forecast_result["forecast_result"].get("predicted_staffing_demand", {})
                cost = forecast_result["forecast_result"].get("estimated_cost_range_rp", {})
                alert_rec = forecast_result["forecast_result"].get("peak_period_alerts_and_recommendations", "")
                
                staff_detail_str = ", ".join([f"{role}: {count}" for role, count in demand.items() if count > 0])
                if staff_detail_str:
                    staffing_recommendations_for_alerts.append(
                        f"Untuk Faskes {partner.nama_faskes} ({partner.faskes_id_internal}) di {partner.alamat_kota_kabupaten}: "
                        f"Rekomendasi staf darurat (3 hari): {staff_detail_str}. "
                        f"Estimasi biaya: Rp {cost.get('min_cost',0):,.0f} - {cost.get('max_cost',0):,.0f}. "
                        f"Catatan AI: {alert_rec}"
                    )
                    # Agregasi kebutuhan staf
                    for role, count in demand.items():
                        overall_staff_recommendation[role] = overall_staff_recommendation.get(role, 0) + count
            else:
                 staffing_recommendations_for_alerts.append(
                     f"Gagal membuat rekomendasi staf darurat untuk Faskes {partner.nama_faskes}."
                 )

    # Gabungkan semua alert dan rekomendasi
    combined_pre_positioning_text = "Pre-Positioning Alerts & Rekomendasi Awal:\n"
    if pre_positioning_alerts:
        combined_pre_positioning_text += "\n--- Peringatan Risiko Regional ---\n"
        combined_pre_positioning_text += "\n".join([f"- {alert}" for alert in pre_positioning_alerts])
    
    if staffing_recommendations_for_alerts:
        combined_pre_positioning_text += "\n\n--- Rekomendasi Kebutuhan Staf Darurat (per Faskes Partner Terdampak) ---\n"
        combined_pre_positioning_text += "\n".join([f"- {rec}" for rec in staffing_recommendations_for_alerts])
    
    if overall_staff_recommendation:
        combined_pre_positioning_text += "\n\n--- Total Estimasi Kebutuhan Staf Tambahan (Agregat) ---\n"
        overall_staff_str = ", ".join([f"{role}: {count}" for role, count in overall_staff_recommendation.items() if count > 0])
        combined_pre_positioning_text += f"- {overall_staff_str if overall_staff_str else 'Tidak ada rekomendasi staf spesifik saat ini.'}"
    
    if not pre_positioning_alerts and not staffing_recommendations_for_alerts:
         combined_pre_positioning_text += "\nTidak ada alert risiko tinggi atau rekomendasi staf spesifik yang dihasilkan saat ini berdasarkan data yang tersedia."

    event.ai_pre_positioning_recommendations_text = combined_pre_positioning_text
    event.save(update_fields=['ai_regional_risk_assessment_results_json', 'ai_pre_positioning_recommendations_text'])
    
    return {
        "message": "Analisis risiko dan rekomendasi pre-positioning telah dibuat.",
        "risk_assessments": all_region_assessments,
        "pre_positioning_alerts_text": combined_pre_positioning_text,
        "overall_staff_needs": overall_staff_recommendation
    }

def get_active_emergency_events_with_details():
    """
    Mengembalikan daftar EmergencyEvent aktif dengan detail AI jika sudah ada.
    Digunakan oleh aplikasi planning.
    """
    events = EmergencyEvent.objects.filter(is_active=True).order_by('-activation_time')
    # Anda bisa menambahkan prefetch_related jika perlu data relasi lain
    return events

def get_emergency_event_detail_for_planning(event_id):
    """
    Mengambil detail satu EmergencyEvent, termasuk hasil analisis AI.
    """
    try:
        event = EmergencyEvent.objects.get(id=event_id)
        # Jika hasil AI belum ada dan event aktif, mungkin picu analisis di sini
        # atau biarkan view di planning yang memicunya jika perlu.
        # For simplicity, we assume analysis is run on activation or via a button.
        return event
    except EmergencyEvent.DoesNotExist:
        return None

def trigger_ai_analysis_for_event(event_id):
    """
    Memicu ulang analisis AI untuk event tertentu.
    Mengembalikan hasil analisis atau pesan error.
    """
    event = EmergencyEvent.objects.filter(id=event_id, is_active=True).first()
    if not event:
        return {"error": "Kejadian darurat tidak ditemukan atau tidak aktif."}
    
    try:
        # Panggil fungsi inti yang sudah ada
        analysis_result = generate_pre_positioning_alert_and_staff_recommendation(event)
        if analysis_result and "message" in analysis_result:
            return {
                "success": True, 
                "message": analysis_result["message"], 
                "pre_positioning_alerts_text": analysis_result.get("pre_positioning_alerts_text"),
                "overall_staff_needs": analysis_result.get("overall_staff_needs")
            }
        elif analysis_result and "error" in analysis_result:
             return {"error": f"Gagal membuat analisis AI: {analysis_result['error']}"}
        return {"error": "Hasil analisis AI tidak diketahui."}
    except Exception as e:
        logger.error(f"Kesalahan saat memicu analisis AI untuk event {event_id}: {e}", exc_info=True)
        return {"error": f"Terjadi kesalahan internal: {str(e)}"}