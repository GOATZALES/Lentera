# management/forms.py
from django import forms
from .models import Nakes, ShiftAssignment
from .choices import JENIS_KELAMIN_CHOICES, PROFESI_CHOICES, STATUS_CHOICES, KATEGORI_KUALIFIKASI_CHOICES

class NakesProfileForm(forms.ModelForm):
    # Field user tidak ditampilkan karena primary_key OneToOneField
    # Diasumsikan Nakes sudah ada saat ini (misalnya setelah login)
    
    # Override fields untuk menampilkan choices
    jenis_kelamin = forms.ChoiceField(choices=JENIS_KELAMIN_CHOICES, required=False)
    profesi = forms.ChoiceField(choices=PROFESI_CHOICES)
    status = forms.ChoiceField(choices=STATUS_CHOICES)
    kategori_kualifikasi = forms.ChoiceField(choices=KATEGORI_KUALIFIKASI_CHOICES)

    class Meta:
        model = Nakes
        # Sesuaikan field yang ingin diizinkan untuk diedit oleh Nakes
        fields = [
            'nama_lengkap', 
            'nomor_telepon', 
            'alamat', 
            'tanggal_lahir', 
            'jenis_kelamin', 
            'profesi', 
            'status',
            'nomor_registrasi',
            'tahun_pengalaman',
            'kategori_kualifikasi',
            # 'log_ketersediaan_menit' tidak perlu di sini, ini diupdate otomatis
        ]
        widgets = {
            'tanggal_lahir': forms.DateInput(attrs={'type': 'date'}),
        }

class NakesAvailabilityForm(forms.Form):
    # Form terpisah untuk mengatur ketersediaan menit
    # Ini bisa disesuaikan dengan kebutuhan Anda (misal, input per hari, dll.)
    menit_tersedia_tambahan = forms.IntegerField(
        min_value=0, 
        label="Tambahkan menit ketersediaan (misal: 60 untuk 1 jam)",
        help_text="Ini akan menambah total menit ketersediaan Anda."
    )

class ClockInOutForm(forms.Form):
    # Formulir kosong hanya untuk memicu aksi clock-in/out via POST
    pass