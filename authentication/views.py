# authentication/views.py - Fixed Registration

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from management.choices import KATEGORI_KUALIFIKASI_CHOICES
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError, PermissionDenied
from management.models import Nakes
from .models import Departemen
from .forms import UserRegisterForm, NakesRegistrationForm
import logging

logger = logging.getLogger(__name__)

# Helper to get role type without raising ValidationError for role_required decorator
def get_user_role_type(user):
    """
    Determines the user's role.
    Returns 'nakes', 'departemen', 'superuser', or None.
    """
    # Check for Departemen first as it's the target for planning
    if hasattr(user, 'departemen'): # Accesses the related Departemen object via user.departemen
        return "departemen"
    # Check for Nakes (ensure Nakes model has OneToOneField to User, e.g., user.nakes_profile)
    # For now, using the same logic as detect_user_role but without raising error
    try:
        Nakes.objects.get(user=user) # This confirms Nakes profile exists
        return "nakes"
    except Nakes.DoesNotExist:
        pass
    
    if user.is_superuser:
        return "superuser"
    return None

def login_view(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)
    
    if request.method == 'POST':
        # Handle JSON request for username check if any (from original login.html JS)
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                username_to_check = data.get('username')
                if username_to_check:
                    # This part is just for username existence/role hint, not full auth
                    # It should not actually log in the user or create sessions
                    try:
                        user_exists = User.objects.get(username=username_to_check)
                        roles_info = []
                        # Check Departemen
                        if hasattr(user_exists, 'departemen'):
                            roles_info.append({
                                'name': user_exists.departemen.nama_departemen,
                                'type': 'departemen',
                                'detail': user_exists.departemen.faskes.nama_faskes
                            })
                        # Check Nakes
                        try:
                            nakes_profile = Nakes.objects.get(user=user_exists)
                            roles_info.append({
                                'name': nakes_profile.nama_lengkap, # Assuming Nakes has nama_lengkap
                                'type': 'nakes',
                                'detail': nakes_profile.spesialisasi # Assuming Nakes has spesialisasi
                            })
                        except Nakes.DoesNotExist:
                            pass
                        return JsonResponse({'exists': True, 'roles': roles_info})
                    except User.DoesNotExist:
                        return JsonResponse({'exists': False, 'roles': []})
                return JsonResponse({'error': 'No username provided for check'}, status=400)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)

        # Standard form submission for login
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, 'Mohon masukkan username dan password.')
            return render(request, 'login.html')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            try:
                # detect_user_role will raise ValidationError if no role is found
                role_name_for_message = detect_user_role(user) # For the welcome message
                login(request, user)
                # The success message might be too generic if detect_user_role changes;
                # It might be better to get user's actual name.
                # For Departemen: user.departemen.nama_departemen
                # For Nakes: user.nakes_profile.nama_lengkap (assuming nakes_profile related_name)
                display_name = user.get_full_name() or user.username
                if hasattr(user, 'departemen'):
                    display_name = user.departemen.nama_departemen
                elif hasattr(user, 'nakes_profile'): # Adjust if Nakes model has different access
                     try:
                        nakes = Nakes.objects.get(user=user)
                        display_name = nakes.nama_lengkap # Or similar field
                     except Nakes.DoesNotExist:
                        pass

                messages.success(request, f'Selamat datang, {display_name}!')
                return redirect_by_role(user) # Pass user object to redirect_by_role
            except ValidationError as e:
                 messages.error(request, str(e)) # Show "User Tidak Ditemukan" or similar
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
    
    if role_type == "nakes":
        return redirect("management:nakes_dashboard") # Example: nakes_dashboard
    elif role_type == "departemen":
        return redirect("planning:dashboard") # Redirect Departemen to planning dashboard
    elif role_type == "superuser":
        # Superusers might go to admin or a specific superuser dashboard
        return redirect("/admin/") # Or a custom superuser dashboard
    else:
        # User has no valid role, logout and redirect to login with error
        logout(user) # Pass the request object if logout requires it, or just user if settings allow
        # Since this function is called with 'user' object, standard logout is request.user
        # This path implies an issue, so a generic error is fine.
        # messages.error(request, 'Akun Anda tidak memiliki peran yang valid.') # 'request' is not available here.
        # This function should ideally be called from a view context where `request` is available
        # For now, assume it redirects to login and login view shows message.
        return redirect('authentication:login')


def logout_view(request):
    """
    Logout dengan pesan personal berdasarkan role
    """
    user_name = None
    if request.user.is_authenticated:
        role_info = detect_user_role(request.user)
        user_name = role_info['name']
    
    logout(request) # Correct: logout takes request object
    
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
    