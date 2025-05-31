# Lentera/billing/urls.py
from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    # Ganti nama URL ini jika perlu, atau buat yang baru
    path('dashboard/', views.faskes_billing_dashboard_view, name='faskes_billing_dashboard'), 
]