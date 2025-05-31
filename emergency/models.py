import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from authentication.models import Faskes
from lentera import settings

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

class TaskCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Contoh: Logistik, Administrasi, Transportasi, Dapur Umum")
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Kategori Tugas Relawan"
        verbose_name_plural = "Kategori Tugas Relawan"
        ordering = ['name']

class VolunteerProfile(models.Model):
    # Pilihan 1: Relawan adalah User Django (jika mereka perlu login)
    # user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="volunteer_profile")
    
    # Pilihan 2: Relawan mendaftar dengan email (tanpa login Django, lebih sederhana untuk awal)
    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True, help_text="Email ini akan digunakan untuk komunikasi.")
    phone_number = models.CharField(max_length=20, help_text="Nomor HP/WA aktif.")
    address = models.TextField(blank=True, null=True, help_text="Alamat domisili saat ini.")
    
    # Basic screening
    id_number = models.CharField(max_length=50, help_text="Nomor KTP/SIM/Identitas Lain (untuk verifikasi).", blank=True, null=True)
    # id_document_scan = models.FileField(upload_to='volunteer_ids/', blank=True, null=True, help_text="Opsional: Upload scan KTP/SIM untuk verifikasi lebih lanjut.") # Jika ada fitur upload
    emergency_contact_name = models.CharField(max_length=100, help_text="Nama kontak darurat.")
    emergency_contact_phone = models.CharField(max_length=20, help_text="Nomor telepon kontak darurat.")
    
    # Simple training
    has_completed_basic_training = models.BooleanField(
        default=False, 
        help_text="Konfirmasi telah membaca/menyelesaikan modul training dasar respons bencana (online 30 menit)."
    )
    skills_description = models.TextField(blank=True, null=True, help_text="Keahlian relevan (mis: menyetir, P3K dasar, memasak, entri data).")
    
    is_profile_verified_by_admin = models.BooleanField(default=False, help_text="Apakah profil relawan sudah diverifikasi oleh admin?")
    admin_verification_notes = models.TextField(blank=True, null=True, help_text="Catatan internal admin terkait verifikasi profil.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name # or self.user.get_full_name() if self.user else self.email

    class Meta:
        verbose_name = "Profil Relawan"
        verbose_name_plural = "Profil Relawan"
        ordering = ['full_name']

class VolunteerApplication(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Menunggu Review'),
        ('APPROVED', 'Disetujui'), # Siap untuk dihubungi/ditempatkan
        ('REJECTED', 'Ditolak'),
        ('DEPLOYED', 'Sedang Bertugas'), # Sudah ditempatkan
        ('COMPLETED', 'Selesai Bertugas'),
        ('CANCELLED', 'Dibatalkan oleh Relawan'),
    ]

    emergency_event = models.ForeignKey(EmergencyEvent, on_delete=models.CASCADE, related_name='volunteer_applications')
    volunteer_profile = models.ForeignKey(VolunteerProfile, on_delete=models.CASCADE, related_name='applications')
    
    # Relawan memilih satu atau lebih kategori tugas yang diminati
    task_categories_preference = models.ManyToManyField(
        TaskCategory, 
        blank=True, 
        help_text="Pilih satu atau lebih kategori tugas yang diminati."
    )
    
    # Relawan bisa mengisi ketersediaan mereka
    availability_notes = models.TextField(
        blank=True, null=True, 
        help_text="Contoh: Tersedia penuh mulai besok, atau hanya akhir pekan, atau setiap hari setelah jam 5 sore."
    )

    application_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Untuk admin setelah approval/deployment
    assigned_task_detail = models.TextField(blank=True, null=True, help_text="Detail tugas spesifik yang diberikan oleh admin.")
    assigned_location_detail = models.CharField(max_length=255, blank=True, null=True, help_text="Detail lokasi penugasan spesifik (jika berbeda dari lokasi umum event).")
    deployment_start_time = models.DateTimeField(null=True, blank=True)
    deployment_end_time = models.DateTimeField(null=True, blank=True)
    
    admin_application_notes = models.TextField(blank=True, null=True, help_text="Catatan dari admin terkait aplikasi/penugasan ini.")

    def __str__(self):
        return f"Aplikasi {self.volunteer_profile.full_name} untuk {self.emergency_event.disaster_type}"

    class Meta:
        # Relawan hanya bisa apply sekali per event untuk menjaga integritas data
        unique_together = ('emergency_event', 'volunteer_profile') 
        ordering = ['-application_date']
        verbose_name = "Aplikasi Relawan"
        verbose_name_plural = "Aplikasi Relawan"

class EmergencyFundRequest(models.Model):
    REQUEST_STATUS_CHOICES = [
        ('PENDING', 'Menunggu Persetujuan'),
        ('APPROVED', 'Disetujui'),
        ('REJECTED', 'Ditolak'),
        ('DISBURSED', 'Telah Dicairkan'),
        ('REPORTED', 'Laporan Diterima'),
    ]

    # Pre-approved emergency fund levels
    FUND_AMOUNT_CHOICES = [
        (10000000, 'Rp 10.000.000'),
        (25000000, 'Rp 25.000.000'),
        (50000000, 'Rp 50.000.000'),
        # Tambahkan level lain jika perlu
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    emergency_event = models.ForeignKey(
        EmergencyEvent, 
        on_delete=models.CASCADE, 
        related_name='fund_requests',
        help_text="Kejadian darurat terkait permintaan dana ini."
    )
    faskes = models.ForeignKey(
        Faskes, 
        on_delete=models.CASCADE, 
        related_name='fund_requests',
        help_text="Fasilitas Kesehatan yang mengajukan dana."
    )
    requested_amount = models.PositiveIntegerField(
        choices=FUND_AMOUNT_CHOICES,
        help_text="Jumlah dana darurat yang diajukan (sesuai level yang disetujui)."
    )
    purpose_description = models.TextField(
        help_text="Deskripsi singkat tujuan penggunaan dana (mis: pembelian obat darurat, operasional ambulans, APD tambahan)."
    )
    
    request_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=REQUEST_STATUS_CHOICES, default='PENDING')

    # Admin Approval
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='approved_fund_requests',
        help_text="Admin yang menyetujui permintaan."
    )
    approval_date = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, null=True, help_text="Catatan dari admin terkait persetujuan/penolakan.")

    # Disbursement
    disbursement_date = models.DateTimeField(null=True, blank=True)
    disbursement_proof = models.FileField(
        upload_to='disbursement_proofs/', 
        blank=True, null=True, 
        help_text="Opsional: Bukti transfer atau pencairan dana."
    ) # Perlu konfigurasi MEDIA_ROOT dan MEDIA_URL

    # Reporting
    spending_report_file = models.FileField(
        upload_to='spending_reports/', 
        blank=True, null=True, 
        help_text="File laporan penggunaan dana (PDF, Excel, dll.)."
    )
    report_submission_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Permintaan Dana Rp {self.get_requested_amount_display()} oleh {self.faskes.nama_faskes} untuk {self.emergency_event.disaster_type}"

    class Meta:
        ordering = ['-request_date']
        verbose_name = "Permintaan Dana Darurat"
        verbose_name_plural = "Permintaan Dana Darurat"