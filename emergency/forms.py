from django import forms
from .models import EmergencyEvent

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