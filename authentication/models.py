import uuid
from django.db import models
from django.contrib.auth.models import User

class Faskes(models.Model):
    faskes_id_internal = models.CharField(max_length=50, unique=True, primary_key=True, help_text="ID unik internal Faskes Partner")
    nama_faskes = models.CharField(max_length=255)
    jenis_faskes = models.CharField(max_length=100) # Bisa pakai choices

    # Alamat
    alamat_jalan = models.CharField(max_length=255)
    alamat_kelurahan_desa = models.CharField(max_length=100)
    alamat_kecamatan = models.CharField(max_length=100)
    alamat_kota_kabupaten = models.CharField(max_length=100)
    alamat_provinsi = models.CharField(max_length=100)
    alamat_kode_pos = models.CharField(max_length=10, blank=True)
    
    koordinat_latitude = models.FloatField(null=True, blank=True)
    koordinat_longitude = models.FloatField(null=True, blank=True)
    
    nomor_izin_operasional = models.CharField(max_length=100, blank=True)
    
    # Kontak PIC
    pic_nama = models.CharField(max_length=255, blank=True)
    pic_telepon = models.CharField(max_length=20, blank=True)
    pic_email = models.EmailField(blank=True)
    
    # Jam Operasional
    ops_hari = models.CharField(max_length=100, blank=True) # "Senin - Jumat", "Setiap Hari"
    ops_jam_buka = models.TimeField(null=True, blank=True)
    ops_jam_tutup = models.TimeField(null=True, blank=True)
    ops_catatan = models.TextField(blank=True)
    
    # Kapasitas (bisa JSONField atau field terpisah)
    kapasitas_info_json = models.JSONField(null=True, blank=True, help_text='{"tempat_tidur": 100, "poli_aktif": 5}')
    
    layanan_unggulan_json = models.JSONField(null=True, blank=True, help_text='["UGD", "Poli Anak"]') # List of strings
    
    # Data Historis
    historis_kunjungan_bulanan_json = models.JSONField(null=True, blank=True)
    rata_kunjungan_harian_seminggu_json = models.JSONField(null=True, blank=True)
    pola_kunjungan_layanan_json = models.JSONField(null=True, blank=True)
    periode_puncak_diketahui_json = models.JSONField(null=True, blank=True) # List of strings
    historis_klb_lokal_json = models.JSONField(null=True, blank=True) # List of dicts
    baseline_staffing_json = models.JSONField(null=True, blank=True)
    
    is_active_partner = models.BooleanField(default=True)
    joined_date = models.DateField(auto_now_add=True)
    def __str__(self):
        return self.nama_faskes

class Departemen(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)

    faskes = models.ForeignKey(Faskes, on_delete=models.CASCADE, related_name='departemen')
    nama_departemen = models.CharField(max_length=255)
    jam_buka = models.TimeField(blank=True, null=True)
    jam_tutup = models.TimeField(blank=True, null=True)
    
    
    def __str__(self):
        return f"{self.nama_departemen} ({self.faskes.nama_faskes})"
  