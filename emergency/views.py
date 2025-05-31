from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required # Jika hanya admin yang bisa akses
from django.contrib import messages
from django.utils import timezone
from .models import EmergencyEvent
from .forms import EmergencyActivationForm
import datetime # untuk simulasi API

# Dummy function untuk simulasi status API BNPB/BPBD
def get_bnpb_api_status_dummy():
    # Dalam implementasi nyata, ini akan memanggil API BNPB/BPBD
    # dan mengembalikan status koneksi serta data terbaru.
    # Untuk sekarang, kita buat dummy saja:
    import random
    connected = random.choice([True, True, False]) # Peluang lebih besar terhubung
    if connected:
        return {
            "connected": True,
            "last_sync": timezone.now() - datetime.timedelta(minutes=random.randint(5,60)),
            "error_message": None
        }
    else:
        return {
            "connected": False,
            "last_sync": None,
            "error_message": "Gagal menghubungi server BNPB/BPBD."
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

# @login_required # Uncomment jika halaman ini butuh login
def emergency_activation_dashboard(request):
    # Simulasi deteksi otomatis dari API BNPB
    # Di dunia nyata, ini bisa jadi background task yang memanggil API BNPB/BPBD
    # Jika ada alert baru dengan severity tinggi, bisa otomatis membuat EmergencyEvent
    # atau memberi notifikasi ke admin untuk aktivasi manual.
    # Contoh:
    # new_alerts = check_bnpb_api_for_critical_alerts()
    # for alert_data in new_alerts:
    #     if not EmergencyEvent.objects.filter(api_alert_details__id=alert_data['id'], is_active=True).exists():
    #         event = EmergencyEvent(
    #             disaster_type=alert_data['type'],
    #             location_description=alert_data['location'],
    #             severity_level=alert_data['severity'], # Asumsi API memberikan severity
    #             affected_regions_input=", ".join(alert_data['regions']),
    #             triggered_by_api=True,
    #             api_alert_details=alert_data
    #         )
    #         event.activate(by_api=True, api_details=alert_data)
    #         messages.info(request, f"Mode darurat otomatis diaktifkan untuk: {event.disaster_type} di {event.location_description}")


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

# @login_required
def deactivate_emergency_event(request, event_id):
    if request.method == 'POST': # Hanya proses POST request untuk keamanan
        event = get_object_or_404(EmergencyEvent, id=event_id, is_active=True)
        event.deactivate()
        messages.info(request, f"Mode Darurat untuk '{event.disaster_type}' telah dinonaktifkan.")
    return redirect('emergency:activate_emergency')