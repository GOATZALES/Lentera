import random
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required # Jika hanya admin yang bisa akses
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from .models import EmergencyEvent
from .forms import *
import datetime # untuk simulasi API

# Dummy function untuk simulasi status API BNPB/BPBD
def get_bnpb_api_status_dummy():
    return {
        "connected": True,
        "last_sync": timezone.now() - datetime.timedelta(minutes=random.randint(5,60)),
        "error_message": None
    }
   

# Dummy function untuk simulasi alert dari API
def get_recent_alerts_dummy():
    # Ini akan mengambil data alert terbaru dari API
    # Untuk sekarang, kita buat dummy:
    alerts = [
        {"name": "Peringatan Dini Tsunami", "location": "Pantai Selatan Jawa", "timestamp": timezone.now() - datetime.timedelta(hours=1)},
        {"name": "Peningkatan Aktivitas Gunung Api", "location": "Gunung Semeru", "timestamp": timezone.now() - datetime.timedelta(hours=3)},
    ]
    return alerts # Biasanya hanya tampilkan jika ada alert baru yang belum diproses

def emergency_activation_dashboard(request):
    if request.method == 'POST':
        if 'manual_activation' in request.POST: # Memastikan form manual yang disubmit
            form = EmergencyActivationForm(request.POST)
            if form.is_valid():
                event = form.save(commit=False)
                # Jika menggunakan login_required, user bisa diambil dari request.user
                # event.manually_triggered_by = request.user 
                event.activate(user=request.user if request.user.is_authenticated else None) # Menyimpan user jika login
                messages.success(request, f"Mode Darurat untuk '{event.disaster_type}' berhasil diaktifkan!")
                return redirect('emergency:activate_emergency') # Redirect untuk menghindari resubmit
            else:
                messages.error(request, "Gagal mengaktifkan mode darurat. Periksa kembali isian form.")
        # Bisa tambahkan logika untuk POST dari API trigger di sini jika diperlukan
    else:
        form = EmergencyActivationForm()

    active_emergencies = EmergencyEvent.objects.filter(is_active=True).order_by('-activation_time')
    bnpb_api_status = get_bnpb_api_status_dummy() # Ambil status API (dummy)
    
    # Ambil recent alerts (dummy) - idealnya ini hanya tampil jika relevan atau baru
    recent_alerts_data = []
    if bnpb_api_status["connected"]: # Hanya tampilkan jika API terhubung
         recent_alerts_data = get_recent_alerts_dummy()


    context = {
        'form': form,
        'active_emergencies': active_emergencies,
        'bnpb_api_status': bnpb_api_status,
        'recent_alerts': recent_alerts_data, # Untuk ditampilkan di UI
    }
    return render(request, 'activate_emergency.html', context)

def deactivate_emergency_event(request, event_id):
    if request.method == 'POST': # Hanya proses POST request untuk keamanan
        event = get_object_or_404(EmergencyEvent, id=event_id, is_active=True)
        event.deactivate()
        messages.info(request, f"Mode Darurat untuk '{event.disaster_type}' telah dinonaktifkan.")
    return redirect('emergency:activate_emergency')

def list_events_for_acceleration(request):
    active_emergencies = EmergencyEvent.objects.filter(is_active=True).order_by('-activation_time')
    context = {
        'active_emergencies': active_emergencies,
        'page_title': "Konfigurasi Akselerasi Pencocokan Darurat"
    }
    return render(request, 'list_events_for_acceleration.html', context)

def configure_matching_acceleration(request, event_id):
    event = get_object_or_404(EmergencyEvent, id=event_id, is_active=True)
    
    if request.method == 'POST':
        form = MatchingAccelerationForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, f"Pengaturan akselerasi untuk '{event.disaster_type}' berhasil diperbarui.")
            return redirect('emergency:list_events_for_acceleration')
        else:
            messages.error(request, "Gagal memperbarui pengaturan. Periksa isian form.")
    else:
        form = MatchingAccelerationForm(instance=event)

    context = {
        'form': form,
        'event': event,
        'page_title': f"Akselerasi untuk: {event.disaster_type}"
    }
    return render(request, 'configure_matching_acceleration.html', context)

def volunteer_registration(request):
    """Halaman pendaftaran profil relawan baru."""
    if request.method == 'POST':
        form = VolunteerProfileRegistrationForm(request.POST)
        if form.is_valid():
            try:
                profile = form.save()
                # Simpan email di session untuk kemudahan apply ke event setelah ini
                request.session['registered_volunteer_email'] = profile.email
                messages.success(request, f"Profil relawan atas nama {profile.full_name} berhasil dibuat. Silakan lanjutkan untuk memilih kejadian darurat yang ingin dibantu.")
                return redirect('emergency:volunteer_event_list')
            except IntegrityError: # Jika email sudah ada (unique=True)
                messages.error(request, "Email yang Anda masukkan sudah terdaftar. Jika ini adalah Anda, silakan langsung pilih kejadian darurat.")
                # Bisa arahkan ke halaman login jika ada, atau langsung ke daftar event
                return redirect('emergency:volunteer_event_list') 
    else:
        form = VolunteerProfileRegistrationForm()

    context = {
        'form': form,
        'page_title': "Pendaftaran Relawan Non-Medis",
        'training_module_link': "https://www.example.com/basic-disaster-training" # Ganti dengan link modul training Anda
    }
    return render(request, 'volunteer_registration_form.html', context)

def volunteer_event_list(request):
    """Menampilkan daftar kejadian darurat aktif untuk relawan."""
    active_events = EmergencyEvent.objects.filter(is_active=True).order_by('-activation_time')
    
    # Cek apakah relawan sudah punya profil (berdasarkan email di session)
    volunteer_profile = None
    registered_email = request.session.get('registered_volunteer_email')
    if registered_email:
        try:
            volunteer_profile = VolunteerProfile.objects.get(email=registered_email)
        except VolunteerProfile.DoesNotExist:
            # Email ada di session tapi profil tidak ada (jarang terjadi), hapus session
            del request.session['registered_volunteer_email']
            
    events_data = []
    for event in active_events:
        has_applied = False
        application_status = None
        if volunteer_profile:
            application = VolunteerApplication.objects.filter(emergency_event=event, volunteer_profile=volunteer_profile).first()
            if application:
                has_applied = True
                application_status = application.get_status_display()
        
        events_data.append({
            'event': event,
            'has_applied': has_applied,
            'application_status': application_status
        })

    context = {
        'events_data': events_data,
        'volunteer_profile': volunteer_profile,
        'page_title': "Pilih Kejadian Darurat untuk Dibantu",
    }
    return render(request, 'volunteer_event_list.html', context)

def volunteer_apply_to_event(request, event_id):
    """Form untuk relawan mendaftar ke suatu kejadian darurat."""
    event = get_object_or_404(EmergencyEvent, id=event_id, is_active=True)
    
    # Relawan harus punya profil dulu
    registered_email = request.session.get('registered_volunteer_email')
    if not registered_email:
        messages.warning(request, "Anda harus mendaftarkan profil relawan terlebih dahulu.")
        return redirect(reverse('emergency:volunteer_registration') + f"?next={request.path}")
    
    try:
        volunteer_profile = VolunteerProfile.objects.get(email=registered_email)
    except VolunteerProfile.DoesNotExist:
        messages.error(request, "Profil relawan tidak ditemukan. Silakan daftar ulang.")
        del request.session['registered_volunteer_email']
        return redirect('emergency:volunteer_registration')

    # Cek apakah profil sudah diverifikasi admin (jika ini syarat sebelum apply)
    # if not volunteer_profile.is_profile_verified_by_admin:
    #     messages.info(request, "Profil Anda sedang menunggu verifikasi admin. Anda akan dapat mendaftar setelah diverifikasi.")
    #     return redirect('emergency:volunteer_event_list')

    # Cek apakah sudah pernah apply untuk event ini
    if VolunteerApplication.objects.filter(emergency_event=event, volunteer_profile=volunteer_profile).exists():
        messages.info(request, f"Anda sudah mengajukan diri untuk kejadian '{event.disaster_type}'. Mohon tunggu informasi selanjutnya.")
        return redirect('emergency:volunteer_event_list')

    if request.method == 'POST':
        form = VolunteerEventApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.emergency_event = event
            application.volunteer_profile = volunteer_profile
            try:
                application.save()
                form.save_m2m() # Penting untuk ManyToManyField (task_categories_preference)
                messages.success(request, f"Pengajuan Anda untuk membantu di kejadian '{event.disaster_type}' telah berhasil dikirim. Terima kasih!")
                return redirect('emergency:volunteer_event_list')
            except IntegrityError: # Seharusnya sudah dicek di atas, tapi sebagai fallback
                 messages.error(request, f"Anda sudah mengajukan diri untuk kejadian '{event.disaster_type}'.")
                 return redirect('emergency:volunteer_event_list')
    else:
        form = VolunteerEventApplicationForm()

    context = {
        'form': form,
        'event': event,
        'volunteer_profile': volunteer_profile,
        'page_title': f"Formulir Relawan: {event.disaster_type}",
    }
    return render(request, 'volunteer_apply_to_event_form.html', context)


# --- Views untuk Volunteer Coordination (Admin) ---

@login_required # Pastikan hanya admin/staf yang bisa akses
def admin_event_volunteer_dashboard(request, event_id):
    """Dashboard admin untuk melihat dan mengelola relawan per event."""
    event = get_object_or_404(EmergencyEvent, id=event_id)
    applications = VolunteerApplication.objects.filter(emergency_event=event)\
                                           .select_related('volunteer_profile')\
                                           .prefetch_related('task_categories_preference')\
                                           .order_by('status', '-application_date')
    
    status_filter = request.GET.get('status_filter')
    if status_filter:
        applications = applications.filter(status=status_filter)

    context = {
        'event': event,
        'applications': applications,
        'status_choices': VolunteerApplication.STATUS_CHOICES,
        'current_status_filter': status_filter,
        'page_title': f"Manajemen Relawan: {event.disaster_type}"
    }
    return render(request, 'admin_event_volunteer_dashboard.html', context)

@login_required
def admin_manage_volunteer_application(request, application_id):
    """Halaman admin untuk mengupdate detail aplikasi relawan."""
    application = get_object_or_404(VolunteerApplication, id=application_id)
    volunteer_profile = application.volunteer_profile
    
    if request.method == 'POST':
        # Ada dua form di halaman ini: satu untuk aplikasi, satu untuk verifikasi profil
        app_form = VolunteerApplicationManagementForm(request.POST, instance=application, prefix="app")
        profile_form = VolunteerProfileVerificationForm(request.POST, instance=volunteer_profile, prefix="profile")

        if 'submit_app_form' in request.POST:
            if app_form.is_valid():
                app_form.save()
                messages.success(request, f"Detail aplikasi untuk {volunteer_profile.full_name} berhasil diperbarui.")
                return redirect('emergency:admin_manage_volunteer_application', application_id=application.id)
            else:
                messages.error(request, "Gagal memperbarui detail aplikasi. Periksa error di bawah.")
        
        elif 'submit_profile_form' in request.POST:
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, f"Status verifikasi profil {volunteer_profile.full_name} berhasil diperbarui.")
                return redirect('emergency:admin_manage_volunteer_application', application_id=application.id)
            else:
                messages.error(request, "Gagal memperbarui status verifikasi profil. Periksa error di bawah.")
    else:
        app_form = VolunteerApplicationManagementForm(instance=application, prefix="app")
        profile_form = VolunteerProfileVerificationForm(instance=volunteer_profile, prefix="profile")

    context = {
        'application': application,
        'volunteer_profile': volunteer_profile,
        'app_form': app_form,
        'profile_form': profile_form,
        'page_title': f"Kelola Relawan: {volunteer_profile.full_name} ({application.emergency_event.disaster_type})"
    }
    return render(request, 'admin_manage_volunteer_application.html', context)