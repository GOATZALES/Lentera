# planning/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone

class BudgetPlan(models.Model):
    # faskes = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'user_type': 'FASKES'})
    faskes_id_temp = models.CharField(max_length=100, help_text="ID Faskes (gantilah dengan FK ke model Faskes Anda)")
    plan_name = models.CharField(max_length=255)
    period_start = models.DateField()
    period_end = models.DateField()
    total_estimated_cost_min = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    total_estimated_cost_max = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    # Simpan referensi ke log AI yang digunakan untuk membuat budget ini jika perlu
    # related_ai_log_ids_json = models.JSONField(null=True, blank=True, help_text="List of AiForecastRequestLog IDs used")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Budget Plan: {self.plan_name} for Faskes {self.faskes_id_temp}"

    class Meta:
        ordering = ['-created_at']