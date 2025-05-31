# authentication/forms.py - Fixed and Simplified

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from PIL import Image
import io

# Import from management app
from management.models import Nakes
from management.choices import JENIS_KELAMIN_CHOICES, PROFESI_CHOICES, STATUS_CHOICES


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")
    first_name = forms.CharField(max_length=30, required=True, label="Nama Depan")
    last_name = forms.CharField(max_length=30, required=True, label="Nama Belakang")

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        # Override specific styling for password help text
        self.fields['username'].help_text = "Username unik untuk login"
        self.fields['email'].help_text = "Email valid untuk verifikasi akun"

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email sudah terdaftar.")
        return email


class NakesRegistrationForm(forms.ModelForm):
    # Certificate upload field (required but not analyzed for now)
    certificate_image = forms.ImageField(
        required=True,
        label="Upload Sertifikat Medis",
        help_text="Upload sertifikat medis Anda (JPEG, PNG, WebP - Max 10MB)",
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])]
    )
    
    # Choice fields
    jenis_kelamin = forms.ChoiceField(
        choices=JENIS_KELAMIN_CHOICES, 
        required=True,
        label="Jenis Kelamin"
    )
    profesi = forms.ChoiceField(
        choices=PROFESI_CHOICES, 
        required=True,
        label="Profesi"
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES, 
        required=True,
        label="Status"
    )
    
    # Agreement checkbox
    agree_terms = forms.BooleanField(
        required=True,
        label="Saya setuju dengan syarat dan ketentuan",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Nakes
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
            # kategori_kualifikasi will be set automatically
        ]
        widgets = {
            'tanggal_lahir': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
            'nama_lengkap': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Nama lengkap sesuai sertifikat'
            }),
            'nomor_telepon': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '+62 8xx xxxx xxxx'
            }),
            'alamat': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Alamat lengkap'
            }),
            'nomor_registrasi': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Nomor registrasi profesi'
            }),
            'tahun_pengalaman': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 0, 
                'max': 50,
                'placeholder': 'Contoh: 5'
            }),
        }
        labels = {
            'nama_lengkap': 'Nama Lengkap',
            'nomor_telepon': 'Nomor Telepon',
            'alamat': 'Alamat',
            'tanggal_lahir': 'Tanggal Lahir',
            'nomor_registrasi': 'Nomor Registrasi',
            'tahun_pengalaman': 'Tahun Pengalaman',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add CSS classes for choice fields
        self.fields['jenis_kelamin'].widget.attrs.update({'class': 'form-select'})
        self.fields['profesi'].widget.attrs.update({'class': 'form-select'})
        self.fields['status'].widget.attrs.update({'class': 'form-select'})
        
        # Certificate upload field styling
        self.fields['certificate_image'].widget.attrs.update({
            'class': 'form-control',
            'accept': 'image/*',
            'id': 'certificate_image'
        })

    def clean_certificate_image(self):
        """Validate certificate image upload"""
        image = self.cleaned_data.get('certificate_image')
        
        if image:
            # Check file size (10MB max)
            if image.size > 10 * 1024 * 1024:
                raise ValidationError("Ukuran file terlalu besar. Maksimal 10MB.")
            
            # Check if it's a valid image
            try:
                img = Image.open(image)
                img.verify()
                # Reset file pointer after verify
                image.seek(0)
            except Exception:
                raise ValidationError("File yang diupload bukan gambar yang valid.")
                
        return image

    def clean_nomor_telepon(self):
        """Validate phone number format"""
        nomor = self.cleaned_data.get('nomor_telepon')
        if nomor:
            # Remove spaces and special characters for validation
            clean_nomor = ''.join(filter(str.isdigit, nomor))
            if len(clean_nomor) < 10 or len(clean_nomor) > 15:
                raise ValidationError("Nomor telepon harus antara 10-15 digit.")
        return nomor

    def clean_tahun_pengalaman(self):
        """Validate years of experience"""
        tahun = self.cleaned_data.get('tahun_pengalaman')
        if tahun is not None and (tahun < 0 or tahun > 50):
            raise ValidationError("Tahun pengalaman harus antara 0-50 tahun.")
        return tahun

    def clean_nama_lengkap(self):
        """Validate full name"""
        nama = self.cleaned_data.get('nama_lengkap')
        if nama and len(nama.strip()) < 3:
            raise ValidationError("Nama lengkap minimal 3 karakter.")
        return nama

    def clean_nomor_registrasi(self):
        """Validate registration number"""
        nomor = self.cleaned_data.get('nomor_registrasi')
        if nomor and len(nomor.strip()) < 3:
            raise ValidationError("Nomor registrasi minimal 3 karakter.")
        return nomor