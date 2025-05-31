# authentication/views.py - Fixed Registration

from functools import wraps
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from management.choices import KATEGORI_KUALIFIKASI_CHOICES
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from management.models import Nakes
from .models import Departemen
from .forms import UserRegisterForm, NakesRegistrationForm
import logging

logger = logging.getLogger(__name__)

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
    
    return None

def redirect_by_role(user):
    """
    Redirect user based on their role.
    """
    role_type = get_user_role_type(user) # Use the non-exception raising version here
    
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
    """Logout dengan pesan personal berdasarkan role"""
    user_name = None
    if request.user.is_authenticated:
        role_info = detect_user_role(request.user)
        user_name = role_info
    
    logout(request)
    
    if user_name:
        messages.success(request, f'Sampai jumpa, {user_name}!')
    else:
        messages.success(request, 'Anda telah berhasil logout.')
    
    return redirect('authentication:login')

def register_nakes(request):
    """
    Simplified registration view - skip AI for now
    """
    if request.method == 'POST':
        user_form = UserRegisterForm(request.POST)
        nakes_form = NakesRegistrationForm(request.POST, request.FILES)

        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        print("=== FORM VALIDATION DEBUG ===")
        print(f"User form valid: {user_form.is_valid()}")
        print(f"Nakes form valid: {nakes_form.is_valid()}")
        
        if not user_form.is_valid():
            print("User form errors:", user_form.errors)
        if not nakes_form.is_valid():
            print("Nakes form errors:", nakes_form.errors)

        if user_form.is_valid() and nakes_form.is_valid():
            try:
                print("=== SAVING DATA ===")
                
                # Skip AI analysis for now - just save with default category
                default_category = 'Dokter Umum'
                
                with transaction.atomic():
                    # Create user
                    user = user_form.save()
                    print(f"User created: {user.username}")
                    
                    # Create Nakes profile
                    nakes = nakes_form.save(commit=False)
                    nakes.user = user
                    nakes.kategori_kualifikasi = default_category
                    nakes.save()
                    print(f"Nakes created: {nakes.nama_lengkap}")
                    
                    # Store simple result in session
                    request.session['registration_ai_analysis'] = {
                        'category': default_category,
                        'confidence': 'manual',
                        'ai_response': 'Registration completed successfully'
                    }

                success_message = f"Registrasi berhasil! Kategori kualifikasi: {default_category}"
                messages.success(request, success_message)
                
                # Auto login user after successful registration
                login(request, user)
                
                # Return appropriate response
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': success_message,
                        'redirect_url': '/authentication/login/'
                    })
                else:
                    return redirect('authentication:login')
                    
            except Exception as e:
                logger.error(f"Error during registration: {e}")
                error_message = f"Terjadi kesalahan saat memproses registrasi: {str(e)}"
                messages.error(request, error_message)
                
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'error': error_message
                    }, status=500)
        else:
            error_message = "Tolong periksa kembali formulir."
            messages.error(request, error_message)
            
            if is_ajax:
                # Return form errors for AJAX
                errors = {}
                if user_form.errors:
                    errors['user_form'] = user_form.errors
                if nakes_form.errors:
                    errors['nakes_form'] = nakes_form.errors
                
                return JsonResponse({
                    'success': False,
                    'error': error_message,
                    'form_errors': errors
                }, status=400)

    else:
        user_form = UserRegisterForm()
        nakes_form = NakesRegistrationForm()

    return render(request, 'register.html', {
        'user_form': user_form,
        'nakes_form': nakes_form,
        'available_categories': [choice[0] for choice in KATEGORI_KUALIFIKASI_CHOICES[:10]]
    })

def registration_success(request):
    """Show registration success page"""
    ai_analysis = request.session.get('registration_ai_analysis', {})
    
    # Clear the session data after displaying
    if 'registration_ai_analysis' in request.session:
        del request.session['registration_ai_analysis']
    
    return render(request, 'registration_success.html', {
        'ai_analysis': ai_analysis
    })

# Utility functions for role-based access
def role_required(allowed_roles=[]):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                return redirect('login')  # atau halaman unauthorized

            if hasattr(user, 'departemen') and 'departemen' in allowed_roles:
                request.departemen = user.departemen
                request.faskes = user.departemen.faskes  # ← ini penting!
                return view_func(request, *args, **kwargs)
            
            elif hasattr(user, 'otherrole') and 'otherrole' in allowed_roles:
                request.otherrole = user.otherrole
                # set attribut lain jika perlu
                return view_func(request, *args, **kwargs)

            return redirect('unauthorized')  # misalnya: render 403

        return _wrapped_view
    return decorator

def get_user_context(request):
    """Helper function untuk mendapatkan context user berdasarkan role"""
    if hasattr(request, 'user_role_info'):
        role_info = request.user_role_info
    else:
        role_info = detect_user_role(request.user)

    if role_info == "nakes":
        return Nakes.objects.get(user=request.user)
    elif role_info == "departemen":
        return Departemen.objects.get(user=request.user)
    else:
        raise ValidationError("User role not found")

# AJAX endpoints (if needed)
@csrf_exempt
def ajax_analyze_certificate(request):
    """AJAX endpoint for certificate analysis - currently disabled"""
    return JsonResponse({
        'success': False,
        'error': 'AI analysis temporarily disabled'
    }, status=503)

def get_available_categories(request):
    """API endpoint to get available categories"""
    try:
        return JsonResponse({
            'categories': KATEGORI_KUALIFIKASI_CHOICES,
            'total_count': len(KATEGORI_KUALIFIKASI_CHOICES)
        })
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return JsonResponse({
            'error': 'Error retrieving categories'
        }, status=500)