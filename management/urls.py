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
    # path('departemen/nakes-database/', faskes_views.nakes_database, name='nakes_database'),
    
    # AJAX/API URLs untuk Departemen
    # path('process-application/<int:application_id>/', faskes_views.process_application, name='process_application'),
    # path('api/shift-stats/', faskes_views.shift_statistics_api, name='shift_stats_api'),
    # path('api/nakes-search/', faskes_views.nakes_search_api, name='nakes_search_api'),
    # path('api/export-laporan/', faskes_views.export_laporan, name='export_laporan'),
    
    # Shift Management URLs
    path('shift/create/', faskes_views.create_shift, name='create_shift'),
    # path('shift/<int:shift_id>/edit/', faskes_views.edit_shift, name='edit_shift'),
    # path('shift/<int:shift_id>/delete/', faskes_views.delete_shift, name='delete_shift'),
    # path('shift/<int:shift_id>/cancel/', faskes_views.cancel_shift, name='cancel_shift'),
    
    # # Application Management URLs  
    # path('application/<int:application_id>/detail/', faskes_views.application_detail, name='application_detail'),
    # path('applications/bulk-action/', faskes_views.bulk_application_action, name='bulk_application_action'),
    
    # # Reporting URLs
    # path('reports/performance/', faskes_views.performance_report, name='performance_report'),
    # path('reports/attendance/', faskes_views.attendance_report, name='attendance_report'),
    # path('reports/export/', faskes_views.export_reports, name='export_reports'),

    path('upload/', management_ai_services.upload_certificate_form, name='upload_form'),
    path('process/', management_ai_services.process_certificate_image, name='process_image'),
    path('categories/', management_ai_services.get_categories, name='get_categories'),
    path('results/', management_ai_services.certificate_results, name='results'),
]