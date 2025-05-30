from django.urls import path
from .views import *

app_name = 'authentication'

urlpatterns = [
    path('', show_test, name='show_test'),
]