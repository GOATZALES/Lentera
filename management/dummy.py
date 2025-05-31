# management/dummy.py
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta, time
import random
import uuid

from .models import Nakes, Shift, ShiftAssignment, ReviewNakes
from authentication.models import Faskes, Departemen

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
            status='Available',  # Perbaiki typo 'Avaiable' -> 'Available'
            nomor_registrasi='STR123456789',
            tahun_pengalaman=5,
            kategori_kualifikasi='Perawat Umum',
            log_ketersediaan_menit=2400  # 40 jam
        )
    
    # 3. Create Faskes - Sesuaikan dengan struktur model yang baru
    faskes_data = [
        {
            'faskes_id_internal': 'JMC001',
            'nama': 'RS. Jakarta Medical Center',
            'jenis': 'Rumah Sakit Umum',
            'alamat_jalan': 'Jl. Sudirman No. 1',
            'alamat_kelurahan_desa': 'Karet Tengsin',
            'alamat_kecamatan': 'Tanah Abang',
            'alamat_kota_kabupaten': 'Jakarta Pusat',
            'alamat_provinsi': 'DKI Jakarta',
            'alamat_kode_pos': '10220',
            'departemen': ['IGD', 'ICU', 'Bedah', 'Penyakit Dalam']
        },
        {
            'faskes_id_internal': 'PMT001',
            'nama': 'Puskesmas Menteng',
            'jenis': 'Puskesmas',
            'alamat_jalan': 'Jl. Menteng Raya No. 45',
            'alamat_kelurahan_desa': 'Menteng',
            'alamat_kecamatan': 'Menteng',
            'alamat_kota_kabupaten': 'Jakarta Pusat',
            'alamat_provinsi': 'DKI Jakarta',
            'alamat_kode_pos': '10310',
            'departemen': ['Poli Umum', 'KIA', 'Gigi']
        },
        {
            'faskes_id_internal': 'KSB001',
            'nama': 'Klinik Sehat Bersama',
            'jenis': 'Klinik Pratama',
            'alamat_jalan': 'Jl. Kemang No. 88',
            'alamat_kelurahan_desa': 'Kemang Selatan',
            'alamat_kecamatan': 'Mampang Prapatan',
            'alamat_kota_kabupaten': 'Jakarta Selatan',
            'alamat_provinsi': 'DKI Jakarta',
            'alamat_kode_pos': '12560',
            'departemen': ['Poli Umum', 'Laboratorium']
        },
        {
            'faskes_id_internal': 'RSCM001',
            'nama': 'RS. Cipto Mangunkusumo',
            'jenis': 'Rumah Sakit Umum',
            'alamat_jalan': 'Jl. Diponegoro No. 71',
            'alamat_kelurahan_desa': 'Kenari',
            'alamat_kecamatan': 'Senen',
            'alamat_kota_kabupaten': 'Jakarta Pusat',
            'alamat_provinsi': 'DKI Jakarta',
            'alamat_kode_pos': '10430',
            'departemen': ['IGD', 'ICU', 'Bedah', 'Anak', 'Kandungan']
        },
        {
            'faskes_id_internal': 'KPS001',
            'nama': 'Klinik Pratama Sehat',
            'jenis': 'Klinik Pratama',
            'alamat_jalan': 'Jl. Gatot Subroto No. 123',
            'alamat_kelurahan_desa': 'Kuningan Timur',
            'alamat_kecamatan': 'Setiabudi',
            'alamat_kota_kabupaten': 'Jakarta Selatan',
            'alamat_provinsi': 'DKI Jakarta',
            'alamat_kode_pos': '12950',
            'departemen': ['Poli Umum', 'Gigi', 'KIA']
        }
    ]
    
    created_faskes = []
    for faskes_info in faskes_data:
        faskes, created = Faskes.objects.get_or_create(
            faskes_id_internal=faskes_info['faskes_id_internal'],
            defaults={
                'nama_faskes': faskes_info['nama'],
                'jenis_faskes': faskes_info['jenis'],
                'alamat_jalan': faskes_info['alamat_jalan'],
                'alamat_kelurahan_desa': faskes_info['alamat_kelurahan_desa'],
                'alamat_kecamatan': faskes_info['alamat_kecamatan'],
                'alamat_kota_kabupaten': faskes_info['alamat_kota_kabupaten'],
                'alamat_provinsi': faskes_info['alamat_provinsi'],
                'alamat_kode_pos': faskes_info['alamat_kode_pos'],
                'koordinat_latitude': -6.2 + random.uniform(-0.1, 0.1),  # Random Jakarta coordinates
                'koordinat_longitude': 106.8 + random.uniform(-0.1, 0.1),
                'nomor_izin_operasional': f"IZN-{faskes_info['faskes_id_internal']}-2024",
                'pic_nama': f"Dr. Admin {faskes_info['nama'].split('.')[1] if '.' in faskes_info['nama'] else faskes_info['nama']}",
                'pic_telepon': f'021-{random.randint(1000000, 9999999)}',
                'pic_email': f"admin@{faskes_info['faskes_id_internal'].lower()}.com",
                'ops_hari': 'Senin - Minggu',
                'ops_jam_buka': time(6, 0),
                'ops_jam_tutup': time(23, 59),
                'ops_catatan': 'Layanan 24/7 untuk IGD',
                'kapasitas_info_json': {
                    'tempat_tidur': random.randint(50, 200),
                    'poli_aktif': len(faskes_info['departemen'])
                },
                'layanan_unggulan_json': faskes_info['departemen'][:2],  # First 2 departments as featured
                'is_active_partner': True
            }
        )
        created_faskes.append((faskes, faskes_info['departemen']))
        if created:
            print(f"Created Faskes: {faskes.nama_faskes}")
    
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
            # Create department user
            dept_username = f"admin_{faskes.faskes_id_internal.lower()}_{dept_name.lower().replace(' ', '')}"
            departemen_user, user_created = User.objects.get_or_create(
                username=dept_username,
                defaults={
                    'email': f"{dept_username}@example.com",
                    'first_name': f"{dept_name} Admin",
                    'last_name': f"{faskes.nama_faskes}"
                }
            )
            
            # Set password for new users
            if user_created:
                departemen_user.set_password('password123')
                departemen_user.save()
            
            # Create departemen
            departemen, created = Departemen.objects.get_or_create(
                user=departemen_user,
                defaults={
                    'faskes': faskes,
                    'nama_departemen': dept_name,
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
        
        # Get or create the departemen user first
        dept_username = f"admin_{random_faskes.faskes_id_internal.lower()}_{random_dept_name.lower().replace(' ', '')}"
        departemen_user, user_created = User.objects.get_or_create(
            username=dept_username,
            defaults={
                'email': f"{dept_username}@example.com",
                'first_name': f"{random_dept_name} Admin",
                'last_name': f"{random_faskes.nama_faskes}"
            }
        )
        
        if user_created:
            departemen_user.set_password('password123')
            departemen_user.save()
        
        # Get or create the departemen
        departemen, _ = Departemen.objects.get_or_create(
            user=departemen_user,
            defaults={
                'faskes': random_faskes,
                'nama_departemen': random_dept_name,
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
        
        # Handle cross-midnight shifts
        if shift.jam_selesai < shift.jam_mulai:
            clock_out_time += timedelta(days=1)
        
        assignment = ShiftAssignment.objects.create(
            shift=shift,
            nakes=nakes,
            status_assignment='Completed',
            waktu_penugasan=clock_in_time - timedelta(hours=random.randint(1, 48)),
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