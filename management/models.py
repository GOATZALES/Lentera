import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .choices import * 

# Create your models here.

class Nakes(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)

    nama_lengkap = models.CharField(max_length=255)
    nomor_telepon = models.CharField(max_length=20, blank=True, null=True)
    alamat = models.TextField(blank=True, null=True)
    tanggal_lahir = models.DateField(blank=True, null=True)
    
    jenis_kelamin = models.CharField(max_length=1, choices=JENIS_KELAMIN_CHOICES, blank=True, null=True)
    profesi = models.CharField(max_length=50, choices=PROFESI_CHOICES)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    nomor_registrasi = models.CharField(max_length=100, unique=True, help_text="Contoh: STR, SIP, dll.")
    tahun_pengalaman = models.IntegerField(default=0)
    
    # Primary qualification - the main one used for shift matching
    kategori_kualifikasi = models.CharField(max_length=50, choices=KATEGORI_KUALIFIKASI_CHOICES)
    
    # Additional skills - stored as JSON field or separate model
    # For simplicity, we'll use a separate model for skills
    
    # Field unik: log untuk menghitung dia bersedia bekerja 50 menit * x (log)
    log_ketersediaan_menit = models.IntegerField(default=0, help_text="Total menit yang diindikasikan Nakes bersedia bekerja. Perlu reset periodik.")
    
    tanggal_daftar = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Nakes"
        verbose_name_plural = "Nakes"
        ordering = ['nama_lengkap'] 

    def __str__(self):
        return f"{self.nama_lengkap} ({self.profesi})"

    def clean(self):
        if self.tahun_pengalaman < 0:
            raise ValidationError('Tahun pengalaman tidak boleh negatif')
        
        if self.log_ketersediaan_menit < 0:
            raise ValidationError('Log ketersediaan tidak boleh negatif')

    @property
    def log_count(self):
        """Mengembalikan jumlah log berdasarkan menit ketersediaan"""
        return self.log_ketersediaan_menit // 50

    @property
    def all_skills(self):
        """Mengembalikan semua skill yang dimiliki nakes"""
        skills = list(self.skills.values_list('skill_name', flat=True))
        # Include primary qualification if not already in skills
        if self.kategori_kualifikasi not in skills:
            skills.append(self.kategori_kualifikasi)
        return skills

    @property
    def skill_categories(self):
        """Mengembalikan skills yang dikelompokkan berdasarkan kategori"""
        skills = self.skills.all()
        categories = {
            'profesi_umum': [],
            'spesialisasi': [],
            'sertifikasi': []
        }
        
        for skill in skills:
            if skill.category:
                categories.setdefault(skill.category, []).append(skill.skill_name)
            else:
                # Auto-categorize based on skill name
                skill_name = skill.skill_name.lower()
                if 'spesialis' in skill_name:
                    categories['spesialisasi'].append(skill.skill_name)
                elif any(cert in skill_name for cert in ['bls', 'acls', 'btls', 'atls', 'sertifikasi', 'pelatihan']):
                    categories['sertifikasi'].append(skill.skill_name)
                else:
                    categories['profesi_umum'].append(skill.skill_name)
        
        return categories

    # Metode untuk menambahkan menit ketersediaan
    def add_ketersediaan_menit(self, menit):
        if menit > 0:
            self.log_ketersediaan_menit += menit
            self.save()

    # Metode untuk mengurangi menit ketersediaan
    def reduce_ketersediaan_menit(self, menit):
        if menit > 0:
            self.log_ketersediaan_menit = max(0, self.log_ketersediaan_menit - menit)
            self.save()

    def set_log_count(self, log_count):
        """Set ketersediaan berdasarkan jumlah log"""
        self.log_ketersediaan_menit = log_count * 50
        self.save()

    def add_skill(self, skill_name, category=None):
        """Menambahkan skill baru"""
        skill, created = NakesSkill.objects.get_or_create(
            nakes=self,
            skill_name=skill_name,
            defaults={'category': category}
        )
        return skill

    def remove_skill(self, skill_name):
        """Menghapus skill"""
        self.skills.filter(skill_name=skill_name).delete()

    def has_skill(self, skill_name):
        """Cek apakah memiliki skill tertentu"""
        return (self.kategori_kualifikasi == skill_name or 
                self.skills.filter(skill_name=skill_name).exists())


class NakesSkill(models.Model):
    """Model untuk menyimpan additional skills yang dimiliki nakes"""
    
    SKILL_CATEGORIES = [
        ('profesi_umum', 'Profesi Umum'),
        ('spesialisasi', 'Spesialisasi'),
        ('sertifikasi', 'Sertifikasi & Pelatihan'),
        ('manajemen', 'Manajemen & Administrasi'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nakes = models.ForeignKey(Nakes, on_delete=models.CASCADE, related_name='skills')
    skill_name = models.CharField(max_length=100, choices=KATEGORI_KUALIFIKASI_CHOICES)
    category = models.CharField(max_length=20, choices=SKILL_CATEGORIES, blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False, help_text="Apakah skill ini sudah diverifikasi")
    
    class Meta:
        unique_together = ('nakes', 'skill_name')
        ordering = ['category', 'skill_name']
        verbose_name = "Nakes Skill"
        verbose_name_plural = "Nakes Skills"

    def __str__(self):
        return f"{self.nakes.nama_lengkap} - {self.skill_name}"

    def save(self, *args, **kwargs):
        # Auto-categorize if category is not set
        if not self.category:
            self.category = self.auto_categorize()
        super().save(*args, **kwargs)

    def auto_categorize(self):
        """Auto-categorize skill based on skill name"""
        skill_name = self.skill_name.lower()
        
        if 'spesialis' in skill_name:
            return 'spesialisasi'
        elif any(cert in skill_name for cert in ['bls', 'acls', 'btls', 'atls', 'sertifikasi', 'pelatihan']):
            return 'sertifikasi'
        elif any(mgmt in skill_name for mgmt in ['manajemen', 'quality', 'edukator']):
            return 'manajemen'
        else:
            return 'profesi_umum'


class Faskes(models.Model):
    faskes_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nama_faskes = models.CharField(max_length=255)
    alamat = models.TextField(blank=True, null=True)
    tipe_faskes = models.CharField(max_length=100, blank=True, null=True,
                                   help_text="Contoh: Rumah Sakit, Puskesmas, Klinik")
    nomor_telepon = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    # Mungkin ada user yang mengelola Faskes (misal: admin Faskes)
    # admin_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_faskes')

    def __str__(self):
        return self.nama_faskes
    

class Departemen(models.Model):
    departemen_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    faskes = models.ForeignKey(Faskes, on_delete=models.CASCADE, related_name='departemen')
    nama_departemen = models.CharField(max_length=255)
    jam_buka = models.TimeField(blank=True, null=True)
    jam_tutup = models.TimeField(blank=True, null=True)
    
    

    def __str__(self):
        return f"{self.nama_departemen} ({self.faskes.nama_faskes})"
  
    
class Shift(models.Model):
    shift_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    departemen = models.ForeignKey(Departemen, on_delete=models.CASCADE, related_name='shifts')
    
    # Kebutuhan SDM
    profesi = models.CharField(max_length=50, choices=PROFESI_CHOICES)

    kategori_kualifikasi = models.CharField(max_length=50, choices=KATEGORI_KUALIFIKASI_CHOICES)

    jumlah_nakes_dibutuhkan = models.IntegerField(default=1)

    # Detail Waktu & Lokasi
    tanggal_shift = models.DateField()
    jam_mulai = models.TimeField()
    jam_selesai = models.TimeField()
    durasi_menit = models.IntegerField(help_text="Durasi shift dalam menit")
    deskripsi_tugas = models.TextField(blank=True, null=True)
    
    # Status Shift
    is_active = models.BooleanField(default=True, help_text="Apakah shift masih dibuka untuk penugasan")
    is_completed_by_faskes = models.BooleanField(default=False, help_text="Apakah Faskes sudah menandai shift selesai")

    @property
    def estimated_worth(self):
        # Contoh perhitungan sederhana: Rp 500 per menit
        # Anda bisa membuat ini lebih kompleks (misal, berdasarkan jenis nakes, jam, dll.)
        return self.durasi_menit * 500

    def __str__(self):
        return f"Shift {self.jenis_nakes_dibutuhkan} di {self.departemen.nama_departemen} pada {self.tanggal_shift} ({self.jam_mulai}-{self.jam_selesai})"

# --- Model ShiftAssignment ---
# Ini menghubungkan Shift dengan Nakes yang ditugaskan
class ShiftAssignment(models.Model):
    assignment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='assignments')
    nakes = models.ForeignKey(Nakes, on_delete=models.CASCADE, related_name='assigned_shifts')
    
    status_assignment = models.CharField(max_length=50, choices=STATUS_ASSIGNMENT_CHOICES, default='Pending')
    
    waktu_penugasan = models.DateTimeField(auto_now_add=True)
    waktu_nakes_menerima = models.DateTimeField(null=True, blank=True)
    waktu_clock_in = models.DateTimeField(null=True, blank=True)
    waktu_clock_out = models.DateTimeField(null=True, blank=True)
    
    # Logika untuk pembayaran
    total_bayaran_nakes = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_paid = models.BooleanField(default=False) # Apakah sudah dibayar

    class Meta:
        unique_together = ('shift', 'nakes') # Satu Nakes hanya bisa ditugaskan ke satu Shift sekali

    def __str__(self):
        return f"Assignment: {self.nakes.nama_lengkap} - {self.shift.jenis_nakes_dibutuhkan} di {self.shift.departemen.nama_departemen} ({self.status_assignment})"

# --- Model ReviewNakes ---
# Untuk Faskes menilai kinerja Nakes setelah shift selesai
class ReviewNakes(models.Model):
    review_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.OneToOneField(ShiftAssignment, on_delete=models.CASCADE, related_name='review_faskes',
                                      help_text="Review terkait dengan satu penugasan shift tertentu")
    faskes = models.ForeignKey(Faskes, on_delete=models.CASCADE, related_name='reviews_given')
    nakes = models.ForeignKey(Nakes, on_delete=models.CASCADE, related_name='reviews_received')
    
    # Penilaian dalam skala (misal 1-5)
    rating_kinerja = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text="Rating kinerja Nakes (skala 1-5)"
    )
    komentar = models.TextField(blank=True, null=True,
                                help_text="Komentar atau catatan mengenai kinerja Nakes")
    tanggal_review = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('assignment', 'faskes') # Faskes hanya bisa review satu assignment sekali

    def __str__(self):
        return f"Review Nakes {self.nakes.nama_lengkap} oleh {self.faskes.nama_faskes} untuk Shift {self.assignment.shift.shift_id}"


