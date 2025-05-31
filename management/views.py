# management/views.py 
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.models import User

from datetime import timedelta
import json

from .dummy import create_dummy_data
from .models import Nakes, Shift, ShiftAssignment, Departemen, Faskes
from .forms import NakesProfileForm, NakesAvailabilityForm
from .choices import KATEGORI_KUALIFIKASI_CHOICES, PROFESI_CHOICES, STATUS_CHOICES, JENIS_KELAMIN_CHOICES




def nakes_profile_view(request):
    nakes = get_current_nakes()
    if not nakes:
        messages.error(request, "Nakes profile not found. Please ensure you are logged in.")
        return redirect('some_other_page') # Redirect ke halaman lain jika nakes tidak ada

    if request.method == 'POST':
        form = NakesProfileForm(request.POST, instance=nakes)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil berhasil diperbarui!")
            return redirect('management:nakes_profile')
        else:
            messages.error(request, "Terdapat kesalahan saat memperbarui profil. Mohon cek input Anda.")
    else:
        form = NakesProfileForm(instance=nakes)
    
    # Form untuk ketersediaan
    availability_form = NakesAvailabilityForm()

    context = {
        'nakes': nakes,
        'form': form,
        'availability_form': availability_form,
    }
    return render(request, 'nakes_profile.html', context)


def get_current_nakes():
    try:
        # Ambil Nakes yang namanya 'Budi Santoso' atau username 'nakes_histori_banyak'
        user_to_load = User.objects.get(username='nakes_histori_banyak')
        nakes = Nakes.objects.get(user=user_to_load)
        return nakes
    except (User.DoesNotExist, Nakes.DoesNotExist):
        print("Nakes 'Budi Santoso' tidak ditemukan. Pastikan data dummy sudah dibuat.")
        create_dummy_data()
        nakes = get_current_nakes()
        return nakes

def cari_tugas_view(request):
    """View untuk halaman cari tugas dengan tampilan faskes dan jadwal"""
    nakes = get_current_nakes()
    if not nakes:
        messages.error(request, "Nakes profile not found.")
        return redirect('management:nakes_profile')

    # Ambil semua faskes yang memiliki shift yang cocok dengan profesi dan kualifikasi nakes
    faskes_with_shifts = Faskes.objects.filter(
        departemen__shifts__profesi=nakes.profesi,
        departemen__shifts__kategori_kualifikasi=nakes.kategori_kualifikasi,
        departemen__shifts__is_active=True,
        departemen__shifts__is_completed_by_faskes=False,
        departemen__shifts__tanggal_shift__gte=timezone.now().date()
    ).distinct().prefetch_related('departemen')

    # Struktur data untuk frontend
    faskes_data = []
    for faskes in faskes_with_shifts:
        departemen_with_shifts = []
        for departemen in faskes.departemen.all():
            # Cek apakah departemen ini punya shift yang cocok
            shift_count = departemen.shifts.filter(
                profesi=nakes.profesi,
                kategori_kualifikasi=nakes.kategori_kualifikasi,
                is_active=True,
                is_completed_by_faskes=False,
                tanggal_shift__gte=timezone.now().date()
            ).exclude(
                assignments__nakes=nakes,
                assignments__status_assignment__in=['Pending', 'Accepted', 'Clocked In', 'Completed']
            ).count()
            
            if shift_count > 0:
                departemen_with_shifts.append({
                    'departemen': departemen,
                    'shift_count': shift_count
                })
        
        if departemen_with_shifts:
            # Tambahkan informasi tipe faskes jika tidak ada
            if not faskes.tipe_faskes:
                if 'rumah sakit' in faskes.nama_faskes.lower() or 'rs' in faskes.nama_faskes.lower():
                    faskes.tipe_faskes = 'Rumah Sakit'
                elif 'puskesmas' in faskes.nama_faskes.lower():
                    faskes.tipe_faskes = 'Puskesmas'
                elif 'klinik' in faskes.nama_faskes.lower():
                    faskes.tipe_faskes = 'Klinik'
                else:
                    faskes.tipe_faskes = 'Faskes'
            
            faskes_data.append({
                'faskes': faskes,
                'departemen_list': departemen_with_shifts
            })

    context = {
        'nakes': nakes,
        'faskes_data': faskes_data,
    }
    return render(request, 'cari_tugas.html', context)

def get_departemen_schedule(request, departemen_id):
    """AJAX endpoint untuk mendapatkan jadwal departemen"""
    nakes = get_current_nakes()
    if not nakes:
        return JsonResponse({'error': 'Nakes not found'}, status=400)
    
    departemen = get_object_or_404(Departemen, departemen_id=departemen_id)
    
    # Ambil tanggal start (hari ini) dan end (2 minggu ke depan)
    start_date = timezone.now().date()
    end_date = start_date + timedelta(days=14)
    
    # Ambil semua shift yang tersedia di departemen ini
    shifts = Shift.objects.filter(
        departemen=departemen,
        profesi=nakes.profesi,
        kategori_kualifikasi=nakes.kategori_kualifikasi,
        is_active=True,
        is_completed_by_faskes=False,
        tanggal_shift__range=[start_date, end_date]
    ).exclude(
        assignments__nakes=nakes,
        assignments__status_assignment__in=['Pending', 'Accepted', 'Clocked In', 'Completed']
    ).order_by('tanggal_shift', 'jam_mulai')
    
    # Format data untuk calendar
    shifts_data = []
    for shift in shifts:
        shifts_data.append({
            'shift_id': str(shift.shift_id),
            'tanggal': shift.tanggal_shift.isoformat(),
            'jam_mulai': shift.jam_mulai.strftime('%H:%M'),
            'jam_selesai': shift.jam_selesai.strftime('%H:%M'),
            'durasi_menit': shift.durasi_menit,
            'deskripsi_tugas': shift.deskripsi_tugas or '',
            'estimated_worth': shift.estimated_worth,
        })
    
    return JsonResponse({
        'departemen': {
            'nama': departemen.nama_departemen,
            'faskes': departemen.faskes.nama_faskes,
        },
        'shifts': shifts_data,
        'date_range': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        }
    })

def accept_shift_ajax(request, shift_id):
    """AJAX endpoint untuk menerima shift"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    nakes = get_current_nakes()
    if not nakes:
        return JsonResponse({'error': 'Nakes not found'}, status=400)

    shift = get_object_or_404(Shift, shift_id=shift_id)

    # Pastikan shift masih aktif dan belum ada assignment untuk nakes ini
    if not shift.is_active:
        return JsonResponse({'error': 'Shift tidak aktif'}, status=400)
    
    if ShiftAssignment.objects.filter(
        shift=shift, 
        nakes=nakes, 
        status_assignment__in=['Pending', 'Accepted', 'Clocked In', 'Completed']
    ).exists():
        return JsonResponse({'error': 'Anda sudah ditugaskan untuk shift ini'}, status=400)
    
    try:
        with transaction.atomic():
            assignment = ShiftAssignment.objects.create(
                shift=shift,
                nakes=nakes,
                status_assignment='Accepted',
                waktu_nakes_menerima=timezone.now()
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Berhasil menerima shift di {shift.departemen.nama_departemen}',
            'assignment_id': str(assignment.assignment_id)
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

def nakes_profile_view(request):
    """View untuk halaman profile nakes dengan layout horizontal"""
    nakes = get_current_nakes()
    if not nakes:
        messages.error(request, "Nakes profile not found. Please ensure you are logged in.")
        return redirect('some_other_page')

    if request.method == 'POST':
        # Handle profile update
        form_data = request.POST.copy()
        
        # Convert log availability to minutes if provided
        if 'log_availability' in form_data:
            try:
                log_count = int(form_data['log_availability'])
                minutes = log_count * 50  # 1 log = 50 menit
                form_data['log_ketersediaan_menit'] = minutes
            except (ValueError, TypeError):
                pass
        
        # Handle multiple skills selection
        selected_skills = request.POST.getlist('skills')
        
        # Update nakes instance
        try:
            with transaction.atomic():
                # Update basic fields
                nakes.nama_lengkap = form_data.get('nama_lengkap', nakes.nama_lengkap)
                nakes.nomor_telepon = form_data.get('nomor_telepon', nakes.nomor_telepon)
                nakes.alamat = form_data.get('alamat', nakes.alamat)
                
                if form_data.get('tanggal_lahir'):
                    nakes.tanggal_lahir = form_data.get('tanggal_lahir')
                
                nakes.jenis_kelamin = form_data.get('jenis_kelamin', nakes.jenis_kelamin)
                nakes.profesi = form_data.get('profesi', nakes.profesi)
                nakes.status = form_data.get('status', nakes.status)
                nakes.nomor_registrasi = form_data.get('nomor_registrasi', nakes.nomor_registrasi)
                
                if form_data.get('tahun_pengalaman'):
                    nakes.tahun_pengalaman = int(form_data.get('tahun_pengalaman', nakes.tahun_pengalaman))
                
                nakes.kategori_kualifikasi = form_data.get('kategori_kualifikasi', nakes.kategori_kualifikasi)
                
                if form_data.get('log_ketersediaan_menit'):
                    nakes.log_ketersediaan_menit = int(form_data.get('log_ketersediaan_menit', nakes.log_ketersediaan_menit))
                
                nakes.save()
                
                # Update skills
                # First, clear all existing skills except the primary qualification
                from .models import NakesSkill
                NakesSkill.objects.filter(nakes=nakes).delete()
                
                # Add selected skills (excluding primary qualification to avoid duplication)
                for skill_name in selected_skills:
                    if skill_name != nakes.kategori_kualifikasi:
                        nakes.add_skill(skill_name)
                
                messages.success(request, "Profil berhasil diperbarui!")
                return redirect('management:nakes_profile')
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan saat memperbarui profil: {str(e)}")
    
    # Get current skills for display
    current_skills = list(nakes.skills.values_list('skill_name', flat=True))
    if nakes.kategori_kualifikasi not in current_skills:
        current_skills.append(nakes.kategori_kualifikasi)
    
    # Categorize skills for better display
    skill_categories = {
        'profesi_umum': [],
        'spesialisasi': [],
        'sertifikasi': [],
        'manajemen': []
    }
    
    for value, label in KATEGORI_KUALIFIKASI_CHOICES:
        # Auto-categorize
        if 'spesialis' in label.lower():
            skill_categories['spesialisasi'].append((value, label))
        elif any(cert in label.lower() for cert in ['bls', 'acls', 'btls', 'atls', 'sertifikasi', 'pelatihan', 'manajemen nyeri', 'k3', 'penanganan', 'pengendalian', 'komunikasi', 'bahasa']):
            skill_categories['sertifikasi'].append((value, label))
        elif any(mgmt in label.lower() for mgmt in ['manajemen', 'quality', 'edukator']):
            skill_categories['manajemen'].append((value, label))
        else:
            skill_categories['profesi_umum'].append((value, label))
    
    # Prepare data for template
    context = {
        'nakes': nakes,
        'profesi_choices': PROFESI_CHOICES,
        'status_choices': STATUS_CHOICES,
        'jenis_kelamin_choices': JENIS_KELAMIN_CHOICES,
        'kategori_kualifikasi_choices': KATEGORI_KUALIFIKASI_CHOICES,
        'skill_categories': skill_categories,
        'current_skills': current_skills,
        'current_log_count': nakes.log_ketersediaan_menit // 50 if nakes.log_ketersediaan_menit else 0,
        'log_options': [(i, f"{i} Log ({i * 50} Menit)") for i in range(0, 21)],  # 0-20 logs
    }
    
    return render(request, 'nakes_profile.html', context)

def update_availability_ajax(request):
    """AJAX endpoint untuk update ketersediaan"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    nakes = get_current_nakes()
    if not nakes:
        return JsonResponse({'error': 'Nakes not found'}, status=400)
    
    try:
        data = json.loads(request.body)
        log_count = int(data.get('log_count', 0))
        minutes = log_count * 50
        
        nakes.log_ketersediaan_menit = minutes
        nakes.save()
        
        return JsonResponse({
            'success': True,
            'log_count': log_count,
            'total_minutes': minutes,
            'message': f'Ketersediaan diperbarui menjadi {log_count} log ({minutes} menit)'
        })
    
    except (ValueError, TypeError ) as e:
        return JsonResponse({'error': f'Invalid data: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

def nakes_histori_kinerja_view(request):
    """View untuk halaman histori kinerja nakes"""
    nakes = get_current_nakes()
    if not nakes:
        messages.error(request, "Nakes profile not found.")
        return redirect('management:nakes_profile')

    # Ambil semua assignment yang sudah completed dengan review
    completed_assignments = ShiftAssignment.objects.filter(
        nakes=nakes,
        status_assignment='Completed'
    ).select_related(
        'shift__departemen__faskes',
        'shift__departemen'
    ).prefetch_related(
        'review_faskes'
    ).order_by('-waktu_clock_out')

    # Prepare data untuk template
    histori_data = []
    total_shifts = 0
    total_rating = 0
    total_earnings = 0

    for assignment in completed_assignments:
        # Ambil review jika ada
        review = getattr(assignment, 'review_faskes', None)
        
        # Calculate statistics
        total_shifts += 1
        total_earnings += float(assignment.total_bayaran_nakes or 0)
        
        if review:
            total_rating += review.rating_kinerja

        # Format data untuk card
        histori_item = {
            'assignment': assignment,
            'faskes_name': assignment.shift.departemen.faskes.nama_faskes,
            'departemen_name': assignment.shift.departemen.nama_departemen,
            'tanggal_shift': assignment.shift.tanggal_shift,
            'jam_shift': f"{assignment.shift.jam_mulai.strftime('%H:%M')} - {assignment.shift.jam_selesai.strftime('%H:%M')}",
            'durasi': assignment.shift.durasi_menit,
            'bayaran': assignment.total_bayaran_nakes,
            'review': review,
            'rating': review.rating_kinerja if review else None,
            'komentar': review.komentar if review else None,
            'tanggal_review': review.tanggal_review if review else None,
        }
        histori_data.append(histori_item)

    # Calculate average rating
    avg_rating = (total_rating / total_shifts) if total_shifts > 0 else 0

    # Group by month for better organization
    from collections import defaultdict
    from datetime import datetime
    
    grouped_histori = defaultdict(list)
    for item in histori_data:
        month_key = item['tanggal_shift'].strftime('%Y-%m')
        month_name = item['tanggal_shift'].strftime('%B %Y')
        grouped_histori[month_key].append(item)
    
    # Convert to list and sort by month
    grouped_histori_list = []
    for month_key in sorted(grouped_histori.keys(), reverse=True):
        month_name = datetime.strptime(month_key, '%Y-%m').strftime('%B %Y')
        grouped_histori_list.append({
            'month': month_name,
            'items': grouped_histori[month_key]
        })

    context = {
        'nakes': nakes,
        'histori_data': histori_data,
        'grouped_histori': grouped_histori_list,
        'total_shifts': total_shifts,
        'avg_rating': round(avg_rating, 1),
        'total_earnings': total_earnings,
        'has_histori': len(histori_data) > 0,
    }
    
    return render(request, 'histori_kinerja.html', context)


# Tambahkan ini ke management/views.py

def nakes_evaluasi_view(request):
    """View untuk halaman evaluasi kinerja nakes"""
    nakes = get_current_nakes()
    if not nakes:
        messages.error(request, "Nakes profile not found.")
        return redirect('management:nakes_profile')

    # Ambil semua assignment yang sudah completed dengan review
    completed_assignments = ShiftAssignment.objects.filter(
        nakes=nakes,
        status_assignment='Completed'
    ).select_related(
        'shift__departemen__faskes',
        'shift__departemen'
    ).prefetch_related(
        'review_faskes'
    ).order_by('-waktu_clock_out')

    # Hitung statistik evaluasi
    total_shifts = completed_assignments.count()
    total_hours = sum([assignment.shift.durasi_menit for assignment in completed_assignments]) / 60
    total_earnings = sum([float(assignment.total_bayaran_nakes or 0) for assignment in completed_assignments])
    
    # Rating statistics
    reviews = [assignment.review_faskes for assignment in completed_assignments if hasattr(assignment, 'review_faskes')]
    total_reviews = len(reviews)
    
    if total_reviews > 0:
        avg_rating = sum([review.rating_kinerja for review in reviews]) / total_reviews
        rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for review in reviews:
            rating_distribution[review.rating_kinerja] += 1
        
        # Convert to percentages
        for rating in rating_distribution:
            rating_distribution[rating] = (rating_distribution[rating] / total_reviews) * 100
    else:
        avg_rating = 0
        rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    # Performance by faskes
    faskes_performance = {}
    for assignment in completed_assignments:
        if hasattr(assignment, 'review_faskes'):
            faskes_name = assignment.shift.departemen.faskes.nama_faskes
            if faskes_name not in faskes_performance:
                faskes_performance[faskes_name] = {
                    'total_shifts': 0,
                    'total_rating': 0,
                    'avg_rating': 0,
                    'earnings': 0
                }
            
            faskes_performance[faskes_name]['total_shifts'] += 1
            faskes_performance[faskes_name]['total_rating'] += assignment.review_faskes.rating_kinerja
            faskes_performance[faskes_name]['earnings'] += float(assignment.total_bayaran_nakes or 0)
    
    # Calculate averages
    for faskes in faskes_performance:
        if faskes_performance[faskes]['total_shifts'] > 0:
            faskes_performance[faskes]['avg_rating'] = faskes_performance[faskes]['total_rating'] / faskes_performance[faskes]['total_shifts']

    # Monthly performance data for charts
    from collections import defaultdict
    from datetime import datetime
    
    monthly_data = defaultdict(lambda: {'shifts': 0, 'earnings': 0, 'total_rating': 0, 'review_count': 0})
    
    for assignment in completed_assignments:
        month_key = assignment.shift.tanggal_shift.strftime('%Y-%m')
        monthly_data[month_key]['shifts'] += 1
        monthly_data[month_key]['earnings'] += float(assignment.total_bayaran_nakes or 0)
        
        if hasattr(assignment, 'review_faskes'):
            monthly_data[month_key]['total_rating'] += assignment.review_faskes.rating_kinerja
            monthly_data[month_key]['review_count'] += 1
    
    # Calculate monthly averages and convert to list
    monthly_performance = []
    for month_key in sorted(monthly_data.keys()):
        data = monthly_data[month_key]
        avg_rating = data['total_rating'] / data['review_count'] if data['review_count'] > 0 else 0
        
        # Convert month key to readable format
        month_name = datetime.strptime(month_key, '%Y-%m').strftime('%b %Y')
        
        monthly_performance.append({
            'month': month_name,
            'month_key': month_key,
            'shifts': data['shifts'],
            'earnings': data['earnings'],
            'avg_rating': round(avg_rating, 1)
        })

    # Skills assessment based on reviews
    skills_feedback = []
    for assignment in completed_assignments:
        if hasattr(assignment, 'review_faskes') and assignment.review_faskes.komentar:
            skills_feedback.append({
                'faskes': assignment.shift.departemen.faskes.nama_faskes,
                'departemen': assignment.shift.departemen.nama_departemen,
                'tanggal': assignment.shift.tanggal_shift,
                'rating': assignment.review_faskes.rating_kinerja,
                'komentar': assignment.review_faskes.komentar
            })

    # Recent performance trend (last 6 months)
    from datetime import timedelta
    six_months_ago = timezone.now().date() - timedelta(days=180)
    
    recent_assignments = completed_assignments.filter(
        shift__tanggal_shift__gte=six_months_ago
    )
    
    recent_performance = {
        'shifts': recent_assignments.count(),
        'avg_rating': 0,
        'total_earnings': sum([float(assignment.total_bayaran_nakes or 0) for assignment in recent_assignments])
    }
    
    recent_reviews = [assignment.review_faskes for assignment in recent_assignments if hasattr(assignment, 'review_faskes')]
    if recent_reviews:
        recent_performance['avg_rating'] = sum([review.rating_kinerja for review in recent_reviews]) / len(recent_reviews)

    context = {
        'nakes': nakes,
        'total_shifts': total_shifts,
        'total_hours': round(total_hours, 1),
        'total_earnings': total_earnings,
        'avg_rating': round(avg_rating, 1),
        'total_reviews': total_reviews,
        'rating_distribution': rating_distribution,
        'faskes_performance': faskes_performance,
        'monthly_performance': monthly_performance[-6:],  # Last 6 months
        'skills_feedback': skills_feedback[-5:],  # Last 5 feedback
        'recent_performance': recent_performance,
        'has_data': total_shifts > 0,
    }
    
    return render(request, 'evaluasi.html', context)