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