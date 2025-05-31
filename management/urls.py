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

app_name = "management"

urlpatterns = [
    path('profile/', nakes_profile_view, name='nakes_profile'),
    path('api/update-availability/', update_availability_ajax, name='update_availability_ajax'), 
    path('cari-tugas/', cari_tugas_view, name='cari_tugas'),
    path('api/departemen/<uuid:departemen_id>/schedule/', get_departemen_schedule, name='get_departemen_schedule'),
    path('api/shift/<uuid:shift_id>/accept/', accept_shift_ajax, name='accept_shift_ajax'),
    path('histori-kinerja/', nakes_histori_kinerja_view, name='histori_kinerja'),
    path('evaluasi/', nakes_evaluasi_view, name='evaluasi'),
]