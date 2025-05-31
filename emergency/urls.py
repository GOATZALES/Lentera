from django.urls import path
from .views import *

app_name = 'emergency'

urlpatterns = [
    path('activate/', emergency_activation_dashboard, name='activate_emergency'),
    path('deactivate/<int:event_id>/', deactivate_emergency_event, name='deactivate_emergency'),
    path('acceleration/', list_events_for_acceleration, name='list_events_for_acceleration'),
    path('acceleration/configure/<int:event_id>/', configure_matching_acceleration, name='configure_matching_acceleration'),
]