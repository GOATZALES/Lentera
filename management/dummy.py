# management/dummy.py
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta, time
import random

from .models import Nakes, Faskes, Departemen, Shift, ShiftAssignment, ReviewNakes

def create_dummy_data():
    """Membuat data dummy untuk testing aplikasi"""
    print("Creating dummy data...")
    
    # 1. Create Users
    try:
        user_nakes = User.objects.get(username='nakes_histori_banyak')
    except User.DoesNotExist:
        user_nakes = User.objects.create_user(
            username='nakes_histori_banyak',
            email='budi.santoso@email.com',
            password='password123',
            first_name='Budi',
            last_name='Santoso'
        )
    
    # 2. Create Nakes
    try:
        nakes = Nakes.objects.get(user=user_nakes)
    except Nakes.DoesNotExist:
        nakes = Nakes.objects.create(
            user=user_nakes,
            nama_lengkap='Budi Santoso',
            nomor_telepon='08123456789',
            alamat='Jl. Kesehatan No. 123, Jakarta',
            tanggal_lahir=datetime(1990, 5, 15).date(),
            jenis_kelamin='L',
            profesi='Perawat',
            status='Avaiable',
            nomor_registrasi='STR123456789',
            tahun_pengalaman=5,
            kategori_kualifikasi='Perawat Umum',
            log_ketersediaan_menit=2400  # 40 jam
        )
    
    # 3. Create Faskes
    faskes_data = [
        {
            'nama': 'RS. Jakarta Medical Center',
            'alamat': 'Jl. Sudirman No. 1, Jakarta Pusat',
            'tipe': 'Rumah Sakit',
            'departemen': ['IGD', 'ICU', 'Bedah', 'Penyakit Dalam']
        },
        {
            'nama': 'Puskesmas Menteng',
            'alamat': 'Jl. Menteng Raya No. 45, Jakarta Pusat',
            'tipe': 'Puskesmas',
            'departemen': ['Poli Umum', 'KIA', 'Gigi']
        },
        {
            'nama': 'Klinik Sehat Bersama',
            'alamat': 'Jl. Kemang No. 88, Jakarta Selatan',
            'tipe': 'Klinik',
            'departemen': ['Poli Umum', 'Laboratorium']
        },
        {
            'nama': 'RS. Cipto Mangunkusumo',
            'alamat': 'Jl. Diponegoro No. 71, Jakarta Pusat',
            'tipe': 'Rumah Sakit',
            'departemen': ['IGD', 'ICU', 'Bedah', 'Anak', 'Kandungan']
        },
        {
            'nama': 'Klinik Pratama Sehat',
            'alamat': 'Jl. Gatot Subroto No. 123, Jakarta Selatan',
            'tipe': 'Klinik',
            'departemen': ['Poli Umum', 'Gigi', 'KIA']
        }
    ]
    
    created_faskes = []
    for faskes_info in faskes_data:
        faskes, created = Faskes.objects.get_or_create(
            nama_faskes=faskes_info['nama'],
            defaults={
                'alamat': faskes_info['alamat'],
                'tipe_faskes': faskes_info['tipe'],
                'nomor_telepon': f'021-{random.randint(1000000, 9999999)}',
                'email': f"admin@{faskes_info['nama'].lower().replace(' ', '').replace('.', '')}.com"
            }
        )
        created_faskes.append((faskes, faskes_info['departemen']))
    
    # 4. Create Departemen dan Shifts
    shift_templates = [
        {'jam_mulai': time(7, 0), 'jam_selesai': time(15, 0), 'durasi': 480},  # Pagi
        {'jam_mulai': time(15, 0), 'jam_selesai': time(23, 0), 'durasi': 480},  # Sore
        {'jam_mulai': time(23, 0), 'jam_selesai': time(7, 0), 'durasi': 480},  # Malam
        {'jam_mulai': time(8, 0), 'jam_selesai': time(12, 0), 'durasi': 240},  # Part-time pagi
        {'jam_mulai': time(13, 0), 'jam_selesai': time(17, 0), 'durasi': 240},  # Part-time sore
    ]
    
    profesi_choices = ['Perawat', 'Dokter Umum', 'Bidan']
    kualifikasi_choices = ['Perawat Umum', 'Perawat IGD', 'Perawat ICU', 'Dokter Umum', 'Bidan']
    
    for faskes, dept_names in created_faskes:
        for dept_name in dept_names:
            departemen, created = Departemen.objects.get_or_create(
                faskes=faskes,
                nama_departemen=dept_name,
                defaults={
                    'jam_buka': time(6, 0),
                    'jam_tutup': time(0, 0)
                }
            )
            
            # Create shifts for next 14 days
            start_date = timezone.now().date()
            for day_offset in range(14):
                shift_date = start_date + timedelta(days=day_offset)
                
                # Skip creating shifts for past dates
                if shift_date < start_date:
                    continue
                
                # Create 1-3 random shifts per day per departemen
                num_shifts = random.randint(1, 3)
                used_templates = random.sample(shift_templates, min(num_shifts, len(shift_templates)))
                
                for template in used_templates:
                    # Skip if shift already exists
                    if Shift.objects.filter(
                        departemen=departemen,
                        tanggal_shift=shift_date,
                        jam_mulai=template['jam_mulai']
                    ).exists():
                        continue
                    
                    shift = Shift.objects.create(
                        departemen=departemen,
                        profesi=random.choice(profesi_choices),
                        kategori_kualifikasi=random.choice(kualifikasi_choices),
                        jumlah_nakes_dibutuhkan=random.randint(1, 2),
                        tanggal_shift=shift_date,
                        jam_mulai=template['jam_mulai'],
                        jam_selesai=template['jam_selesai'],
                        durasi_menit=template['durasi'],
                        deskripsi_tugas=f"Tugas {dept_name} - {template['jam_mulai'].strftime('%H:%M')}-{template['jam_selesai'].strftime('%H:%M')}",
                        is_active=True,
                        is_completed_by_faskes=False
                    )
    
    # 5. Create historical assignments for evaluation data
    # Create more shifts for better evaluation data
    six_months_ago = timezone.now().date() - timedelta(days=180)
    ratings = [3, 3, 4, 4, 4, 5, 5, 5, 4, 3, 5, 4, 4, 5, 4]  # Variasi rating
    comments = [
        "Kinerja sangat baik, profesional dalam bekerja",
        "Tepat waktu dan sangat membantu tim",
        "Komunikasi baik dengan pasien dan keluarga",
        "Menunjukkan dedikasi tinggi selama shift",
        "Sangat kooperatif dan mudah diajak bekerja sama",
        "Penanganan pasien sangat hati-hati dan teliti",
        "Inisiatif bagus dalam membantu rekan kerja",
        "Dokumentasi medis rapi dan lengkap",
        "Respons cepat terhadap kondisi darurat",
        "Sikap empati tinggi kepada pasien",
        "Kepatuhan terhadap SOP sangat baik",
        "Kemampuan teknis di atas rata-rata",
        "Mampu bekerja di bawah tekanan dengan baik",
        "Koordinasi dengan tim sangat efektif",
        "Menunjukkan improvement yang konsisten"
    ]
    
    # Create 15 historical shifts dengan tanggal yang tersebar di 6 bulan terakhir
    for i in range(15):
        # Generate random date dalam 6 bulan terakhir
        random_days = random.randint(0, 180)
        shift_date = six_months_ago + timedelta(days=random_days)
        
        # Pick random faskes and departemen
        random_faskes, dept_names = random.choice(created_faskes)
        random_dept_name = random.choice(dept_names)
        
        # Get or create the departemen
        departemen, _ = Departemen.objects.get_or_create(
            faskes=random_faskes,
            nama_departemen=random_dept_name,
            defaults={
                'jam_buka': time(6, 0),
                'jam_tutup': time(0, 0)
            }
        )
        
        # Pick random shift template
        template = random.choice(shift_templates)
        
        # Create historical shift
        shift = Shift.objects.create(
            departemen=departemen,
            profesi=nakes.profesi,  # Match nakes profession
            kategori_kualifikasi=nakes.kategori_kualifikasi,  # Match nakes qualification
            jumlah_nakes_dibutuhkan=1,
            tanggal_shift=shift_date,
            jam_mulai=template['jam_mulai'],
            jam_selesai=template['jam_selesai'],
            durasi_menit=template['durasi'],
            deskripsi_tugas=f"Tugas {random_dept_name} - {template['jam_mulai'].strftime('%H:%M')}-{template['jam_selesai'].strftime('%H:%M')}",
            is_active=False,  # Historical shifts are not active
            is_completed_by_faskes=True
        )
        
        # Create assignment
        clock_in_time = timezone.make_aware(
            datetime.combine(shift.tanggal_shift, shift.jam_mulai)
        )
        clock_out_time = timezone.make_aware(
            datetime.combine(shift.tanggal_shift, shift.jam_selesai)
        )
        
        assignment = ShiftAssignment.objects.create(
            shift=shift,
            nakes=nakes,
            status_assignment='Completed',
            waktu_nakes_menerima=clock_in_time - timedelta(hours=random.randint(1, 48)),
            waktu_clock_in=clock_in_time,
            waktu_clock_out=clock_out_time,
            total_bayaran_nakes=shift.estimated_worth * random.uniform(0.8, 1.2),  # Variasi bayaran
            is_paid=True
        )
        
        # Create review for completed assignment
        ReviewNakes.objects.create(
            assignment=assignment,
            faskes=shift.departemen.faskes,
            nakes=nakes,
            rating_kinerja=ratings[i % len(ratings)],
            komentar=comments[i % len(comments)],
            tanggal_review=clock_out_time + timedelta(hours=random.randint(2, 72))
        )
    
    print("Dummy data created successfully!")
    print(f"Created Nakes: {nakes.nama_lengkap}")
    print(f"Created {len(created_faskes)} Faskes")
    print(f"Total Shifts: {Shift.objects.count()}")
    print(f"Historical Assignments: {ShiftAssignment.objects.filter(nakes=nakes, status_assignment='Completed').count()}")
    print(f"Reviews: {ReviewNakes.objects.filter(nakes=nakes).count()}")
    print(f"Available Shifts for {nakes.profesi} ({nakes.kategori_kualifikasi}): {Shift.objects.filter(profesi=nakes.profesi, kategori_kualifikasi=nakes.kategori_kualifikasi, is_active=True, tanggal_shift__gte=timezone.now().date()).count()}")

if __name__ == "__main__":
    create_dummy_data()