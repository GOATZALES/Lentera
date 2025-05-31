from django.contrib import admin
from .models import (
    EmergencyEvent, 
    TaskCategory,       # Tambahkan ini
    VolunteerProfile,   # Tambahkan ini
    VolunteerApplication # Tambahkan ini
)

@admin.register(EmergencyEvent)
class EmergencyEventAdmin(admin.ModelAdmin):
    list_display = (
        'disaster_type', 
        'location_description', 
        'severity_level', 
        'is_active', 
        'activation_time', 
        'manually_triggered_by', 
        'triggered_by_api',
        'matching_acceleration_enabled' # Tambahkan field baru jika ada
    )
    list_filter = ('is_active', 'severity_level', 'triggered_by_api', 'activation_time', 'matching_acceleration_enabled')
    search_fields = ('disaster_type', 'location_description', 'affected_regions_input')
    readonly_fields = ('activation_time', 'deactivation_time', 'created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('disaster_type', 'location_description', 'severity_level', 'affected_regions_input', 'description')
        }),
        ('Status & Aktivasi', {
            'fields': ('is_active', 'activation_time', 'deactivation_time', 'manually_triggered_by', 'triggered_by_api', 'api_alert_details')
        }),
        ('Akselerasi Pencocokan', { # Fieldset baru jika ada
            'fields': ('matching_acceleration_enabled', 'expanded_matching_radius_km'),
            'classes': ('collapse',), # Bisa disembunyikan default
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        current_readonly = list(self.readonly_fields) # Buat salinan agar bisa dimodifikasi
        if obj: 
            current_readonly.extend(['manually_triggered_by', 'triggered_by_api', 'api_alert_details'])
        return tuple(current_readonly)

# --- Daftarkan Model untuk Volunteer Coordination ---

@admin.register(TaskCategory)
class TaskCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(VolunteerProfile)
class VolunteerProfileAdmin(admin.ModelAdmin):
    list_display = (
        'full_name', 
        'email', 
        'phone_number', 
        'has_completed_basic_training', 
        'is_profile_verified_by_admin',
        'created_at'
    )
    list_filter = ('has_completed_basic_training', 'is_profile_verified_by_admin', 'created_at')
    search_fields = ('full_name', 'email', 'phone_number', 'id_number')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Informasi Pribadi', {
            'fields': ('full_name', 'email', 'phone_number', 'address', 'id_number')
        }),
        ('Kontak Darurat & Keahlian', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone', 'skills_description')
        }),
        ('Status & Verifikasi', {
            'fields': ('has_completed_basic_training', 'is_profile_verified_by_admin', 'admin_verification_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    # Jika Anda menggunakan Pilihan 1 (user Django) untuk VolunteerProfile:
    # raw_id_fields = ('user',) 

@admin.register(VolunteerApplication)
class VolunteerApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'volunteer_profile_name', 
        'emergency_event_name', 
        'application_date', 
        'status',
        'assigned_task_short'
    )
    list_filter = ('status', 'application_date', 'emergency_event')
    search_fields = (
        'volunteer_profile__full_name', 
        'volunteer_profile__email', 
        'emergency_event__disaster_type'
    )
    autocomplete_fields = ['emergency_event', 'volunteer_profile'] # Untuk pencarian yang lebih baik
    readonly_fields = ('application_date',)
    
    fieldsets = (
        ('Informasi Aplikasi', {
            'fields': ('emergency_event', 'volunteer_profile', 'application_date', 'status')
        }),
        ('Preferensi & Ketersediaan Relawan', {
            'fields': ('task_categories_preference', 'availability_notes')
        }),
        ('Penugasan & Catatan Admin', {
            'fields': ('assigned_task_detail', 'assigned_location_detail', 'deployment_start_time', 'deployment_end_time', 'admin_application_notes')
        }),
    )
    filter_horizontal = ('task_categories_preference',) # Widget yang lebih baik untuk ManyToManyField

    def volunteer_profile_name(self, obj):
        return obj.volunteer_profile.full_name
    volunteer_profile_name.short_description = 'Nama Relawan'
    volunteer_profile_name.admin_order_field = 'volunteer_profile__full_name' # Untuk sorting

    def emergency_event_name(self, obj):
        return obj.emergency_event.disaster_type
    emergency_event_name.short_description = 'Kejadian Darurat'
    emergency_event_name.admin_order_field = 'emergency_event__disaster_type'

    def assigned_task_short(self, obj):
        if obj.assigned_task_detail:
            return (obj.assigned_task_detail[:75] + '...') if len(obj.assigned_task_detail) > 75 else obj.assigned_task_detail
        return "-"
    assigned_task_short.short_description = 'Detail Tugas (Singkat)'