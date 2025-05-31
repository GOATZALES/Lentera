# faskes_views.py - Updated untuk menggunakan model yang sudah ada

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta
import json

from authentication.models import Departemen, Faskes
from .models import Nakes, Shift, ShiftAssignment, ReviewNakes, NakesSkill

def get_current_department():
    """
    Mengambil departemen untuk testing frontend departemen
    Menggunakan departemen IGD dari RS Jakarta Medical Center sebagai default
    """
    try:
        # Ambil departemen IGD dari RS Jakarta Medical Center
        # Berdasarkan pattern dari dummy data: admin_jmc001_igd
        user_to_load = User.objects.get(username='admin_jmc001_igd')
        departemen = Departemen.objects.get(user=user_to_load)
        return departemen
    except (User.DoesNotExist, Departemen.DoesNotExist):
        print("Departemen IGD RS Jakarta Medical Center tidak ditemukan. Mencoba departemen lain...")
        
        # Coba ambil departemen pertama yang ada
        try:
            departemen = Departemen.objects.first()
            if departemen:
                print(f"Menggunakan departemen: {departemen.nama_departemen} - {departemen.faskes.nama_faskes}")
                return departemen
        except:
            pass
        
        print("Tidak ada departemen yang ditemukan. Pastikan data dummy sudah dibuat.")
        print("Menjalankan create_dummy_data()...")
        create_dummy_data()
        
        # Coba lagi setelah membuat dummy data
        try:
            user_to_load = User.objects.get(username='admin_jmc001_igd')
            departemen = Departemen.objects.get(user=user_to_load)
            return departemen
        except (User.DoesNotExist, Departemen.DoesNotExist):
            # Jika masih gagal, ambil departemen pertama yang ada
            departemen = Departemen.objects.first()
            if departemen:
                print(f"Menggunakan departemen: {departemen.nama_departemen} - {departemen.faskes.nama_faskes}")
                return departemen
            else:
                raise Exception("Gagal membuat atau menemukan departemen dummy")

def departemen_dashboard(request):
    """
    Dashboard utama Departemen dengan overview operasional
    """
    try:
        departemen = request.user.departemen
    except Departemen.DoesNotExist:
        messages.error(request, 'Akses ditolak. Anda bukan Departemen yang terdaftar.')
        return redirect('authentication:login')
    
    # Statistics untuk dashboard
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    stats = {
        'total_shifts_active': Shift.objects.filter(
            departemen=departemen,
            tanggal_shift__gte=today,
            is_active=True
        ).count(),
        
        'pending_assignments': ShiftAssignment.objects.filter(
            shift__departemen=departemen,
            status_assignment='Pending'
        ).count(),
        
        'nakes_registered': Nakes.objects.filter(
            # Nakes yang pernah ditugaskan ke departemen ini
            assigned_shifts__shift__departemen=departemen
        ).distinct().count(),
        
        'shifts_this_week': Shift.objects.filter(
            departemen=departemen,
            tanggal_shift__range=[week_start, week_end]
        ).count(),
        
        'occupancy_rate': calculate_occupancy_rate(departemen),
        'urgent_shifts': get_urgent_shifts(departemen),
    }
    
    # Recent activities
    recent_activities = get_recent_activities(departemen)
    
    # Pending actions yang butuh perhatian
    pending_actions = {
        'new_assignments': ShiftAssignment.objects.filter(
            shift__departemen=departemen,
            status_assignment='Pending',
            waktu_penugasan__gte=today
        ).count(),
        
        'shift_conflicts': check_shift_conflicts(departemen),
        'unfilled_shifts': get_unfilled_shifts(departemen),
    }
    
    context = {
        'departemen': departemen,
        'stats': stats,
        'recent_activities': recent_activities,
        'pending_actions': pending_actions,
        'page_title': 'Dashboard Departemen'
    }
    
    return render(request, 'management/departemen_dashboard.html', context)

def kelola_lamaran(request):
    
    try:
        departemen = get_current_department()
    except Departemen.DoesNotExist:
        messages.error(request, 'Akses ditolak. Anda bukan Departemen yang terdaftar.')
        return redirect('management:login')
    
    # Filter assignments
    status_filter = request.GET.get('status', 'all')
    shift_filter = request.GET.get('shift', 'all')
    date_filter = request.GET.get('date', 'all')
    
    assignments = ShiftAssignment.objects.filter(
        shift__departemen=departemen
    ).select_related('nakes', 'shift').order_by('-waktu_penugasan')
    
    if status_filter != 'all':
        assignments = assignments.filter(status_assignment=status_filter)
    
    if shift_filter != 'all':
        assignments = assignments.filter(shift_id=shift_filter)
        
    if date_filter == 'today':
        assignments = assignments.filter(waktu_penugasan__date=timezone.now().date())
    elif date_filter == 'week':
        week_start = timezone.now().date() - timedelta(days=7)
        assignments = assignments.filter(waktu_penugasan__date__gte=week_start)
    
    # Available shifts untuk filter
    available_shifts = Shift.objects.filter(
        departemen=departemen,
        tanggal_shift__gte=timezone.now().date()
    ).order_by('tanggal_shift', 'jam_mulai')
    
    # Statistics
    assignment_stats = {
        'total': assignments.count(),
        'pending': assignments.filter(status_assignment='Pending').count(),
        'accepted': assignments.filter(status_assignment='Accepted').count(),
        'completed': assignments.filter(status_assignment='Completed').count(),
        'cancelled': assignments.filter(status_assignment='Cancelled').count(),
    }
    
    context = {
        'departemen': departemen,
        'assignments': assignments,
        'available_shifts': available_shifts,
        'assignment_stats': assignment_stats,
        'current_filters': {
            'status': status_filter,
            'shift': shift_filter,
            'date': date_filter,
        },
        'page_title': 'Kelola Penugasan'
    }
    
    return render(request, 'kelola_lamaran.html', context)

def process_assignment(request, assignment_id):
    """
    Proses perubahan status assignment
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        departemen = request.user.departemen
    except Departemen.DoesNotExist:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    assignment = get_object_or_404(
        ShiftAssignment,
        assignment_id=assignment_id,
        shift__departemen=departemen
    )
    
    action = request.POST.get('action')
    notes = request.POST.get('notes', '')
    
    if action == 'cancel':
        if assignment.status_assignment in ['Pending', 'Accepted']:
            assignment.status_assignment = 'Cancelled'
            assignment.save()
            
            messages.success(request, f'Penugasan {assignment.nakes.nama_lengkap} telah dibatalkan')
        else:
            return JsonResponse({
                'error': 'Assignment tidak dapat dibatalkan'
            }, status=400)
            
    elif action == 'complete':
        if assignment.status_assignment == 'Accepted':
            assignment.status_assignment = 'Completed'
            assignment.waktu_clock_out = timezone.now()
            
            # Calculate payment
            shift_duration = assignment.shift.durasi_menit
            assignment.total_bayaran_nakes = assignment.shift.estimated_worth
            assignment.save()
            
            # Add to Nakes log ketersediaan
            assignment.nakes.add_ketersediaan_menit(shift_duration)
            
            messages.success(request, f'Shift {assignment.nakes.nama_lengkap} telah selesai')
        else:
            return JsonResponse({
                'error': 'Assignment tidak dapat diselesaikan'
            }, status=400)
    
    else:
        return JsonResponse({'error': 'Invalid action'}, status=400)
    
    return JsonResponse({'success': True})

def kelola_shift(request):
    """
    Kelola shift yang dibuat oleh departemen
    """
    try:
        departemen = get_current_department()
    except Departemen.DoesNotExist:
        messages.error(request, 'Akses ditolak. Anda bukan Departemen yang terdaftar.')
        return redirect('authentication:login')
    
    if request.method == 'POST':
        # Create new shift
        return create_shift(request, departemen)
    
    # Get shifts dengan filter
    date_filter = request.GET.get('date', 'upcoming')
    status_filter = request.GET.get('status', 'all')
    
    shifts = Shift.objects.filter(departemen=departemen)
    
    if date_filter == 'today':
        shifts = shifts.filter(tanggal_shift=timezone.now().date())
    elif date_filter == 'upcoming':
        shifts = shifts.filter(tanggal_shift__gte=timezone.now().date())
    elif date_filter == 'past':
        shifts = shifts.filter(tanggal_shift__lt=timezone.now().date())
    
    if status_filter == 'active':
        shifts = shifts.filter(is_active=True)
    elif status_filter == 'inactive':
        shifts = shifts.filter(is_active=False)
    
    shifts = shifts.order_by('tanggal_shift', 'jam_mulai')
    
    # Annotate dengan assignment count
    shifts = shifts.annotate(
        assignment_count=Count('assignments'),
        filled_count=Count('assignments', filter=Q(assignments__status_assignment='Accepted'))
    )
    
    # Shift statistics
    shift_summary = {
        'total': shifts.count(),
        'active': shifts.filter(is_active=True).count(),
        'completed': shifts.filter(is_completed_by_faskes=True).count(),
        'unfilled': shifts.filter(is_active=True, assignments__isnull=True).count(),
    }
    
    context = {
        'departemen': departemen,
        'shifts': shifts,
        'shift_summary': shift_summary,
        'current_filters': {
            'date': date_filter,
            'status': status_filter,
        },
        'page_title': 'Kelola Shift'
    }
    
    return render(request, 'management_shift.html', context)

def laporan_departemen(request):
    """
    Laporan dan analytics untuk departemen
    """
    try:
        departemen = request.user.departemen
    except Departemen.DoesNotExist:
        messages.error(request, 'Akses ditolak. Anda bukan Departemen yang terdaftar.')
        return redirect('management:login')
    
    # Date range untuk laporan
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)  # Default 30 hari terakhir
    
    if request.GET.get('start_date'):
        start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
    if request.GET.get('end_date'):
        end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
    
    # Shift statistics
    shift_stats = {
        'total_shifts': Shift.objects.filter(
            departemen=departemen,
            tanggal_shift__range=[start_date, end_date]
        ).count(),
        
        'filled_shifts': ShiftAssignment.objects.filter(
            shift__departemen=departemen,
            shift__tanggal_shift__range=[start_date, end_date],
            status_assignment='Accepted'
        ).count(),
        
        'completed_shifts': ShiftAssignment.objects.filter(
            shift__departemen=departemen,
            shift__tanggal_shift__range=[start_date, end_date],
            status_assignment='Completed'
        ).count(),
    }
    
    if shift_stats['total_shifts'] > 0:
        shift_stats['fill_rate'] = (shift_stats['filled_shifts'] / shift_stats['total_shifts'] * 100)
        shift_stats['completion_rate'] = (shift_stats['completed_shifts'] / shift_stats['total_shifts'] * 100)
    else:
        shift_stats['fill_rate'] = 0
        shift_stats['completion_rate'] = 0
    
    # Assignment statistics
    assignment_stats = get_assignment_statistics(departemen, start_date, end_date)
    
    # Nakes performance
    nakes_performance = get_nakes_performance(departemen, start_date, end_date)
    
    # Review statistics
    review_stats = get_review_statistics(departemen, start_date, end_date)
    
    context = {
        'departemen': departemen,
        'shift_stats': shift_stats,
        'assignment_stats': assignment_stats,
        'nakes_performance': nakes_performance,
        'review_stats': review_stats,
        'date_range': {
            'start': start_date,
            'end': end_date
        },
        'page_title': 'Laporan Departemen'
    }
    
    return render(request, 'management_departemen.html', context)

# Utility functions
def calculate_occupancy_rate(departemen):
    """Calculate occupancy rate for departemen"""
    total_shifts = Shift.objects.filter(departemen=departemen, is_active=True).count()
    filled_shifts = ShiftAssignment.objects.filter(
        shift__departemen=departemen,
        status_assignment='Accepted'
    ).count()
    return (filled_shifts / total_shifts * 100) if total_shifts > 0 else 0

def get_urgent_shifts(departemen):
    """Get shifts yang urgent (besok dan belum ada assignment)"""
    tomorrow = timezone.now().date() + timedelta(days=1)
    return Shift.objects.filter(
        departemen=departemen,
        tanggal_shift=tomorrow,
        is_active=True,
        assignments__isnull=True
    ).count()

def get_unfilled_shifts(departemen):
    """Get shifts yang belum terisi"""
    return Shift.objects.filter(
        departemen=departemen,
        tanggal_shift__gte=timezone.now().date(),
        is_active=True,
        assignments__isnull=True
    ).count()

def get_recent_activities(departemen):
    """Get recent activities untuk departemen"""
    activities = []
    
    # Recent assignments
    recent_assignments = ShiftAssignment.objects.filter(
        shift__departemen=departemen,
        waktu_penugasan__gte=timezone.now() - timedelta(days=7)
    ).order_by('-waktu_penugasan')[:5]
    
    for assignment in recent_assignments:
        activities.append({
            'type': 'assignment',
            'icon': 'fa-user-plus',
            'title': f'{assignment.nakes.nama_lengkap} ditugaskan',
            'description': f'{assignment.shift.profesi} - {assignment.shift.tanggal_shift}',
            'time': assignment.waktu_penugasan,
            'status': assignment.status_assignment
        })
    
    # Recent reviews
    recent_reviews = ReviewNakes.objects.filter(
        assignment__shift__departemen=departemen,
        tanggal_review__gte=timezone.now() - timedelta(days=7)
    ).order_by('-tanggal_review')[:3]
    
    for review in recent_reviews:
        activities.append({
            'type': 'review',
            'icon': 'fa-star',
            'title': f'Review untuk {review.nakes.nama_lengkap}',
            'description': f'Rating: {review.rating_kinerja}/5',
            'time': review.tanggal_review,
            'status': 'completed'
        })
    
    return sorted(activities, key=lambda x: x['time'], reverse=True)[:10]

def check_shift_conflicts(departemen):
    """Check for potential shift conflicts"""
    # Implementation untuk detect conflicts
    return 0

def get_assignment_statistics(departemen, start_date, end_date):
    """Get assignment statistics for reporting"""
    assignments = ShiftAssignment.objects.filter(
        shift__departemen=departemen,
        waktu_penugasan__date__range=[start_date, end_date]
    )
    
    return {
        'total': assignments.count(),
        'pending': assignments.filter(status_assignment='Pending').count(),
        'accepted': assignments.filter(status_assignment='Accepted').count(),
        'completed': assignments.filter(status_assignment='Completed').count(),
        'cancelled': assignments.filter(status_assignment='Cancelled').count(),
    }

def get_nakes_performance(departemen, start_date, end_date):
    """Get top performing Nakes"""
    return Nakes.objects.filter(
        assigned_shifts__shift__departemen=departemen,
        assigned_shifts__shift__tanggal_shift__range=[start_date, end_date]
    ).annotate(
        shifts_completed=Count('assigned_shifts', filter=Q(assigned_shifts__status_assignment='Completed')),
        avg_rating=Avg('reviews_received__rating_kinerja')
    ).order_by('-shifts_completed')[:10]

def get_review_statistics(departemen, start_date, end_date):
    """Get review statistics"""
    reviews = ReviewNakes.objects.filter(
        assignment__shift__departemen=departemen,
        tanggal_review__date__range=[start_date, end_date]
    )
    
    return {
        'total_reviews': reviews.count(),
        'avg_rating': reviews.aggregate(avg=Avg('rating_kinerja'))['avg'] or 0,
        'rating_distribution': {
            '5': reviews.filter(rating_kinerja=5).count(),
            '4': reviews.filter(rating_kinerja=4).count(),
            '3': reviews.filter(rating_kinerja=3).count(),
            '2': reviews.filter(rating_kinerja=2).count(),
            '1': reviews.filter(rating_kinerja=1).count(),
        }
    }

def create_shift(request, departemen):
    """Create new shift"""
    # Implementation untuk create shift
    messages.success(request, 'Shift berhasil dibuat')
    return redirect('management:kelola_shift')
