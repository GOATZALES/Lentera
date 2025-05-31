# management/views.py - Complete version with all required functions

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from datetime import timedelta
import json

from .models import Nakes, Shift, ShiftAssignment, Departemen, Faskes
from .forms import NakesProfileForm, NakesAvailabilityForm
from .choices import KATEGORI_KUALIFIKASI_CHOICES, PROFESI_CHOICES, STATUS_CHOICES, JENIS_KELAMIN_CHOICES
from .dummy import create_dummy_data

logger = logging.getLogger(__name__)

# ===== UTILITY FUNCTIONS =====

def get_current_nakes():
    """Get current nakes - with fallback options"""
    try:
        # Try to get test user first
        try:
            user_to_load = User.objects.get(username='nakes_histori_banyak')
            nakes = Nakes.objects.get(user=user_to_load)
            logger.info(f"Found test nakes: {nakes.nama_lengkap}")
            return nakes
        except (User.DoesNotExist, Nakes.DoesNotExist):
            logger.warning("Test nakes not found")
        
        # Try to get any nakes
        nakes = Nakes.objects.first()
        if nakes:
            logger.info(f"Using first available nakes: {nakes.nama_lengkap}")
            return nakes
        
        # Create dummy data as last resort
        logger.info("Creating dummy data...")
        create_dummy_data()
        
        # Try again after creating dummy data
        user_to_load = User.objects.get(username='nakes_histori_banyak')
        nakes = Nakes.objects.get(user=user_to_load)
        logger.info(f"Created and found nakes: {nakes.nama_lengkap}")
        return nakes
        
    except Exception as e:
        logger.error(f"Failed to get current nakes: {e}", exc_info=True)
        return None

# ===== TEST ENDPOINTS =====

def test_api_connection(request):
    """Simple test endpoint"""
    try:
        return JsonResponse({
            'status': 'success',
            'message': 'API connection working',
            'method': request.method,
            'path': request.path,
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)

def test_departemen_list(request):
    """Test endpoint to list all departemen"""
    try:
        departemen_list = []
        for dept in Departemen.objects.all()[:10]:  # Limit to 10
            departemen_list.append({
                'id': str(dept.departemen_id),
                'nama': dept.nama_departemen,
                'faskes': dept.faskes.nama_faskes if dept.faskes else 'No Faskes'
            })
        
        return JsonResponse({
            'status': 'success',
            'count': len(departemen_list),
            'departemen': departemen_list
        })
    except Exception as e:
        logger.error(f"Error in test_departemen_list: {e}")
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)

@csrf_exempt
def test_schedule_simple(request, departemen_id):
    """Simplified schedule test"""
    try:
        # Check if departemen exists
        try:
            departemen = Departemen.objects.get(departemen_id=departemen_id)
        except Departemen.DoesNotExist:
            return JsonResponse({
                'error': f'Departemen {departemen_id} not found'
            }, status=404)
        
        # Get basic shift count
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=14)
        
        shift_count = Shift.objects.filter(
            departemen=departemen,
            is_active=True,
            tanggal_shift__range=[start_date, end_date]
        ).count()
        
        return JsonResponse({
            'success': True,
            'departemen': {
                'id': str(departemen.departemen_id),
                'nama': departemen.nama_departemen,
                'faskes': departemen.faskes.nama_faskes if departemen.faskes else 'No Faskes'
            },
            'shift_count': shift_count,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error in test_schedule_simple: {e}")
        return JsonResponse({
            'error': f'Error: {str(e)}'
        }, status=500)

# ===== MAIN VIEWS =====

def cari_tugas_view(request):
    """View untuk halaman cari tugas"""
    logger.info("=== CARI TUGAS VIEW STARTED ===")
    
    try:
        nakes = get_current_nakes()
        if not nakes:
            messages.error(request, "Nakes profile not found.")
            return redirect('management:nakes_profile')
        
        logger.info(f"Nakes: {nakes.nama_lengkap}")
        
        # Get faskes with available shifts (simplified query)
        faskes_with_shifts = Faskes.objects.filter(
            departemen__shifts__is_active=True,
            departemen__shifts__is_completed_by_faskes=False,
            departemen__shifts__tanggal_shift__gte=timezone.now().date()
        ).distinct().prefetch_related('departemen')

        
        logger.info(f"Found {faskes_with_shifts.count()} faskes with shifts")
        
        # Build faskes data
        faskes_data = []
        for faskes in faskes_with_shifts:
            departemen_with_shifts = []
            for departemen in faskes.departemen.all():
                # Count shifts for this departemen (simplified)
                shift_count = departemen.shifts.filter(
                    is_active=True,
                    is_completed_by_faskes=False,
                    tanggal_shift__gte=timezone.now().date()
                ).count()

                print(shift_count)
                
                if shift_count > 0:
                    departemen_with_shifts.append({
                        'departemen': departemen,
                        'shift_count': shift_count
                    })
            
            if departemen_with_shifts:
                # Set default tipe faskes
                if not hasattr(faskes, 'tipe_faskes') or not faskes.tipe_faskes:
                    faskes.tipe_faskes = 'Rumah Sakit'
                
                faskes_data.append({
                    'faskes': faskes,
                    'departemen_list': departemen_with_shifts
                })
        
        context = {
            'nakes': nakes,
            'faskes_data': faskes_data,
        }
        
        return render(request, 'cari_tugas.html', context)
        
    except Exception as e:
        logger.error(f"Error in cari_tugas_view: {e}", exc_info=True)
        messages.error(request, f"Error loading page: {str(e)}")
        return render(request, 'cari_tugas.html', {'nakes': None, 'faskes_data': []})

@require_http_methods(["GET"])
def get_departemen_schedule(request, departemen_id):
    """AJAX endpoint untuk mendapatkan jadwal departemen"""
    logger.info(f"=== GET DEPARTEMEN SCHEDULE: {departemen_id} ===")
    
    try:
        # Get nakes
        nakes = get_current_nakes()
        if not nakes:
            return JsonResponse({
                'error': 'Nakes tidak ditemukan'
            }, status=400)
        
        # Get departemen
        try:
            departemen = Departemen.objects.get(departemen_id=departemen_id)
        except Departemen.DoesNotExist:
            return JsonResponse({
                'error': 'Departemen tidak ditemukan'
            }, status=404)
        
        # Date range
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=14)
        
        # Get shifts (simplified query)
        shifts = Shift.objects.filter(
            departemen=departemen,
            is_active=True,
            is_completed_by_faskes=False,
            tanggal_shift__range=[start_date, end_date]
        ).order_by('tanggal_shift', 'jam_mulai')
        
        logger.info(f"Found {shifts.count()} shifts")
        
        # Format shifts data
        shifts_data = []
        for shift in shifts:
            try:
                shifts_data.append({
                    'shift_id': str(shift.shift_id),
                    'tanggal': shift.tanggal_shift.isoformat(),
                    'jam_mulai': shift.jam_mulai.strftime('%H:%M') if shift.jam_mulai else '08:00',
                    'jam_selesai': shift.jam_selesai.strftime('%H:%M') if shift.jam_selesai else '16:00',
                    'durasi_menit': shift.durasi_menit or 480,
                    'deskripsi_tugas': shift.deskripsi_tugas or f'Shift di {departemen.nama_departemen}',
                    'estimated_worth': float(shift.estimated_worth or 500000),
                })
            except Exception as e:
                logger.error(f"Error formatting shift {shift.shift_id}: {e}")
                continue
        
        response_data = {
            'success': True,
            'departemen': {
                'nama': departemen.nama_departemen,
                'faskes': departemen.faskes.nama_faskes if departemen.faskes else 'Unknown Faskes',
            },
            'shifts': shifts_data,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error in get_departemen_schedule: {e}", exc_info=True)
        return JsonResponse({
            'error': f'Server error: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def accept_shift_ajax(request, shift_id):
    """Accept shift endpoint"""
    logger.info(f"=== ACCEPT SHIFT: {shift_id} ===")
    
    try:
        nakes = get_current_nakes()
        if not nakes:
            return JsonResponse({'error': 'Nakes tidak ditemukan'}, status=400)

        shift = get_object_or_404(Shift, shift_id=shift_id)

        # Check availability
        if not shift.is_active:
            return JsonResponse({'error': 'Shift tidak aktif'}, status=400)
        
        # Check existing assignment
        existing = ShiftAssignment.objects.filter(
            shift=shift, 
            nakes=nakes, 
            status_assignment__in=['Pending', 'Accepted', 'Clocked In', 'Completed']
        ).first()
        
        if existing:
            return JsonResponse({'error': 'Anda sudah ditugaskan untuk shift ini'}, status=400)
        
        # Create assignment
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
        logger.error(f"Error accepting shift: {e}", exc_info=True)
        return JsonResponse({'error': f'Error: {str(e)}'}, status=500)

# ===== PROFILE VIEWS =====

def nakes_profile_view(request):
    """View untuk halaman profile nakes"""
    nakes = get_current_nakes()
    if not nakes:
        messages.error(request, "Nakes profile not found.")
        return redirect('authentication:login')

    if request.method == 'POST':
        # Handle profile update
        try:
            with transaction.atomic():
                # Update basic fields
                nakes.nama_lengkap = request.POST.get('nama_lengkap', nakes.nama_lengkap)
                nakes.nomor_telepon = request.POST.get('nomor_telepon', nakes.nomor_telepon)
                nakes.alamat = request.POST.get('alamat', nakes.alamat)
                
                if request.POST.get('tanggal_lahir'):
                    nakes.tanggal_lahir = request.POST.get('tanggal_lahir')
                
                nakes.jenis_kelamin = request.POST.get('jenis_kelamin', nakes.jenis_kelamin)
                nakes.profesi = request.POST.get('profesi', nakes.profesi)
                nakes.status = request.POST.get('status', nakes.status)
                nakes.nomor_registrasi = request.POST.get('nomor_registrasi', nakes.nomor_registrasi)
                
                if request.POST.get('tahun_pengalaman'):
                    nakes.tahun_pengalaman = int(request.POST.get('tahun_pengalaman', nakes.tahun_pengalaman))
                
                nakes.kategori_kualifikasi = request.POST.get('kategori_kualifikasi', nakes.kategori_kualifikasi)
                nakes.save()
                
                messages.success(request, "Profil berhasil diperbarui!")
                return redirect('management:nakes_profile')
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan: {str(e)}")
    
    context = {
        'nakes': nakes,
        'profesi_choices': PROFESI_CHOICES,
        'status_choices': STATUS_CHOICES,
        'jenis_kelamin_choices': JENIS_KELAMIN_CHOICES,
        'kategori_kualifikasi_choices': KATEGORI_KUALIFIKASI_CHOICES,
    }
    
    return render(request, 'nakes_profile.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def update_availability_ajax(request):
    """AJAX endpoint untuk update ketersediaan"""
    try:
        nakes = get_current_nakes()
        if not nakes:
            return JsonResponse({'error': 'Nakes not found'}, status=400)
        
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
    
    except Exception as e:
        logger.error(f"Error updating availability: {e}")
        return JsonResponse({'error': str(e)}, status=500)

# ===== HISTORY VIEWS =====

def nakes_histori_kinerja_view(request):
    """View untuk halaman histori kinerja nakes"""
    nakes = get_current_nakes()
    if not nakes:
        messages.error(request, "Nakes profile not found.")
        return redirect('management:nakes_profile')

    # Get completed assignments with reviews
    completed_assignments = ShiftAssignment.objects.filter(
        nakes=nakes,
        status_assignment='Completed'
    ).select_related(
        'shift__departemen__faskes',
        'shift__departemen'
    ).prefetch_related(
        'review_faskes'
    ).order_by('-waktu_clock_out')

    # Prepare data for template
    histori_data = []
    total_shifts = 0
    total_rating = 0
    total_earnings = 0

    for assignment in completed_assignments:
        # Get review if exists
        review = getattr(assignment, 'review_faskes', None)
        
        # Calculate statistics
        total_shifts += 1
        total_earnings += float(assignment.total_bayaran_nakes or 0)
        
        if review:
            total_rating += review.rating_kinerja

        # Format data for display
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

    # Group by month
    from collections import defaultdict
    from datetime import datetime
    
    grouped_histori = defaultdict(list)
    for item in histori_data:
        month_key = item['tanggal_shift'].strftime('%Y-%m')
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

def nakes_evaluasi_view(request):
    """View untuk halaman evaluasi kinerja nakes"""
    nakes = get_current_nakes()
    if not nakes:
        messages.error(request, "Nakes profile not found.")
        return redirect('management:nakes_profile')

    # Get completed assignments with reviews
    completed_assignments = ShiftAssignment.objects.filter(
        nakes=nakes,
        status_assignment='Completed'
    ).select_related(
        'shift__departemen__faskes',
        'shift__departemen'
    ).prefetch_related(
        'review_faskes'
    ).order_by('-waktu_clock_out')

    # Calculate statistics
    total_shifts = completed_assignments.count()
    total_hours = sum([assignment.shift.durasi_menit for assignment in completed_assignments]) / 60
    total_earnings = sum([float(assignment.total_bayaran_nakes or 0) for assignment in completed_assignments])
    
    # Rating statistics
    reviews = [assignment.review_faskes for assignment in completed_assignments if hasattr(assignment, 'review_faskes')]
    total_reviews = len(reviews)
    
    if total_reviews > 0:
        avg_rating = sum([review.rating_kinerja for review in reviews]) / total_reviews
    else:
        avg_rating = 0

    # Monthly performance data
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
    
    # Convert to list
    monthly_performance = []
    for month_key in sorted(monthly_data.keys()):
        data = monthly_data[month_key]
        avg_rating_month = data['total_rating'] / data['review_count'] if data['review_count'] > 0 else 0
        
        month_name = datetime.strptime(month_key, '%Y-%m').strftime('%b %Y')
        
        monthly_performance.append({
            'month': month_name,
            'month_key': month_key,
            'shifts': data['shifts'],
            'earnings': data['earnings'],
            'avg_rating': round(avg_rating_month, 2)
        })

    # Collect comments for AI summary
    all_comments = []
    for assignment in completed_assignments:
        if hasattr(assignment, 'review_faskes') and assignment.review_faskes.komentar:
            all_comments.append({
                'faskes': assignment.shift.departemen.faskes.nama_faskes,
                'departemen': assignment.shift.departemen.nama_departemen,
                'tanggal': assignment.shift.tanggal_shift,
                'rating': assignment.review_faskes.rating_kinerja,
                'komentar': assignment.review_faskes.komentar
            })

    # Generate AI summary
    ai_summary = None
    if all_comments:
        try:
            from .management_ai_services import get_gemini_summary
            ai_summary = get_gemini_summary(all_comments, nakes.nama_lengkap)
        except Exception as e:
            logger.error(f"Error generating AI summary: {e}")
            ai_summary = None

    # Recent performance (last 6 months)
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
        'monthly_performance': monthly_performance[-12:],  # Last 12 months
        'recent_performance': recent_performance,
        'ai_summary': ai_summary,
        'has_data': total_shifts > 0,
        'total_comments': len(all_comments),
    }
    
    return render(request, 'evaluasi.html', context)