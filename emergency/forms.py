from django import forms
from .models import *

class EmergencyActivationForm(forms.ModelForm):
    class Meta:
        model = EmergencyEvent
        fields = [
            'disaster_type', 
            'location_description', 
            'severity_level', 
            'affected_regions_input', 
            'description'
        ]
        widgets = {
            'disaster_type': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-red-500 focus:border-red-500 sm:text-sm',
                'placeholder': 'Contoh: Gempa Bumi Skala 7.0'
            }),
            'location_description': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-red-500 focus:border-red-500 sm:text-sm',
                'placeholder': 'Contoh: Sekitar Gunung Merapi, Radius 10 KM'
            }),
            'severity_level': forms.Select(attrs={
                'class': 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-red-500 focus:border-red-500 sm:text-sm'
            }),
            'affected_regions_input': forms.Textarea(attrs={
                'class': 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-red-500 focus:border-red-500 sm:text-sm',
                'rows': 2,
                'placeholder': 'Kab. Cianjur, Kota Palu, Kab. Lombok Utara'
            }),
            'description': forms.Textarea(attrs={
                'class': 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-red-500 focus:border-red-500 sm:text-sm',
                'rows': 3,
                'placeholder': 'Detail situasi, kebutuhan mendesak, dll.'
            }),
        }
        labels = {
            'disaster_type': 'Jenis Bencana',
            'location_description': 'Deskripsi Lokasi',
            'severity_level': 'Level Keparahan',
            'affected_regions_input': 'Wilayah Terdampak (pisahkan koma)',
            'description': 'Deskripsi Tambahan',
        }
        
class MatchingAccelerationForm(forms.ModelForm):
    DEFAULT_EMERGENCY_RADIUS = 50 # Contoh radius default dalam km

    expanded_matching_radius_km = forms.IntegerField(
        label="Radius Pencocokan Diperluas (km)",
        required=False, # Tidak wajib jika akselerasi tidak diaktifkan
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': f'Contoh: {DEFAULT_EMERGENCY_RADIUS}'
        })
    )

    class Meta:
        model = EmergencyEvent
        fields = ['matching_acceleration_enabled', 'expanded_matching_radius_km']
        widgets = {
            'matching_acceleration_enabled': forms.CheckboxInput(attrs={
                'class': 'h-5 w-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500'
            }),
        }
        labels = {
            'matching_acceleration_enabled': 'Aktifkan Akselerasi Pencocokan Darurat',
        }

    def clean(self):
        cleaned_data = super().clean()
        acceleration_enabled = cleaned_data.get('matching_acceleration_enabled')
        radius = cleaned_data.get('expanded_matching_radius_km')

        if acceleration_enabled and not radius:
            # Jika akselerasi diaktifkan tapi radius tidak diisi, set default atau beri error
            # cleaned_data['expanded_matching_radius_km'] = self.DEFAULT_EMERGENCY_RADIUS
            # Atau
            self.add_error('expanded_matching_radius_km', 'Radius harus diisi jika akselerasi diaktifkan.')
        elif not acceleration_enabled:
            # Jika akselerasi tidak diaktifkan, radius bisa dikosongkan
            cleaned_data['expanded_matching_radius_km'] = None
            
        return cleaned_data
    
class VolunteerProfileRegistrationForm(forms.ModelForm):
    # Checkbox konfirmasi training, bukan field di model secara langsung
    confirm_basic_training_read = forms.BooleanField(
        label="Saya menyatakan telah membaca dan memahami modul training dasar respons bencana (30 menit) yang disediakan.",
        required=True, # Jadikan wajib
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500'})
    )

    class Meta:
        model = VolunteerProfile
        # 'user' field di-exclude jika tidak pakai login Django untuk relawan
        # 'is_profile_verified_by_admin', 'admin_verification_notes' diisi admin
        fields = [
            'full_name', 'email', 'phone_number', 'address', 
            'id_number', 
            'emergency_contact_name', 'emergency_contact_phone',
            'skills_description',
        ]
        # 'has_completed_basic_training' akan di-set berdasarkan 'confirm_basic_training_read'
        
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nama Lengkap Sesuai KTP'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'contoh@email.com'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '08xxxxxxxxxx'}),
            'address': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Alamat domisili lengkap'}),
            'id_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nomor KTP/SIM (untuk verifikasi)'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nama orang yang bisa dihubungi saat darurat'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nomor telepon kontak darurat'}),
            'skills_description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 2, 'placeholder': 'Contoh: Mengemudi mobil/motor, P3K, memasak, entri data, dll.'}),
        }
        labels = {
            'full_name': 'Nama Lengkap',
            'email': 'Alamat Email Aktif',
            'phone_number': 'Nomor Telepon/WA',
            'address': 'Alamat Domisili',
            'id_number': 'Nomor Identitas (KTP/SIM)',
            'emergency_contact_name': 'Nama Kontak Darurat',
            'emergency_contact_phone': 'Nomor Telepon Kontak Darurat',
            'skills_description': 'Keahlian Relevan yang Dimiliki',
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('confirm_basic_training_read'):
            instance.has_completed_basic_training = True
        if commit:
            instance.save()
        return instance

class VolunteerEventApplicationForm(forms.ModelForm):
    task_categories_preference = forms.ModelMultipleChoiceField(
        queryset=TaskCategory.objects.all().order_by('name'),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'space-y-1'}), # Akan di-style lebih lanjut di template
        label="Minat Kategori Tugas (pilih satu atau lebih)",
        required=True
    )

    class Meta:
        model = VolunteerApplication
        fields = ['task_categories_preference', 'availability_notes']
        widgets = {
            'availability_notes': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Jelaskan ketersediaan waktu Anda. Contoh: "Siap full-time selama 1 minggu ke depan", atau "Hanya bisa di akhir pekan", atau "Setiap hari setelah pukul 17:00".'}),
        }
        labels = {
            'availability_notes': 'Catatan Ketersediaan Waktu',
        }
        # 'emergency_event' dan 'volunteer_profile' akan diisi otomatis di view

# --- Form untuk Admin Mengelola Aplikasi Relawan ---
class VolunteerApplicationManagementForm(forms.ModelForm):
    class Meta:
        model = VolunteerApplication
        fields = [
            'status', 
            'assigned_task_detail',
            'assigned_location_detail', 
            'deployment_start_time', 
            'deployment_end_time', 
            'admin_application_notes'
        ]
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'assigned_task_detail': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 2}),
            'assigned_location_detail': forms.TextInput(attrs={'class': 'form-input'}),
            'deployment_start_time': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'deployment_end_time': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'admin_application_notes': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
        }

# --- Form untuk Admin memverifikasi profil relawan ---
class VolunteerProfileVerificationForm(forms.ModelForm):
    class Meta:
        model = VolunteerProfile
        fields = ['is_profile_verified_by_admin', 'admin_verification_notes']
        widgets = {
            'is_profile_verified_by_admin': forms.CheckboxInput(attrs={'class': 'h-5 w-5 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500'}),
            'admin_verification_notes': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
        }
        labels = {
            'is_profile_verified_by_admin': 'Verifikasi Profil Relawan Ini?',
            'admin_verification_notes': 'Catatan Verifikasi (Internal Admin)',
        }