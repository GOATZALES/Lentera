# authentication/views.py - Auto Role Detection Login

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from management.models import Nakes
from .models import Departemen
import json

def login_view(request):
    
    if request.user.is_authenticated:
        return redirect_by_role(request.user)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, 'Mohon masukkan username dan password.')
            return render(request, 'login.html')
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Auto-detect role berdasarkan model yang terkait
            role_info = detect_user_role(user)
            
            if role_info:
                login(request, user)
                messages.success(request, f'Selamat datang, {role_info}!')
                return redirect_by_role(request.user)
            else:
                messages.error(request, 'Akun Anda tidak memiliki role yang valid dalam sistem.')
        else:
            messages.error(request, 'Username atau password salah.')
    
    return render(request, 'login.html')

def detect_user_role(user):
    
    # Check if user is Nakes
    try:
        nakes = Nakes.objects.get(user=user)
        return "nakes"
    except Nakes.DoesNotExist:
        pass
    
    # Check if user is Departemen
    try:
        departemen = Departemen.objects.get(user=user)
        return "departemen"
    
    except Departemen.DoesNotExist:
        pass
    
    raise ValidationError("User Tidak Ditemukan")

def redirect_by_role(user):
    """
    Redirect user berdasarkan role mereka
    """
    role_info = detect_user_role(user)
    
    if role_info == "nakes":
        return redirect("management:nakes_profile")
    elif role_info == "departemen":
        return redirect("management:departemen_dashboard")
    else:
        # User tidak memiliki role valid, logout dan redirect ke login
        logout(user)
        messages.error(user, 'Akun Anda tidak memiliki role yang valid.')
        return redirect('authentication:login')

def logout_view(request):
    """
    Logout dengan pesan personal berdasarkan role
    """
    user_name = None
    if request.user.is_authenticated:
        role_info = detect_user_role(request.user)
        user_name = role_info['name']
    
    logout(request)
    
    if user_name:
        messages.success(request, f'Sampai jumpa, {user_name}!')
    else:
        messages.success(request, 'Anda telah berhasil logout.')
    
    return redirect('authentication:login')


# Decorator untuk role-based access control
def role_required(allowed_roles):
    """
    Decorator untuk membatasi akses berdasarkan role
    
    Usage:
    @role_required(['nakes'])
    def nakes_only_view(request):
        pass
    
    @role_required(['departemen'])
    def departemen_only_view(request):
        pass
    
    @role_required(['nakes', 'departemen'])
    def both_roles_view(request):
        pass
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Anda harus login terlebih dahulu.')
                return redirect('authentication:login')
            
            role_info = detect_user_role(request.user)
            
            if not request.user.departemen or not request.user.nakes:
                messages.error(request, f'Akses ditolak. Halaman ini hanya untuk {", ".join(allowed_roles)}.')
                return redirect_by_role(request.user)
            
            # Add role info to request for easy access in views
            request.user_role_info = role_info
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

# Utility functions untuk views
def get_user_context(request):
    """
    Helper function untuk mendapatkan context user berdasarkan role
    """
    if hasattr(request, 'user_role_info'):
        role_info = request.user_role_info

        if role_info == "nakes":
            nakes = Nakes.objects.get(user=request.user)
            return nakes
        elif role_info == "departemen":
            departemen = Departemen.objects.get(user=request.user)
            return departemen

    else:
        try:
            role_info = detect_user_role(request.user)

            if role_info == "nakes":
                nakes = Nakes.objects.get(user=request.user)
                return nakes
            elif role_info == "departemen":
                departemen = Departemen.objects.get(user=request.user)
                return departemen

        
        except ValidationError:
            raise ValidationError("authentication:login")
    