# ai_services/urls.py
from django.urls import path
from . import views

app_name = 'ai_services'

urlpatterns = [
    # Endpoint untuk layanan peramalan staf
    path('invoke/staffing-forecast/', views.api_invoke_staffing_forecast_service, name='invoke_staffing_forecast'),
    path('submit/forecast-feedback/', views.api_submit_forecast_feedback_service, name='submit_forecast_feedback'),
    
    # Endpoint untuk layanan penilaian risiko regional
    path('invoke/regional-risk-assessment/', views.api_invoke_regional_risk_assessment_service, name='invoke_regional_risk_assessment'),
    
    # Anda bisa menambahkan endpoint GET untuk mengambil log jika diperlukan oleh sistem lain
    # path('logs/forecast/<int:log_id>/', views.api_get_forecast_log_detail, name='get_forecast_log_detail'),
]