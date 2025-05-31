# authentication/urls.py

from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Registration URLs
    path('register/', views.register_nakes, name='register'),
    path('registration-success/', views.registration_success, name='registration_success'),
    
    # API endpoints (if needed)
    path('ajax-analyze-certificate/', views.ajax_analyze_certificate, name='ajax_analyze_certificate'),
    path('categories/', views.get_available_categories, name='get_categories'),
]

