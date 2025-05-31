# choices.py

KATEGORI_KUALIFIKASI_CHOICES = [
    # --- Kategori Umum Profesi ---
    ('Perawat Umum', 'Perawat Umum'),
    ('Perawat Gigi', 'Perawat Gigi'),
    ('Perawat Anestesi', 'Perawat Anestesi'),
    ('Perawat Bedah', 'Perawat Bedah'),
    ('Dokter Umum', 'Dokter Umum'),
    ('Dokter Gigi', 'Dokter Gigi'),
    ('Bidan', 'Bidan'),
    ('Analis Kesehatan', 'Analis Kesehatan'),
    ('Pranata Laboratorium Kesehatan', 'Pranata Laboratorium Kesehatan'),
    ('Apoteker', 'Apoteker'),
    ('Fisioterapis', 'Fisioterapis'),
    ('Radiografer', 'Radiografer'),
    ('Nutrisionis', 'Nutrisionis'),
    ('Dietisien', 'Dietisien'),
    ('Perekam Medis', 'Perekam Medis'),
    ('Tenaga Kesehatan Lingkungan', 'Tenaga Kesehatan Lingkungan'),
    ('Tenaga Promosi Kesehatan', 'Tenaga Promosi Kesehatan'),
    ('Tenaga Teknis Biomedika', 'Tenaga Teknis Biomedika'),
    ('Asisten Tenaga Kesehatan', 'Asisten Tenaga Kesehatan'),
    ('Volunteer Medis', 'Volunteer Medis'),

    # --- Kategori Spesialisasi Dokter/Profesi Lainnya ---
    ('Spesialis Anak', 'Spesialis Anak'),
    ('Spesialis Penyakit Dalam', 'Spesialis Penyakit Dalam'),
    ('Spesialis Bedah Umum', 'Spesialis Bedah Umum'),
    ('Spesialis Bedah Ortopedi', 'Spesialis Bedah Ortopedi'),
    ('Spesialis Bedah Plastik', 'Spesialis Bedah Plastik'),
    ('Spesialis Bedah Saraf', 'Spesialis Bedah Saraf'),
    ('Spesialis Obstetri & Ginekologi', 'Spesialis Obstetri & Ginekologi'),
    ('Spesialis Mata', 'Spesialis Mata'),
    ('Spesialis THT', 'Spesialis THT'),
    ('Spesialis Jantung & Pembuluh Darah', 'Spesialis Jantung & Pembuluh Darah'),
    ('Spesialis Saraf', 'Spesialis Saraf'),
    ('Spesialis Kulit & Kelamin', 'Spesialis Kulit & Kelamin'),
    ('Spesialis Anestesiologi & Terapi Intensif', 'Spesialis Anestesiologi & Terapi Intensif'),
    ('Spesialis Paru', 'Spesialis Paru'),
    ('Spesialis Kedokteran Fisik & Rehabilitasi', 'Spesialis Kedokteran Fisik & Rehabilitasi'),
    ('Spesialis Patologi Klinik', 'Spesialis Patologi Klinik'),
    ('Spesialis Radiologi', 'Spesialis Radiologi'),
    ('Spesialis Forensik & Medikolegal', 'Spesialis Forensik & Medikolegal'),
    ('Spesialis Kesehatan Jiwa', 'Spesialis Kesehatan Jiwa'),
    ('Spesialis Gizi Klinik', 'Spesialis Gizi Klinik'),
    ('Spesialis Farmakologi Klinik', 'Spesialis Farmakologi Klinik'),
    ('Spesialis Gigi Anak', 'Spesialis Gigi Anak'),
    ('Spesialis Orthodonsia', 'Spesialis Orthodonsia'),
    ('Spesialis Konservasi Gigi', 'Spesialis Konservasi Gigi'),
    ('Spesialis Periodonsia', 'Spesialis Periodonsia'),
    ('Spesialis Penyakit Mulut', 'Spesialis Penyakit Mulut'),
    ('Spesialis Bedah Mulut', 'Spesialis Bedah Mulut'),

    # --- Kategori Kompetensi & Sertifikasi Khusus ---
    ('Basic Life Support (BLS)', 'Basic Life Support (BLS)'),
    ('Advanced Cardiac Life Support (ACLS)', 'Advanced Cardiac Life Support (ACLS)'),
    ('Basic Trauma Life Support (BTLS)', 'Basic Trauma Life Support (BTLS)'),
    ('Advanced Trauma Life Support (ATLS)', 'Advanced Trauma Life Support (ATLS)'),
    ('Pelatihan Triase IGD', 'Pelatihan Triase IGD'),
    ('Sertifikasi Perawat ICU', 'Sertifikasi Perawat ICU'),
    ('Sertifikasi Perawat IGD', 'Sertifikasi Perawat IGD'),
    ('Sertifikasi Perawat Kamar Bedah', 'Sertifikasi Perawat Kamar Bedah'),
    ('Sertifikasi Perawat Hemodialisa', 'Sertifikasi Perawat Hemodialisa'),
    ('Sertifikasi Perawat Luka', 'Sertifikasi Perawat Luka'),
    ('Sertifikasi Phlebotomy', 'Sertifikasi Phlebotomy'),
    ('Sertifikasi EKG', 'Sertifikasi EKG'),
    ('Sertifikasi USG Dasar', 'Sertifikasi USG Dasar'),
    ('Pelatihan Resusitasi Neonatus', 'Pelatihan Resusitasi Neonatus'),
    ('Manajemen Nyeri', 'Manajemen Nyeri'),
    ('K3 Faskes', 'Kesehatan dan Keselamatan Kerja di Faskes'),
    ('Penanganan Bencana Medis', 'Penanganan Bencana Medis'),
    ('Pengendalian Infeksi (PPI)', 'Pengendalian Infeksi (PPI)'),
    ('Komunikasi Efektif', 'Komunikasi Efektif (untuk konseling pasien)'),
    ('Bahasa Inggris Medis', 'Keahlian Bahasa Inggris Medis'),
    ('Bahasa Mandarin Medis', 'Keahlian Bahasa Mandarin Medis'),

    # --- Kategori Manajemen / Administrasi ---
    ('Manajemen Faskes', 'Manajemen Faskes'),
    ('Quality Assurance Medis', 'Quality Assurance Medis'),
    ('Edukator Klinis', 'Edukator Klinis'),
]

STATUS_CHOICES = [
    ('Unavaiable', 'Unavaiable'),
    ('Menerima Konsul', 'Menerima Konsul'),
    ('Avaiable', 'Avaiable'),
]

PROFESI_CHOICES = [
    ('Perawat', 'Perawat'),
    ('Dokter Umum', 'Dokter Umum'),
    ('Bidan', 'Bidan'),
    ('Analis Laboratorium', 'Analis Laboratorium'),
    ('Dokter Gigi', 'Dokter Gigi'),
    ('Spesialis Anak', 'Spesialis Anak'),
    ('Spesialis Penyakit Dalam', 'Spesialis Penyakit Dalam'),
    ('Spesialis Bedah', 'Spesialis Bedah'),
    ('Spesialis Kandungan', 'Spesialis Kandungan'),
    ('Spesialis Mata', 'Spesialis Mata'),
    ('Spesialis THT', 'Spesialis THT'),
    ('Spesialis Jantung', 'Spesialis Jantung'),
    ('Spesialis Saraf', 'Spesialis Saraf'),
    ('Spesialis Kulit & Kelamin', 'Spesialis Kulit & Kelamin'),
    ('Spesialis Anastesi', 'Spesialis Anastesi'),
    ('Fisioterapis', 'Fisioterapis'), 
    ('Apoteker', 'Apoteker'), 
    ('Volunteer', 'Volunteer'),
]

JENIS_KELAMIN_CHOICES = [
        ('L', 'Laki-laki'),
        ('P', 'Perempuan'),
]

STATUS_ASSIGNMENT_CHOICES = [
    ('Pending', 'Pending (Menunggu Nakes menerima)'),
    ('Accepted', 'Accepted (Diterima Nakes)'),
    ('Rejected', 'Rejected (Ditolak Nakes)'),
    ('Clocked In', 'Clocked In'),
    ('Clocked Out', 'Clocked Out'),
    ('Completed', 'Completed (Tugas Selesai oleh Nakes)'), # Status setelah Clock Out
    ('Cancelled', 'Cancelled (Dibatalkan)'),
]

