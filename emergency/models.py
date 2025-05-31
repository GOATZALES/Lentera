from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class EmergencyEvent(models.Model):
    SEVERITY_LEVEL_CHOICES = [
        (1, 'Level 1 (Siaga)'),
        (2, 'Level 2 (Waspada)'),
        (3, 'Level 3 (Awas/Darurat Tinggi)'),
    ]

    disaster_type = models.CharField(max_length=100, help_text="Contoh: Gempa Bumi, Banjir, Wabah Penyakit")
    location_description = models.CharField(max_length=255, help_text="Deskripsi singkat lokasi terdampak utama")
    severity_level = models.IntegerField(choices=SEVERITY_LEVEL_CHOICES, default=1)
    affected_regions_input = models.TextField(
        help_text="Daftar wilayah terdampak (Kabupaten/Kota), pisahkan dengan koma. Misal: Kab. Cianjur, Kota Palu"
    )
    description = models.TextField(blank=True, null=True, help_text="Deskripsi tambahan mengenai situasi darurat")
    
    is_active = models.BooleanField(default=False)
    activation_time = models.DateTimeField(null=True, blank=True)
    deactivation_time = models.DateTimeField(null=True, blank=True)

    triggered_by_api = models.BooleanField(default=False, help_text="Apakah dipicu otomatis oleh API BNPB/BPBD?")
    api_alert_details = models.JSONField(null=True, blank=True, help_text="Detail alert dari API jika ada")
    
    manually_triggered_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='triggered_emergencies',
        help_text="Admin yang memicu secara manual"
    )

    # --- Fields for Emergency Matching Acceleration ---
    matching_acceleration_enabled = models.BooleanField(
        default=False, 
        help_text="Apakah akselerasi pencocokan SDM diaktifkan untuk kejadian ini?"
    )
    expanded_matching_radius_km = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Radius pencocokan yang diperluas dalam KM. Kosongkan jika menggunakan radius standar."
    )
    # Emergency rates & priority queue are implied if matching_acceleration_enabled is True.
    # Rapid deployment target is an operational goal.
    # --------------------------------------------------

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_severity_level_display()}: {self.disaster_type} di {self.location_description}"

    def activate(self, user=None, by_api=False, api_details=None):
        self.is_active = True
        self.activation_time = timezone.now()
        self.triggered_by_api = by_api
        if user and not by_api: # Hanya set jika manual dan user ada
            self.manually_triggered_by = user
        if api_details:
            self.api_alert_details = api_details
        self.save()

    def deactivate(self):
        self.is_active = False
        self.deactivation_time = timezone.now()
        self.save()

    class Meta:
        ordering = ['-activation_time']
        verbose_name = "Kejadian Darurat"
        verbose_name_plural = "Kejadian Darurat"
