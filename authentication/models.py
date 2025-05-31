import uuid
from django.db import models

# Create your models here.
class Faskes(models.Model):
    faskes_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nama_faskes = models.CharField(max_length=255)
    alamat = models.TextField(blank=True, null=True)
    tipe_faskes = models.CharField(max_length=100, blank=True, null=True,
                                   help_text="Contoh: Rumah Sakit, Puskesmas, Klinik")
    nomor_telepon = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    nomor_rekening_operasional = models.CharField(max_length=50, blank=True, null=True, help_text="Nomor rekening untuk pencairan dana darurat.")
    nama_bank_operasional = models.CharField(max_length=100, blank=True, null=True, help_text="Nama bank rekening operasional.")
    atas_nama_rekening_operasional = models.CharField(max_length=150, blank=True, null=True, help_text="Atas nama pada rekening operasional.")

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
  