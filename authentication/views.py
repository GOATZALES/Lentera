# authentication/views.py - Auto Role Detection Login

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError, PermissionDenied
from management.models import Nakes
from .models import Departemen
import json

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

def detect_user_role(user): # This version is for login flow, raises ValidationError
    """
    Detects user role. Returns "nakes" or "departemen".
    Raises ValidationError if no specific role is found.
    """
    try:
        # Check Nakes first (example order)
        nakes_instance = Nakes.objects.get(user=user)
        # You might want to return nakes_instance.nama_lengkap or similar for message
        return "Nakes" # Or a more descriptive name if used for messages
    except Nakes.DoesNotExist:
        pass
    
    try:
        dept_instance = Departemen.objects.get(user=user)
        # You might want to return dept_instance.nama_departemen for message
        return dept_instance.nama_departemen # More specific for message
    except Departemen.DoesNotExist:
        pass
    
    # If superuser and no other role, treat as special case or deny login if specific role needed.
    if user.is_superuser:
        return "Superuser" # Or handle as an admin role

    raise ValidationError("Peran pengguna tidak dikenali dalam sistem.")


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
    user_name = None
    if request.user.is_authenticated:
        display_name = request.user.get_full_name() or request.user.username
        # More specific name if available
        role_type = get_user_role_type(request.user)
        if role_type == "departemen" and hasattr(request.user, 'departemen'):
            display_name = request.user.departemen.nama_departemen
        elif role_type == "nakes":
            try:
                nakes = Nakes.objects.get(user=request.user)
                display_name = nakes.nama_lengkap # Assuming this field exists
            except Nakes.DoesNotExist:
                pass
        user_name = display_name
    
    logout(request) # Correct: logout takes request object
    
    if user_name:
        messages.success(request, f'Sampai jumpa, {user_name}!')
    else:
        messages.success(request, 'Anda telah berhasil logout.')
    
    return redirect('authentication:login')


# Decorator for role-based access control
def role_required(allowed_roles):
    """
    Decorator to restrict access based on user role.
    If 'departemen' is in allowed_roles, it attaches `request.departemen` (Departemen instance)
    and `request.faskes` (Faskes instance) to the request object.
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Anda harus login terlebih dahulu.')
                return redirect('authentication:login')

            user_role = get_user_role_type(request.user)

            # Superuser override: if 'superuser' is an allowed role and user is superuser, grant access.
            # Or, if you want superusers to access everything, you can add: if user_role == 'superuser': pass
            if user_role == 'superuser' and 'superuser' in allowed_roles:
                 request.user_role = user_role
                 # Superuser might not have a 'faskes' context unless specifically handled
                 return view_func(request, *args, **kwargs)


            if user_role not in allowed_roles:
                messages.error(request, f'Akses ditolak. Halaman ini hanya untuk pengguna dengan peran: {", ".join(allowed_roles)}.')
                # Redirect to their own dashboard if possible, or just login
                # This requires a robust redirect_by_role that doesn't get into a loop
                # For safety, redirect to login or a specific access_denied page.
                return redirect('authentication:login') 
            
            # If the role is 'departemen' and it's allowed, attach departemen and faskes instances
            if user_role == 'departemen': # No need to check 'departemen' in allowed_roles again, already passed above
                try:
                    # Departemen.user is a OneToOneField, so request.user.departemen should exist
                    departemen_instance = request.user.departemen
                    request.departemen = departemen_instance 
                    request.faskes = departemen_instance.faskes 
                except Departemen.DoesNotExist: 
                    messages.error(request, 'Profil departemen Anda tidak ditemukan. Silakan hubungi administrator.')
                    return redirect('authentication:login')
            
            request.user_role = user_role # For generic use in views if needed
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

# Utility functions untuk views (No change needed for this request for get_user_context if planning uses request.faskes)
def get_user_context(request):
    """
    Helper function untuk mendapatkan context user berdasarkan role
    Note: This function re-detects role. For views using @role_required,
    it's often better to use the role/context attached to the request by the decorator.
    """
    # Prefer role set by decorator if available
    if hasattr(request, 'user_role'):
        role_info_str = request.user_role
        if role_info_str == "departemen" and hasattr(request, 'departemen'):
            return request.departemen
        elif role_info_str == "nakes":
            try: # Nakes instance might not be attached by role_required
                return Nakes.objects.get(user=request.user)
            except Nakes.DoesNotExist:
                pass # Fall through to re-detection or error
        # Add other roles if necessary
    
    # Fallback or if decorator didn't attach specific context object
    try:
        role_info_str = detect_user_role(request.user) # This can raise ValidationError

        if role_info_str == "nakes" or (isinstance(role_info_str, str) and "Nakes" in role_info_str) : # Adjust based on detect_user_role output
            nakes = Nakes.objects.get(user=request.user)
            return nakes
        # For departemen, detect_user_role might return departemen name
        elif hasattr(request.user, 'departemen'): # More robust check
            departemen = Departemen.objects.get(user=request.user)
            return departemen
        # Handle superuser if get_user_context is expected to return something for them
        elif role_info_str == "Superuser" and request.user.is_superuser:
             return request.user # Or a specific superuser profile

    except ValidationError:
        # This implies user is authenticated but has no defined role in our system.
        # This case should ideally be handled by redirecting to login or an error page.
        # Raising PermissionDenied here if no context can be returned.
        raise PermissionDenied("Tidak dapat menentukan konteks pengguna yang valid.")
    
    # Fallback if role detected but instance not fetched (should be rare with current logic)
    raise PermissionDenied("Konteks pengguna tidak valid atau tidak ditemukan.")