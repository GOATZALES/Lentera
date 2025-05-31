import uuid
from django.db import models
from django.contrib.auth.models import User

# Create your models here.
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
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)

    faskes = models.ForeignKey(Faskes, on_delete=models.CASCADE, related_name='departemen')
    nama_departemen = models.CharField(max_length=255)
    jam_buka = models.TimeField(blank=True, null=True)
    jam_tutup = models.TimeField(blank=True, null=True)
    
    

    def __str__(self):
        return f"{self.nama_departemen} ({self.faskes.nama_faskes})"
  