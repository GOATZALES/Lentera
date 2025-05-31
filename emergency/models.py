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
    # Untuk Geographic targeting: Automatic identification of affected regions
    # Ini bisa diisi manual, atau idealnya terhubung dengan sistem GIS atau daftar wilayah administratif
    affected_regions_input = models.TextField(
        help_text="Daftar wilayah terdampak (Kabupaten/Kota), pisahkan dengan koma. Misal: Kab. Cianjur, Kota Palu"
    )
    # Nantinya bisa parse `affected_regions_input` ke model Wilayah terpisah jika diperlukan
    # affected_regions = models.ManyToManyField('Region', blank=True) 

    description = models.TextField(blank=True, null=True, help_text="Deskripsi tambahan mengenai situasi darurat")
    
    is_active = models.BooleanField(default=False) # Diubah jadi True saat aktivasi
    activation_time = models.DateTimeField(null=True, blank=True)
    deactivation_time = models.DateTimeField(null=True, blank=True)

    # Untuk Emergency Activation System
    triggered_by_api = models.BooleanField(default=False, help_text="Apakah dipicu otomatis oleh API BNPB/BPBD?")
    api_alert_details = models.JSONField(null=True, blank=True, help_text="Detail alert dari API jika ada")
    
    manually_triggered_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='triggered_emergencies',
        help_text="Admin yang memicu secara manual"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_severity_level_display()}: {self.disaster_type} di {self.location_description}"

    def activate(self, user=None, by_api=False, api_details=None):
        self.is_active = True
        self.activation_time = timezone.now()
        self.triggered_by_api = by_api
        if user:
            self.manually_triggered_by = user
        if api_details:
            self.api_alert_details = api_details
        self.save()
        # Tambahkan logika notifikasi atau pemicu lain di sini

    def deactivate(self):
        self.is_active = False
        self.deactivation_time = timezone.now()
        self.save()
        # Tambahkan logika notifikasi atau pemicu lain di sini

    class Meta:
        ordering = ['-activation_time']
        verbose_name = "Kejadian Darurat"
        verbose_name_plural = "Kejadian Darurat"

# Anda bisa menambahkan model Region jika ingin pemetaan geografis yang lebih detail
# class Region(models.Model):
#     name = models.CharField(max_length=100, unique=True) # Nama Kabupaten/Kota
#     province = models.CharField(max_length=100)
#     # Tambahkan field lain seperti kode wilayah, dll.
#     def __str__(self):
#         return self.name