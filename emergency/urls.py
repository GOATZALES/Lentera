from django.urls import path
from .views import *

app_name = 'emergency'

urlpatterns = [
    path('activate/', emergency_activation_dashboard, name='activate_emergency'),
    path('deactivate/<int:event_id>/', deactivate_emergency_event, name='deactivate_emergency'),
    # Tambahkan URL lain untuk subfitur Disaster Response Module di sini
]