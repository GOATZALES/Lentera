# planning/urls.py
from django.urls import path
from . import views

app_name = 'planning'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('forecast/detail/<int:forecast_log_id>/', views.forecast_detail_view, name='forecast_detail'),
    path('forecast/submit-actual/<int:forecast_log_id>/', views.submit_actual_data_view, name='submit_actual_data'),
    path('budget/', views.budget_planning_view, name='budget_plan'),
    path('export/csv/', views.export_forecast_data_csv, name='export_csv'),
    path('disaster-risk/', views.disaster_risk_dashboard_view, name='disaster_dashboard'),
    path('disaster-risk/event/<int:event_id>/', views.disaster_event_detail_for_planning_view, name='disaster_event_detail'),
    path('disaster-risk/event/<int:event_id>/trigger-analysis/', views.trigger_disaster_analysis_view, name='trigger_disaster_analysis'),
]