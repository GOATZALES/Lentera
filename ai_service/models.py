# ai_services/models.py
from django.db import models
from django.utils import timezone

class AiForecastRequestLog(models.Model): # Ganti nama dari ForecastData agar lebih generik
    """Mencatat setiap permintaan forecast ke layanan AI dan inputnya."""
    # faskes_id_temp akan diisi oleh service yang memanggil, bukan tanggung jawab ai_services utk tahu ttg Faskes
    caller_reference_id = models.CharField(max_length=255, db_index=True, help_text="ID referensi dari sistem pemanggil (misal, Faskes ID)")
    service_type = models.CharField(max_length=100, default="staffing_demand_forecast") # Bisa 'risk_assessment', dll.

    # Input data yang dikirim ke AI (disimpan untuk audit dan re-evaluasi)
    input_payload_json = models.JSONField(help_text="Payload JSON lengkap yang dikirimkan untuk AI")
    
    # Output mentah dari AI
    raw_ai_response_text = models.TextField(null=True, blank=True)
    parsed_ai_output_json = models.JSONField(null=True, blank=True, help_text="Output AI yang sudah diparsing ke JSON terstruktur")
    
    ai_model_name_used = models.CharField(max_length=100, blank=True, null=True)
    processing_status = models.CharField(max_length=20, default="completed", choices=[("pending", "Pending"), ("processing", "Processing"), ("completed", "Completed"), ("failed", "Failed")])
    error_message = models.TextField(null=True, blank=True)
    
    requested_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-requested_at']
        verbose_name = "AI Service Request Log"
        verbose_name_plural = "AI Service Request Logs"

    def __str__(self):
        return f"{self.service_type} for {self.caller_reference_id} at {self.requested_at.strftime('%Y-%m-%d %H:%M')}"

class AiModelPerformanceFeedback(models.Model): # Ganti nama dari ModelPerformanceLog
    """Mencatat feedback dan data aktual untuk mengevaluasi performa model AI."""
    ai_request_log = models.OneToOneField(AiForecastRequestLog, on_delete=models.CASCADE, related_name="performance_feedback")
    
    # Data aktual yang diinput oleh sistem pemanggil (misal, Faskes Dashboard)
    actual_data_json = models.JSONField(help_text="Data aktual yang relevan dengan prediksi (misal, realisasi staf)")
    
    # Metrik akurasi yang dihitung oleh ai_services
    accuracy_metrics_json = models.JSONField(null=True, blank=True, help_text="Skor akurasi detail yang dihitung")
    overall_accuracy_score = models.FloatField(null=True, blank=True)
    
    qualitative_feedback = models.TextField(null=True, blank=True, help_text="Feedback kualitatif dari pengguna atau sistem pemanggil")
    
    feedback_provided_at = models.DateTimeField(default=timezone.now)
    accuracy_calculated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-feedback_provided_at']
        verbose_name = "AI Model Performance Feedback"
        verbose_name_plural = "AI Model Performance Feedbacks"

    def __str__(self):
        return f"Feedback for AI Request ID {self.ai_request_log.id}"

# Tambahkan model untuk RegionalRiskAssessment jika AI terlibat langsung dalam scoringnya
# Jika risk scoring lebih rule-based atau dari API eksternal, mungkin tidak perlu model di sini.
# Misal, jika AI hanya menganalisis teks dari BNPB:
class RegionalRiskAnalysisResult(models.Model):
    """Menyimpan hasil analisis AI terhadap data risiko regional."""
    caller_reference_id = models.CharField(max_length=255, db_index=True, help_text="ID Region atau referensi geografis")
    input_data_summary_text = models.TextField(help_text="Teks ringkasan data (misal dari BNPB) yang dianalisis AI")
    
    # Output dari AI
    risk_level_predicted = models.CharField(max_length=50, null=True, blank=True) # Low, Medium, High
    risk_justification_text = models.TextField(null=True, blank=True)
    potential_hazards_json = models.JSONField(null=True, blank=True) # ["Banjir", "Longsor"]
    
    raw_ai_response_text = models.TextField(null=True, blank=True)
    ai_model_name_used = models.CharField(max_length=100, blank=True, null=True)
    
    analyzed_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Risk Analysis for {self.caller_reference_id} at {self.analyzed_at.strftime('%Y-%m-%d %H:%M')}"

# JALANKAN MIGRATIONS