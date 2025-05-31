import json
import random
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth.decorators import login_required # Replaced by role_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from .models import EmergencyEvent
from .forms import *
import datetime # untuk simulasi API
from django.views.decorators.http import require_POST # For deactivate_emergency_event

from authentication.views import role_required # Import custom decorator

# Dummy function untuk simulasi status API BNPB/BPBD
def get_bnpb_api_status_dummy():
    return {
        "connected": True,
        "last_sync": timezone.now() - datetime.timedelta(minutes=random.randint(5,60)),
        "error_message": None
    }
   
# Dummy function untuk simulasi alert dari API
def get_recent_alerts_dummy():
    alerts = [
        {"name": "Peringatan Dini Tsunami", "location": "Pantai Selatan Jawa", "timestamp": timezone.now() - datetime.timedelta(hours=1)},
        {"name": "Peningkatan Aktivitas Gunung Api", "location": "Gunung Semeru", "timestamp": timezone.now() - datetime.timedelta(hours=3)},
    ]
    return alerts

@role_required(['superuser'])
def emergency_activation_dashboard(request):
    if request.method == 'POST':
        if 'manual_activation' in request.POST:
            form = EmergencyActivationForm(request.POST)
            if form.is_valid():
                event = form.save(commit=False)
                event.activate(user=request.user) # Pass the logged-in superuser
                messages.success(request, f"Mode Darurat untuk '{event.disaster_type}' berhasil diaktifkan!")
                return redirect('emergency:activate_emergency')
            else:
                messages.error(request, "Gagal mengaktifkan mode darurat. Periksa kembali isian form.")
    else:
        form = EmergencyActivationForm()

    active_emergencies = EmergencyEvent.objects.filter(is_active=True).order_by('-activation_time')
    bnpb_api_status = get_bnpb_api_status_dummy()
    recent_alerts_data = []
    if bnpb_api_status["connected"]:
         recent_alerts_data = get_recent_alerts_dummy()

    context = {
        'form': form,
        'active_emergencies': active_emergencies,
        'bnpb_api_status': bnpb_api_status,
        'recent_alerts': recent_alerts_data,
    }
    return render(request, 'activate_emergency.html', context)

@role_required(['superuser'])
@require_POST # Ensure this action is via POST
def deactivate_emergency_event(request, event_id):
    event = get_object_or_404(EmergencyEvent, id=event_id, is_active=True)
    event.deactivate() # No user needed for deactivation logic in model
    messages.info(request, f"Mode Darurat untuk '{event.disaster_type}' telah dinonaktifkan.")
    return redirect('emergency:activate_emergency')

@role_required(['superuser'])
def list_events_for_acceleration(request):
    active_emergencies = EmergencyEvent.objects.filter(is_active=True).order_by('-activation_time')
    context = {
        'active_emergencies': active_emergencies,
        'page_title': "Konfigurasi Akselerasi Pencocokan Darurat"
    }
    return render(request, 'list_events_for_acceleration.html', context)

@role_required(['superuser'])
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

# Public view, no authentication needed
def volunteer_registration(request):
    if request.method == 'POST':
        form = VolunteerProfileRegistrationForm(request.POST)
        if form.is_valid():
            try:
                profile = form.save()
                request.session['registered_volunteer_email'] = profile.email
                messages.success(request, f"Profil relawan atas nama {profile.full_name} berhasil dibuat. Silakan lanjutkan untuk memilih kejadian darurat yang ingin dibantu.")
                return redirect('emergency:volunteer_event_list')
            except IntegrityError:
                messages.error(request, "Email yang Anda masukkan sudah terdaftar. Jika ini adalah Anda, silakan langsung pilih kejadian darurat.")
                return redirect('emergency:volunteer_event_list') 
    else:
        form = VolunteerProfileRegistrationForm()
    context = {
        'form': form,
        'page_title': "Pendaftaran Relawan Non-Medis",
        'training_module_link': "https://www.example.com/basic-disaster-training"
    }
    return render(request, 'volunteer_registration_form.html', context)

# Public view
def volunteer_event_list(request):
    active_events = EmergencyEvent.objects.filter(is_active=True).order_by('-activation_time')
    volunteer_profile = None
    registered_email = request.session.get('registered_volunteer_email')
    if registered_email:
        try:
            volunteer_profile = VolunteerProfile.objects.get(email=registered_email)
        except VolunteerProfile.DoesNotExist:
            if 'registered_volunteer_email' in request.session: # check before deleting
                del request.session['registered_volunteer_email']
            
    events_data = []
    for event in active_events:
        has_applied, application_status = False, None
        if volunteer_profile:
            application = VolunteerApplication.objects.filter(emergency_event=event, volunteer_profile=volunteer_profile).first()
            if application:
                has_applied = True
                application_status = application.get_status_display()
        events_data.append({
            'event': event, 'has_applied': has_applied, 'application_status': application_status
        })
    context = {
        'events_data': events_data, 'volunteer_profile': volunteer_profile,
        'page_title': "Pilih Kejadian Darurat untuk Dibantu",
    }
    return render(request, 'volunteer_event_list.html', context)

# Public view, but relies on session for volunteer profile
def volunteer_apply_to_event(request, event_id):
    event = get_object_or_404(EmergencyEvent, id=event_id, is_active=True)
    registered_email = request.session.get('registered_volunteer_email')
    if not registered_email:
        messages.warning(request, "Anda harus mendaftarkan profil relawan terlebih dahulu.")
        return redirect(reverse('emergency:volunteer_registration') + f"?next={request.path}")
    try:
        volunteer_profile = VolunteerProfile.objects.get(email=registered_email)
    except VolunteerProfile.DoesNotExist:
        messages.error(request, "Profil relawan tidak ditemukan. Silakan daftar ulang.")
        if 'registered_volunteer_email' in request.session:
             del request.session['registered_volunteer_email']
        return redirect('emergency:volunteer_registration')

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
                form.save_m2m()
                messages.success(request, f"Pengajuan Anda untuk membantu di kejadian '{event.disaster_type}' telah berhasil dikirim. Terima kasih!")
                return redirect('emergency:volunteer_event_list')
            except IntegrityError:
                 messages.error(request, f"Anda sudah mengajukan diri untuk kejadian '{event.disaster_type}'.")
                 return redirect('emergency:volunteer_event_list')
    else:
        form = VolunteerEventApplicationForm()
    context = {
        'form': form, 'event': event, 'volunteer_profile': volunteer_profile,
        'page_title': f"Formulir Relawan: {event.disaster_type}",
    }
    return render(request, 'volunteer_apply_to_event_form.html', context)

@role_required(['superuser'])
def admin_event_volunteer_dashboard(request, event_id):
    event = get_object_or_404(EmergencyEvent, id=event_id)
    applications = VolunteerApplication.objects.filter(emergency_event=event)\
                                           .select_related('volunteer_profile')\
                                           .prefetch_related('task_categories_preference')\
                                           .order_by('status', '-application_date')
    status_filter = request.GET.get('status_filter')
    if status_filter:
        applications = applications.filter(status=status_filter)
    context = {
        'event': event, 'applications': applications,
        'status_choices': VolunteerApplication.STATUS_CHOICES,
        'current_status_filter': status_filter,
        'page_title': f"Manajemen Relawan: {event.disaster_type}"
    }
    return render(request, 'admin_event_volunteer_dashboard.html', context)

@role_required(['superuser'])
def admin_manage_volunteer_application(request, application_id):
    application = get_object_or_404(VolunteerApplication, id=application_id)
    volunteer_profile = application.volunteer_profile
    
    if request.method == 'POST':
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
        'application': application, 'volunteer_profile': volunteer_profile,
        'app_form': app_form, 'profile_form': profile_form,
        'page_title': f"Kelola Relawan: {volunteer_profile.full_name} ({application.emergency_event.disaster_type})"
    }
    return render(request, 'admin_manage_volunteer_application.html', context)

@role_required(['superuser', 'departemen']) # Faskes can also see resource tracking for events they are involved in
def resource_tracking_dashboard(request, event_id):
    event = get_object_or_404(EmergencyEvent, id=event_id)
    # If user is 'departemen', further check if their Faskes is involved or related to the event might be needed.
    # For now, allow access if role is departemen.
    
    deployed_professionals_data = [
        {"id": 1, "name": "Dr. Budi Santoso", "role": "Dokter Umum", "location": "Posko Utama Banjarbaru", "last_check_in": "2024-03-15 10:00", "status_notes": "Sedang menangani pasien"},
        {"id": 2, "name": "Suster Ani Wijaya", "role": "Perawat", "location": "RS Lapangan Martapura", "last_check_in": "2024-03-15 09:30", "status_notes": "Persiapan operasi minor"},
    ]
    deployed_volunteers = VolunteerApplication.objects.filter(
        emergency_event=event, status='DEPLOYED'
    ).select_related('volunteer_profile')

    min_lat, max_lat = -4.2, 4.2
    min_lon, max_lon = 108.8, 119.0
    map_personnel_points = []
    for prof in deployed_professionals_data:
        map_personnel_points.append({
            "id": f"prof_{prof['id']}", "lat": round(random.uniform(min_lat + 0.5, max_lat - 0.5), 6),
            "lon": round(random.uniform(min_lon + 0.5, max_lon - 0.5), 6), "type": "Profesional",
            "name": prof["name"], "role": prof["role"], "location_desc": prof["location"],
            "popup_html": f"<strong>{prof['name']}</strong><br>Peran: {prof['role']}<br>Lokasi: {prof['location']}"
        })
    for app in deployed_volunteers:
        map_personnel_points.append({
            "id": f"vol_{app.id}", "lat": round(random.uniform(min_lat + 0.5, max_lat - 0.5), 6),
            "lon": round(random.uniform(min_lon + 0.5, max_lon - 0.5), 6), "type": "Relawan",
            "name": app.volunteer_profile.full_name,
            "role": ", ".join([cat.name for cat in app.task_categories_preference.all()]) or "Belum ada peran spesifik",
            "location_desc": app.assigned_location_detail or event.location_description,
            "popup_html": f"<strong>{app.volunteer_profile.full_name}</strong> (Relawan)<br>Minat: {', '.join([cat.name for cat in app.task_categories_preference.all()]) or '-'}<br>Lokasi Tugas: {app.assigned_location_detail or event.location_description}"
        })
    
    whatsapp_group_link = "https://chat.whatsapp.com/YOUR_GROUP_INVITE_LINK"
    context = {
        'event': event, 'deployed_professionals': deployed_professionals_data,
        'deployed_volunteers': deployed_volunteers,
        'map_personnel_points_json': json.dumps(map_personnel_points),
        'whatsapp_group_link': whatsapp_group_link,
        'page_title': f"Pelacakan Sumber Daya: {event.disaster_type}"
    }
    return render(request, 'resource_tracking_dashboard.html', context)

@role_required(['departemen'])
def request_emergency_fund(request):
    faskes_instance = request.faskes # Faskes instance from decorator

    if request.method == 'POST':
        form = EmergencyFundRequestForm(request.POST)
        if form.is_valid():
            fund_request = form.save(commit=False)
            fund_request.faskes = faskes_instance # Set Faskes from logged-in user
            fund_request.save()
            messages.success(request, f"Permintaan dana untuk {fund_request.faskes.nama_faskes} berhasil diajukan.")
            # Redirect to a Faskes-specific list or a general confirmation page
            return redirect('emergency:list_fund_requests') # For now, redirect to admin list
    else:
        # Pre-fill Faskes if desired, though it's not in the form anymore
        form = EmergencyFundRequestForm() 
        # If you had a Faskes selection and wanted to pre-select it:
        # initial_data = {'faskes': faskes_instance.pk}
        # form = EmergencyFundRequestForm(initial=initial_data)
        # However, with faskes field removed, this is not necessary.

    context = {
        'form': form,
        'page_title': "Formulir Permintaan Dana Darurat Operasional",
        'faskes_name': faskes_instance.nama_faskes # Pass Faskes name for display
    }
    return render(request, 'request_fund_form.html', context)

@role_required(['superuser'])
def list_fund_requests(request):
    status_filter = request.GET.get('status_filter')
    event_filter = request.GET.get('event_filter')
    requests_list = EmergencyFundRequest.objects.select_related('emergency_event', 'faskes', 'approved_by').all()
    if status_filter:
        requests_list = requests_list.filter(status=status_filter)
    if event_filter:
        requests_list = requests_list.filter(emergency_event_id=event_filter)
    active_events = EmergencyEvent.objects.filter(is_active=True)
    context = {
        'fund_requests': requests_list, 'status_choices': EmergencyFundRequest.REQUEST_STATUS_CHOICES,
        'active_events': active_events, 'current_status_filter': status_filter,
        'current_event_filter': event_filter, 'page_title': "Daftar Permintaan Dana Darurat"
    }
    return render(request, 'list_fund_requests.html', context)

@role_required(['superuser'])
def manage_fund_request(request, request_id):
    fund_request = get_object_or_404(EmergencyFundRequest, id=request_id)
    
    # Initialize forms with prefix to avoid name collisions if rendered together
    approval_form = EmergencyFundApprovalForm(instance=fund_request, prefix="approval")
    disbursement_form = FundDisbursementForm(instance=fund_request, prefix="disbursement")
    report_form = FundReportSubmissionForm(instance=fund_request, prefix="report")

    if request.method == 'POST':
        original_status = fund_request.status
        if 'submit_approval' in request.POST:
            approval_form = EmergencyFundApprovalForm(request.POST, instance=fund_request, prefix="approval")
            if approval_form.is_valid():
                updated_request = approval_form.save(commit=False)
                if updated_request.status in ['APPROVED', 'REJECTED'] and original_status == 'PENDING':
                    updated_request.approved_by = request.user
                    updated_request.approval_date = timezone.now()
                # Logic for DISBURSED from APPROVED or REPORTED from DISBURSED via this form
                elif updated_request.status == 'DISBURSED' and original_status == 'APPROVED':
                     updated_request.disbursement_date = timezone.now()
                elif updated_request.status == 'REPORTED' and original_status == 'DISBURSED':
                    updated_request.report_submission_date = timezone.now()

                updated_request.save()
                messages.success(request, f"Status permintaan dana untuk {fund_request.faskes.nama_faskes} berhasil diperbarui.")
                return redirect('emergency:manage_fund_request', request_id=fund_request.id)
            else:
                messages.error(request, "Gagal memperbarui status. Periksa form persetujuan.")
        
        elif 'submit_disbursement' in request.POST:
            if fund_request.status == 'APPROVED':
                disbursement_form = FundDisbursementForm(request.POST, request.FILES, instance=fund_request, prefix="disbursement")
                if disbursement_form.is_valid():
                    updated_request = disbursement_form.save(commit=False)
                    updated_request.status = 'DISBURSED'
                    updated_request.disbursement_date = timezone.now()
                    updated_request.save()
                    messages.success(request, f"Bukti pencairan dana untuk {fund_request.faskes.nama_faskes} berhasil diunggah.")
                    return redirect('emergency:manage_fund_request', request_id=fund_request.id)
                else:
                    messages.error(request, "Gagal mengunggah bukti pencairan. Periksa form.")
            else:
                messages.error(request, "Permintaan dana belum disetujui atau sudah dalam status lain.")

        elif 'submit_report' in request.POST:
            if fund_request.status == 'DISBURSED':
                report_form = FundReportSubmissionForm(request.POST, request.FILES, instance=fund_request, prefix="report")
                if report_form.is_valid():
                    updated_request = report_form.save(commit=False)
                    updated_request.status = 'REPORTED'
                    updated_request.report_submission_date = timezone.now()
                    updated_request.save()
                    messages.success(request, f"Laporan penggunaan dana untuk {fund_request.faskes.nama_faskes} berhasil diunggah.")
                    return redirect('emergency:manage_fund_request', request_id=fund_request.id)
                else:
                     messages.error(request, "Gagal mengunggah laporan. Periksa form.")
            else:
                messages.error(request, "Dana belum dicairkan atau sudah dilaporkan.")
    else: # GET request
        # Re-initialize forms on GET to ensure correct choices based on current status
        approval_form = EmergencyFundApprovalForm(instance=fund_request, prefix="approval")
        disbursement_form = FundDisbursementForm(instance=fund_request, prefix="disbursement")
        report_form = FundReportSubmissionForm(instance=fund_request, prefix="report")


    context = {
        'fund_request': fund_request, 'approval_form': approval_form,
        'disbursement_form': disbursement_form, 'report_form': report_form,
        'page_title': f"Kelola Permintaan Dana: {fund_request.faskes.nama_faskes}"
    }
    return render(request, 'manage_fund_request.html', context)