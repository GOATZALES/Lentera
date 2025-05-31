from django.urls import path
from .views import (
    nakes_profile_view,
    update_availability_ajax,
    cari_tugas_view,
    get_departemen_schedule,
    accept_shift_ajax,
    nakes_histori_kinerja_view,
    nakes_evaluasi_view
)

from . import faskes_views

from . import management_ai_services

app_name = "management"

urlpatterns = [
    path('profile/', nakes_profile_view, name='nakes_profile'),
    path('api/update-availability/', update_availability_ajax, name='update_availability_ajax'), 
    path('cari-tugas/', cari_tugas_view, name='cari_tugas'),
    path('api/departemen/<uuid:departemen_id>/schedule/', get_departemen_schedule, name='get_departemen_schedule'),
    path('api/shift/<uuid:shift_id>/accept/', accept_shift_ajax, name='accept_shift_ajax'),
    path('histori-kinerja/', nakes_histori_kinerja_view, name='histori_kinerja'),
    path('evaluasi/', nakes_evaluasi_view, name='evaluasi'),

    path('departemen/dashboard/', faskes_views.departemen_dashboard, name='departemen_dashboard'),
    path('departemen/kelola-shift/', faskes_views.kelola_shift, name='kelola_shift'),
    path('departemen/kelola-lamaran/', faskes_views.kelola_lamaran, name='kelola_lamaran'),
    path('departemen/laporan/', faskes_views.laporan_departemen, name='laporan_departemen'),
    
    path('shift/create/', faskes_views.create_shift, name='create_shift'),
    
    
    path('upload/', management_ai_services.upload_certificate_form, name='upload_form'),
    path('process/', management_ai_services.process_certificate_image, name='process_image'),
    path('categories/', management_ai_services.get_categories, name='get_categories'),
    path('results/', management_ai_services.certificate_results, name='results'),
]