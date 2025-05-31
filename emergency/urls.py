from django.urls import path
from .views import *

app_name = 'emergency'

urlpatterns = [
    path('activate/', emergency_activation_dashboard, name='activate_emergency'),
    path('deactivate/<int:event_id>/', deactivate_emergency_event, name='deactivate_emergency'),
    path('acceleration/', list_events_for_acceleration, name='list_events_for_acceleration'),
    path('acceleration/configure/<int:event_id>/', configure_matching_acceleration, name='configure_matching_acceleration'),
    # Publik (Relawan)
    path('volunteer/register/', volunteer_registration, name='volunteer_registration'),
    path('volunteer/events/', volunteer_event_list, name='volunteer_event_list'),
    path('volunteer/apply/<int:event_id>/', volunteer_apply_to_event, name='volunteer_apply_to_event'),
    
    # Admin
    path('admin/event/<int:event_id>/volunteers/', admin_event_volunteer_dashboard, name='admin_event_volunteer_dashboard'),
    path('admin/volunteer-application/<int:application_id>/manage/', admin_manage_volunteer_application, name='admin_manage_volunteer_application'),
    path('event/<int:event_id>/resource-tracking/', resource_tracking_dashboard, name='resource_tracking_dashboard'),
    path('fund-request/new/', request_emergency_fund, name='request_fund'),
    path('fund-request/list/', list_fund_requests, name='list_fund_requests'),
    path('fund-request/manage/<uuid:request_id>/', manage_fund_request, name='manage_fund_request'), 
]