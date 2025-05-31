from django.urls import path
from . import views  # Import all views from this module
from . import faskes_views
from . import management_ai_services

app_name = "management"

urlpatterns = [
    # Test endpoints (add these first for debugging)
    path('api/test/', views.test_api_connection, name='test_api'),
    path('api/test/departemen/', views.test_departemen_list, name='test_departemen_list'),
    path('api/test/departemen/<uuid:departemen_id>/schedule/', views.test_schedule_simple, name='test_schedule_simple'),
    
    # Nakes Profile & Dashboard URLs
    path('profile/', views.nakes_profile_view, name='nakes_profile'),
    path('cari-tugas/', views.cari_tugas_view, name='cari_tugas'),
    path('histori-kinerja/', views.nakes_histori_kinerja_view, name='histori_kinerja'),
    path('evaluasi/', views.nakes_evaluasi_view, name='evaluasi'),
    
    # API Endpoints for AJAX calls
    path('api/update-availability/', views.update_availability_ajax, name='update_availability_ajax'),
    path('api/departemen/<uuid:departemen_id>/schedule/', views.get_departemen_schedule, name='get_departemen_schedule'),
    path('api/shift/<uuid:shift_id>/accept/', views.accept_shift_ajax, name='accept_shift_ajax'),
    
    # Departemen/Faskes Management URLs
    path('departemen/dashboard/', faskes_views.departemen_dashboard, name='departemen_dashboard'),
    path('departemen/kelola-shift/', faskes_views.kelola_shift, name='kelola_shift'),
    path('departemen/kelola-lamaran/', faskes_views.kelola_lamaran, name='kelola_lamaran'),
    path('departemen/laporan/', faskes_views.laporan_departemen, name='laporan_departemen'),
    path('shift/create/', faskes_views.create_shift, name='create_shift'),
    
    # AI Certificate Management URLs (existing)
    path('upload/', management_ai_services.upload_certificate_form, name='upload_form'),
    path('process/', management_ai_services.process_certificate_image, name='process_image'),
    path('categories/', management_ai_services.get_categories, name='get_categories'),
    path('results/', management_ai_services.certificate_results, name='results'),
]