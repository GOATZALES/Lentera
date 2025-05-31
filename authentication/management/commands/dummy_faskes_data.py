import random
import datetime
from dateutil.relativedelta import relativedelta

# Initial data (first 2 entries)
DUMMY_FASKES_DATA = [
    {
        "faskes_id_internal": "FKS001-JKTSEL", # ID unik internal kita
        "nama_faskes": "Klinik Sehat Keluarga Bintaro",
        "jenis_faskes": "Klinik Pratama",
        "alamat_lengkap": {
            "jalan": "Jl. Kesehatan Raya No. 123, Sektor 9",
            "kelurahan_desa": "Pondok Pucung",
            "kecamatan": "Pondok Aren",
            "kota_kabupaten": "Tangerang Selatan",
            "provinsi": "Banten",
            "kode_pos": "15229"
        },
        "koordinat": {"latitude": -6.2830, "longitude": 106.7100},
        "nomor_izin_operasional": "IZN/KLN/001/VII/2022",
        "kontak_pic": {
            "nama": "Dr. Anisa Rahmawati",
            "telepon": "081234567001",
            "email": "pic.klinikbintaro@example.com"
        },
        "jam_operasional": {
            "hari": "Senin - Sabtu",
            "jam_buka": "08:00",
            "jam_tutup": "21:00",
            "catatan": "Minggu dan hari libur nasional tutup, kecuali perjanjian."
        },
        "kapasitas": {
            "poli_aktif": 3, # Poli Umum, Poli Gigi, KIA
            "ruang_periksa": 5
        },
        "layanan_unggulan": ["Poli Umum", "Poli Gigi", "KIA & Imunisasi", "Laboratorium Sederhana"],
        "historis_kunjungan_bulanan": [ # 12 bulan terakhir
            {"bulan_tahun": "2023-07", "total_kunjungan": 650},
            {"bulan_tahun": "2023-08", "total_kunjungan": 700},
            {"bulan_tahun": "2023-09", "total_kunjungan": 720}, # Pancaroba
            {"bulan_tahun": "2023-10", "total_kunjungan": 680},
            {"bulan_tahun": "2023-11", "total_kunjungan": 600},
            {"bulan_tahun": "2023-12", "total_kunjungan": 750}, # Liburan akhir tahun
            {"bulan_tahun": "2024-01", "total_kunjungan": 800}, # Awal tahun, musim hujan
            {"bulan_tahun": "2024-02", "total_kunjungan": 780},
            {"bulan_tahun": "2024-03", "total_kunjungan": 820}, # Musim DBD
            {"bulan_tahun": "2024-04", "total_kunjungan": 700}, # Lebaran
            {"bulan_tahun": "2024-05", "total_kunjungan": 650},
            {"bulan_tahun": "2024-06", "total_kunjungan": 670},
        ],
        "rata_kunjungan_harian_seminggu": { # Rata-rata
            "Senin": 30, "Selasa": 35, "Rabu": 30, "Kamis": 35, "Jumat": 25, "Sabtu": 40, "Minggu": 0
        },
        "pola_kunjungan_layanan": { # Rata-rata per hari
            "Poli Umum": 20, "Poli Gigi": 8, "KIA & Imunisasi": 7, "Laboratorium": 5
        },
        "periode_puncak_diketahui": [
            "Januari-Maret (Musim Hujan/DBD)",
            "September-Oktober (Pancaroba, ISPA)",
            "Minggu ke-4 Desember (Libur Akhir Tahun)"
        ],
        "historis_klb_lokal": [
            # {"jenis_klb": "Wabah Diare", "periode": "2023-02-15 hingga 2023-02-28", "lonjakan_pasien_harian": 20}
        ],
        "baseline_staffing": { # Rata-rata per shift atau per hari
            "Dokter Umum": {"pagi": 1, "sore": 1, "malam": 0},
            "Dokter Gigi": {"pagi": 1, "sore": 0, "malam": 0}, # Biasanya praktek jam tertentu
            "Perawat": {"pagi": 2, "sore": 1, "malam": 0},
            "Bidan": {"pagi": 1, "sore": 0, "malam": 0} # Sesuai jam KIA
        }
    },
    {
        "faskes_id_internal": "FKS002-BDGKOTA",
        "nama_faskes": "RS Harapan Bunda Bandung",
        "jenis_faskes": "Rumah Sakit Tipe C",
        "alamat_lengkap": {
            "jalan": "Jl. Pahlawan No. 45",
            "kelurahan_desa": "Sukaluyu",
            "kecamatan": "Cibeunying Kaler",
            "kota_kabupaten": "Kota Bandung",
            "provinsi": "Jawa Barat",
            "kode_pos": "40123"
        },
        "koordinat": {"latitude": -6.8937, "longitude": 107.6303},
        "nomor_izin_operasional": "IZN/RS/015/XI/2021",
        "kontak_pic": {
            "nama": "Bapak Hendra Wijaya (Manajer Operasional)",
            "telepon": "081234567002",
            "email": "operasional.rsharapanbunda@example.com"
        },
        "jam_operasional": {"hari": "Senin - Minggu", "jam_buka": "00:00", "jam_tutup": "23:59", "catatan": "UGD 24 Jam"},
        "kapasitas": {"jumlah_tempat_tidur_total": 120, "poli_aktif": 10, "ruang_periksa_ugd": 5, "ruang_periksa_poli": 15},
        "layanan_unggulan": ["UGD 24 Jam", "Rawat Inap Umum", "Bedah Minor", "Poli Anak", "Poli Penyakit Dalam", "Radiologi"],
        "historis_kunjungan_bulanan": [
            {"bulan_tahun": "2023-07", "total_kunjungan": 3200},
            {"bulan_tahun": "2023-08", "total_kunjungan": 3300},
            {"bulan_tahun": "2023-09", "total_kunjungan": 3500},
            {"bulan_tahun": "2023-10", "total_kunjungan": 3400},
            {"bulan_tahun": "2023-11", "total_kunjungan": 3100},
            {"bulan_tahun": "2023-12", "total_kunjungan": 3800},
            {"bulan_tahun": "2024-01", "total_kunjungan": 4000},
            {"bulan_tahun": "2024-02", "total_kunjungan": 3900},
            {"bulan_tahun": "2024-03", "total_kunjungan": 4100},
            {"bulan_tahun": "2024-04", "total_kunjungan": 3500},
            {"bulan_tahun": "2024-05", "total_kunjungan": 3300},
            {"bulan_tahun": "2024-06", "total_kunjungan": 3400},
        ],
        "rata_kunjungan_harian_seminggu": {
            "Senin": 120, "Selasa": 130, "Rabu": 125, "Kamis": 130, "Jumat": 110, "Sabtu": 150, "Minggu": 140
        },
        "pola_kunjungan_layanan": { # Rata-rata per hari
            "UGD": 40, "Rawat Jalan Poli Umum": 50, "Rawat Jalan Poli Anak": 20, "Rawat Jalan Poli Dalam": 15
        },
        "periode_puncak_diketahui": ["Musim Liburan Sekolah (Juni-Juli, Desember-Januari)", "Musim Dingin/Hujan (November-Februari, banyak kasus pernapasan)"],
        "historis_klb_lokal": [
            {"jenis_klb": "KLB Campak", "periode": "2023-10-01 hingga 2023-10-20", "lonjakan_pasien_harian_anak": 15}
        ],
        "baseline_staffing": {
            "Dokter Umum (UGD)": {"pagi": 2, "sore": 2, "malam": 1},
            "Dokter Umum (Poli)": {"pagi": 3, "sore": 2, "malam": 0},
            "Dokter Spesialis Anak": {"pagi": 1, "sore": 1, "malam": 0, "catatan": "On-call malam"},
            "Perawat (UGD)": {"pagi": 4, "sore": 4, "malam": 3},
            "Perawat (Rawat Inap)": {"pagi": 8, "sore": 8, "malam": 6},
            "Perawat (Poli)": {"pagi": 5, "sore": 4, "malam": 0}
        }
    }
]

# --- Helper data and functions ---

# (A more extensive list would be better for true variety)
kota_data = [
    {"nama": "Kota Surabaya", "provinsi": "Jawa Timur", "kode_area": "SBY", "lat_range": (-7.20, -7.35), "lon_range": (112.65, 112.80)},
    {"nama": "Kota Medan", "provinsi": "Sumatera Utara", "kode_area": "MDN", "lat_range": (3.50, 3.70), "lon_range": (98.60, 98.75)},
    {"nama": "Kota Makassar", "provinsi": "Sulawesi Selatan", "kode_area": "MKR", "lat_range": (-5.05, -5.20), "lon_range": (119.35, 119.50)},
    {"nama": "Kabupaten Sleman", "provinsi": "DI Yogyakarta", "kode_area": "SLMN", "lat_range": (-7.60, -7.80), "lon_range": (110.30, 110.50)},
    {"nama": "Kota Denpasar", "provinsi": "Bali", "kode_area": "DPS", "lat_range": (-8.60, -8.70), "lon_range": (115.18, 115.28)},
    {"nama": "Kota Palembang", "provinsi": "Sumatera Selatan", "kode_area": "PLM", "lat_range": (-2.90, -3.05), "lon_range": (104.65, 104.85)},
    {"nama": "Kota Semarang", "provinsi": "Jawa Tengah", "kode_area": "SMG", "lat_range": (-6.95, -7.05), "lon_range": (110.35, 110.45)},
    {"nama": "Kabupaten Badung", "provinsi": "Bali", "kode_area": "BDGBL", "lat_range": (-8.30, -8.80), "lon_range": (115.05, 115.25)},
    {"nama": "Kota Balikpapan", "provinsi": "Kalimantan Timur", "kode_area": "BPN", "lat_range": (-1.10, -1.30), "lon_range": (116.75, 116.95)},
    {"nama": "Kabupaten Jayapura", "provinsi": "Papua", "kode_area": "JPR", "lat_range": (-2.40, -2.70), "lon_range": (139.80, 140.70)},
    {"nama": "Kota Manado", "provinsi": "Sulawesi Utara", "kode_area": "MND", "lat_range": (1.40, 1.55), "lon_range": (124.78, 124.92)},
    {"nama": "Kota Padang", "provinsi": "Sumatera Barat", "kode_area": "PDG", "lat_range": (-0.80, -1.05), "lon_range": (100.25, 100.50)},
    {"nama": "Kabupaten Lombok Barat", "provinsi": "Nusa Tenggara Barat", "kode_area": "LOBAR", "lat_range": (-8.40, -8.85), "lon_range": (115.85, 116.30)},
    {"nama": "Kota Pontianak", "provinsi": "Kalimantan Barat", "kode_area": "PTK", "lat_range": (-0.10, 0.05), "lon_range": (109.25, 109.40)},
     {"nama": "Jakarta Pusat", "provinsi": "DKI Jakarta", "kode_area": "JKTPST", "lat_range": (-6.15, -6.20), "lon_range": (106.80, 106.86)},
    {"nama": "Jakarta Timur", "provinsi": "DKI Jakarta", "kode_area": "JKTTIM", "lat_range": (-6.20, -6.30), "lon_range": (106.85, 106.95)},
    {"nama": "Kabupaten Bandung Barat", "provinsi": "Jawa Barat", "kode_area": "KBB", "lat_range": (-6.75, -6.95), "lon_range": (107.30, 107.60)},
    {"nama": "Kota Yogyakarta", "provinsi": "DI Yogyakarta", "kode_area": "YGK", "lat_range": (-7.78, -7.82), "lon_range": (110.35, 110.40)},
    {"nama": "Kota Malang", "provinsi": "Jawa Timur", "kode_area": "MLG", "lat_range": (-7.90, -8.05), "lon_range": (112.55, 112.70)},
    {"nama": "Kota Batam", "provinsi": "Kepulauan Riau", "kode_area": "BTM", "lat_range": (0.80, 1.20), "lon_range": (103.80, 104.20)},
]

faskes_nama_prefixes = ["Klinik", "RS", "Puskesmas", "Lab Klinik", "Balai Kesehatan"]
faskes_nama_suffixes = ["Medika", "Sejahtera", "Harapan", "Utama", "Sentosa", "Keluarga", "Bakti Husada", "Ceria", "Prima"]
jalan_nama = ["Merdeka", "Diponegoro", "Sudirman", "Thamrin", "Gatot Subroto", "Pahlawan", "Kartini", "Patimura", "Melati", "Mawar", "Anggrek", "Cendana", "Rajawali"]
kelurahan_desa_nama = ["Suka Maju", "Mekar Sari", "Harapan Jaya", "Sumber Rejeki", "Tanjung Sari", "Karang Asih", "Wana Sari", "Bukit Indah"]
kecamatan_nama = ["Kota Baru", "Sukaraja", "Cipedes", "Tawang", "Mangkubumi", "Kawalu", "Indihiang", "Cibeureum"]
nama_pic_pria = ["Budi Santoso", "Agus Wijaya", "Eko Prasetyo", "Rahmat Hidayat", "Joko Susilo", "Tri Kurniawan"]
nama_pic_wanita = ["Siti Aminah", "Dewi Lestari", "Fitri Handayani", "Sri Wahyuni", "Retno Wulandari", "Indah Permatasari"]
dokter_titles = ["Dr.", "dr.", "Prof. Dr."]
manager_titles = ["Bapak", "Ibu", "Manajer"]

roman_months = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]

klb_types = [
    {"jenis": "DBD", "pasien_tambahan": "pasien DBD", "lonjakan_harian_range": (5, 15)},
    {"jenis": "Diare Akut", "pasien_tambahan": "pasien diare", "lonjakan_harian_range": (10, 25)},
    {"jenis": "ISPA Berat", "pasien_tambahan": "pasien ISPA", "lonjakan_harian_range": (8, 20)},
    {"jenis": "Keracunan Makanan", "pasien_tambahan": "korban keracunan", "lonjakan_harian_range": (15, 30)},
    {"jenis": "Chikungunya", "pasien_tambahan": "pasien Chikungunya", "lonjakan_harian_range": (3, 10)},
]

def generate_random_phone():
    return f"08{random.randint(11,99)}{random.randint(1000,9999)}{random.randint(1000,9999)}"

def generate_historis_kunjungan(base_avg_monthly, seasonality_factors=None):
    history = []
    current_date = datetime.date.today()
    if seasonality_factors is None: # default seasonality
        seasonality_factors = {1:1.15, 2:1.1, 3:1.1, 4:0.9, 5:0.9, 6:1.0, 7:1.0, 8:1.05, 9:1.1, 10:1.05, 11:1.0, 12:1.2} # Month: factor

    for i in range(12):
        month_date = current_date - relativedelta(months=i)
        year_month_str = month_date.strftime("%Y-%m")
        
        # Apply seasonality and some randomness
        season_factor = seasonality_factors.get(month_date.month, 1.0)
        visits = int(base_avg_monthly * season_factor * random.uniform(0.95, 1.05))
        history.append({"bulan_tahun": year_month_str, "total_kunjungan": visits})
    return sorted(history, key=lambda x: x["bulan_tahun"]) # Ensure chronological order

def generate_rata_kunjungan_harian(avg_total_monthly, is_24_7=True):
    avg_daily = avg_total_monthly / 30
    days = {"Senin": 0, "Selasa": 0, "Rabu": 0, "Kamis": 0, "Jumat": 0, "Sabtu": 0, "Minggu": 0}
    
    # Distribute visits, with some randomness and typical patterns
    # Weekdays slightly higher for appointments, weekends might be higher for emergencies or if open
    day_factors = {"Senin": 1.0, "Selasa": 1.05, "Rabu": 1.0, "Kamis": 1.05, "Jumat": 0.9}
    if is_24_7:
        day_factors["Sabtu"] = 1.1
        day_factors["Minggu"] = 1.1
    else: # Not 24/7, might be closed or reduced on weekends
        day_factors["Sabtu"] = random.choice([0.8, 0]) # Could be half day or closed
        day_factors["Minggu"] = 0

    total_factor = sum(day_factors.values())
    if total_factor == 0: # Avoid division by zero if all days are 0 (e.g. hypothetical very small clinic)
         for day in days:
            days[day] = 0
         return days


    for day, factor in day_factors.items():
        days[day] = int(avg_daily * (factor / total_factor) * 7 * random.uniform(0.9, 1.1)) if total_factor > 0 else 0
        if days[day] < 0: days[day] = 0 # Ensure non-negative

    # Quick check to ensure sum is somewhat reasonable, not strictly enforced to be exact
    # current_total_daily_avg = sum(days.values()) / 7
    # if current_total_daily_avg > 0:
    #     correction_factor = avg_daily / current_total_daily_avg
    #     for day in days:
    #         days[day] = int(days[day] * correction_factor)
    #         if days[day] < 0 : days[day] = 0

    return days

# --- Generation Loop ---
generated_faskes = []
start_id = 3 # Start from FKS003

for i in range(30):
    faskes_id_num = start_id + i
    
    # 1. Basic Info
    chosen_kota = random.choice(kota_data)
    faskes_type_choice = random.choices(
        ["Klinik Pratama", "Puskesmas", "Rumah Sakit Tipe C", "Rumah Sakit Tipe B", "Klinik Utama", "Laboratorium Klinik"],
        weights=[0.25, 0.25, 0.20, 0.15, 0.1, 0.05], # Relative frequencies
        k=1
    )[0]

    faskes_id_internal = f"FKS{faskes_id_num:03d}-{chosen_kota['kode_area']}"
    nama_faskes_base = f"{random.choice(faskes_nama_prefixes)} {random.choice(faskes_nama_suffixes)}"
    if "Kabupaten" in chosen_kota["nama"] or "Kota" in chosen_kota["nama"]:
         nama_faskes = f"{nama_faskes_base} {chosen_kota['nama'].split(' ')[-1]}"
    else:
         nama_faskes = f"{nama_faskes_base} {chosen_kota['nama']}"


    # 2. Alamat
    alamat = {
        "jalan": f"Jl. {random.choice(jalan_nama)} No. {random.randint(1, 200)}",
        "kelurahan_desa": random.choice(kelurahan_desa_nama),
        "kecamatan": random.choice(kecamatan_nama),
        "kota_kabupaten": chosen_kota["nama"],
        "provinsi": chosen_kota["provinsi"],
        "kode_pos": str(random.randint(10000, 99999))
    }
    koordinat = {
        "latitude": round(random.uniform(chosen_kota["lat_range"][0], chosen_kota["lat_range"][1]), 4),
        "longitude": round(random.uniform(chosen_kota["lon_range"][0], chosen_kota["lon_range"][1]), 4)
    }

    # 3. Izin & PIC
    izin_type_code = "KLN" if "Klinik" in faskes_type_choice else ("PKM" if "Puskesmas" in faskes_type_choice else "RS")
    nomor_izin = f"IZN/{izin_type_code}/{random.randint(1, 999):03d}/{random.choice(roman_months)}/{random.randint(2018, 2023)}"
    
    is_pic_male = random.choice([True, False])
    pic_name_base = random.choice(nama_pic_pria) if is_pic_male else random.choice(nama_pic_wanita)
    pic_title = random.choice(dokter_titles) if "Klinik" in faskes_type_choice or "Dokter" in pic_name_base else (random.choice(manager_titles) if "RS" in faskes_type_choice else ("Kepala Puskesmas" if "Puskesmas" in faskes_type_choice else "Penanggung Jawab Lab"))
    if "Dr." not in pic_name_base and "dr." not in pic_name_base and pic_title in dokter_titles:
        pic_name = f"{pic_title} {pic_name_base}"
    else:
        pic_name = f"{pic_name_base} ({pic_title})" if pic_title not in dokter_titles else pic_name_base


    kontak_pic = {
        "nama": pic_name,
        "telepon": generate_random_phone(),
        "email": f"{pic_name_base.lower().replace(' ','_').replace('.','')}@{nama_faskes_base.lower().replace(' ','')}.example.com"
    }

    # 4. Operasional
    jam_operasional = {}
    is_24_7 = False
    if "Rumah Sakit" in faskes_type_choice:
        is_24_7 = True
        jam_operasional = {"hari": "Senin - Minggu", "jam_buka": "00:00", "jam_tutup": "23:59", "catatan": "UGD 24 Jam"}
    elif "Puskesmas" in faskes_type_choice:
        if random.random() < 0.2: # Some Puskesmas have 24h UGD (PONED)
            is_24_7 = True
            jam_operasional = {"hari": "Senin - Minggu", "jam_buka": "00:00", "jam_tutup": "23:59", "catatan": "UGD 24 Jam, Layanan Poli Pagi-Siang."}
        else:
            jam_operasional = {"hari": "Senin - Sabtu", "jam_buka": "07:30", "jam_tutup": "14:00", "catatan": "Minggu dan hari libur nasional tutup."}
    elif "Laboratorium Klinik" in faskes_type_choice:
         jam_operasional = {"hari": "Senin - Sabtu", "jam_buka": "07:00", "jam_tutup": "19:00", "catatan": "Minggu tutup."}
    else: # Klinik
        jam_operasional = {"hari": "Senin - Sabtu", "jam_buka": "08:00", "jam_tutup": random.choice(["20:00", "21:00"]), "catatan": "Minggu dan hari libur nasional tutup."}

    # 5. Kapasitas & Layanan (highly dependent on type)
    kapasitas = {}
    layanan_unggulan = []
    base_avg_monthly_visits = 0
    pola_kunjungan_layanan = {}
    baseline_staffing = {}

    if faskes_type_choice == "Klinik Pratama":
        kapasitas = {"poli_aktif": random.randint(2, 4), "ruang_periksa": random.randint(2, 5)}
        layanan_unggulan = random.sample(["Poli Umum", "Poli Gigi", "KIA", "Imunisasi", "Khitan", "Lab Sederhana"], k=random.randint(2,4))
        base_avg_monthly_visits = random.randint(400, 900)
        pola_kunjungan_layanan = {"Poli Umum": int(base_avg_monthly_visits/30 * 0.6)}
        if "Poli Gigi" in layanan_unggulan: pola_kunjungan_layanan["Poli Gigi"] = int(base_avg_monthly_visits/30 * 0.2)
        if "KIA" in layanan_unggulan or "Imunisasi" in layanan_unggulan: pola_kunjungan_layanan["KIA/Imunisasi"] = int(base_avg_monthly_visits/30 * 0.2)
        baseline_staffing = {
            "Dokter Umum": {"pagi": random.randint(1,2), "sore": random.randint(0,1)},
            "Perawat": {"pagi": random.randint(1,2), "sore": random.randint(1,1)},
        }
        if "Poli Gigi" in layanan_unggulan: baseline_staffing["Dokter Gigi"] = {"pagi": 1, "sore": 0}
        if "KIA" in layanan_unggulan: baseline_staffing["Bidan"] = {"pagi": 1, "sore": 0}

    elif faskes_type_choice == "Klinik Utama":
        kapasitas = {"poli_spesialis_aktif": random.randint(3, 6), "ruang_periksa": random.randint(5, 10)}
        layanan_unggulan = random.sample(["Poli Penyakit Dalam", "Poli Anak", "Poli Kandungan (Obgyn)", "Poli Bedah Minor", "Poli Jantung", "Poli THT", "Fisioterapi"], k=random.randint(3,5))
        layanan_unggulan.append("Poli Umum")
        base_avg_monthly_visits = random.randint(1000, 2500)
        pola_kunjungan_layanan = {"Poli Umum": int(base_avg_monthly_visits/30 * 0.3)}
        for i, lay in enumerate(layanan_unggulan[:-1]): # Distribute rest among specialists
            pola_kunjungan_layanan[lay] = int(base_avg_monthly_visits/30 * (0.7 / (len(layanan_unggulan)-1) ))
        baseline_staffing = {
            "Dokter Umum": {"pagi": 1, "sore": 1},
            "Dokter Spesialis (bergiliran)": {"pagi": len(layanan_unggulan)-1, "sore": random.randint(1, max(1,len(layanan_unggulan)-2))},
            "Perawat": {"pagi": random.randint(3,5), "sore": random.randint(2,4)},
        }


    elif faskes_type_choice == "Puskesmas":
        kapasitas = {"poli_aktif": random.randint(4, 7), "ruang_periksa": random.randint(5, 10), "tempat_tidur_poned": (random.randint(2,5) if is_24_7 else 0) }
        layanan_unggulan = ["Poli Umum", "Poli Gigi", "KIA & KB", "Imunisasi", "Gizi", "Sanitasi/Kesling", "Laboratorium Sederhana"]
        if is_24_7: layanan_unggulan.append("UGD 24 Jam (PONED)")
        base_avg_monthly_visits = random.randint(1500, 4000)
        pola_kunjungan_layanan = {"Poli Umum": int(base_avg_monthly_visits/30 * 0.4), "KIA & KB": int(base_avg_monthly_visits/30 * 0.2), "Poli Gigi": int(base_avg_monthly_visits/30 * 0.15)}
        if is_24_7: pola_kunjungan_layanan["UGD"] = int(base_avg_monthly_visits/30 * 0.1)
        baseline_staffing = {
            "Dokter Umum": {"pagi": random.randint(1,3), "sore": (1 if is_24_7 else 0)},
            "Dokter Gigi": {"pagi": 1},
            "Perawat": {"pagi": random.randint(3,6), "sore": (random.randint(1,2) if is_24_7 else 0)},
            "Bidan": {"pagi": random.randint(2,4), "sore": (random.randint(1,2) if is_24_7 else 0)},
            "Tenaga Kesmas/Gizi/Sanitarian": {"pagi": random.randint(1,3)}
        }
        if is_24_7: baseline_staffing["Dokter Umum"]["malam"] = 1; baseline_staffing["Perawat"]["malam"] = 1; baseline_staffing["Bidan"]["malam"] = 1;


    elif faskes_type_choice == "Rumah Sakit Tipe C":
        kapasitas = {"jumlah_tempat_tidur_total": random.randint(80, 150), "poli_aktif": random.randint(8, 12), "ruang_periksa_ugd": random.randint(4,8), "ruang_periksa_poli": random.randint(10,20)}
        layanan_unggulan = ["UGD 24 Jam", "Rawat Inap", "Poli Anak", "Poli Penyakit Dalam", "Poli Bedah Umum", "Poli Obgyn", "Radiologi", "Laboratorium Lengkap"]
        layanan_unggulan.extend(random.sample(["Poli Mata", "Poli THT", "Poli Saraf", "Rehabilitasi Medik"], k=random.randint(1,2)))
        base_avg_monthly_visits = random.randint(2500, 5000) # UGD + Rawat Jalan
        pola_kunjungan_layanan = {"UGD": int(base_avg_monthly_visits/30 * 0.25), "RJ Poli Umum/Dalam": int(base_avg_monthly_visits/30 * 0.3), "RJ Poli Anak": int(base_avg_monthly_visits/30 * 0.15), "RJ Poli Bedah": int(base_avg_monthly_visits/30 * 0.1), "RJ Poli Obgyn": int(base_avg_monthly_visits/30 * 0.1)}
        baseline_staffing = {
            "Dokter Umum (UGD)": {"pagi": 2, "sore": 2, "malam": 1},
            "Dokter Umum (Poli)": {"pagi": random.randint(2,4), "sore": random.randint(1,2)},
            "Dokter Spesialis (total, terjadwal)": {"pagi": len(layanan_unggulan) - 3, "sore": max(1, int((len(layanan_unggulan) -3)*0.5) ) }, # Crude estimate
            "Perawat (UGD)": {"pagi": random.randint(3,5), "sore": random.randint(3,5), "malam": random.randint(2,3)},
            "Perawat (Rawat Inap)": {"pagi": random.randint(6,10), "sore": random.randint(6,10), "malam": random.randint(4,7)},
            "Perawat (Poli)": {"pagi": random.randint(5,8), "sore": random.randint(3,5)}
        }

    elif faskes_type_choice == "Rumah Sakit Tipe B":
        kapasitas = {"jumlah_tempat_tidur_total": random.randint(150, 300), "poli_aktif": random.randint(12, 20), "ruang_periksa_ugd": random.randint(6,12), "ruang_periksa_poli": random.randint(15,30), "ICU_beds": random.randint(5,15)}
        layanan_unggulan = ["UGD 24 Jam (Subspesialistik)", "Rawat Inap Intensif (ICU/NICU/PICU)", "Bedah Mayor & Subspesialistik", "Poli Jantung & Pembuluh Darah", "Poli Saraf Lanjutan", "Poli Onkologi", "Hemodialisa"]
        layanan_unggulan.extend(random.sample(["Pusat Trauma", "Katerisasi Jantung", "Endoskopi Lanjut"], k=random.randint(1,2)))
        base_avg_monthly_visits = random.randint(4500, 8000)
        pola_kunjungan_layanan = {"UGD": int(base_avg_monthly_visits/30 * 0.20), "RJ Poli Jantung": int(base_avg_monthly_visits/30 * 0.1), "RJ Poli Dalam Subsp.": int(base_avg_monthly_visits/30 * 0.15), "RJ Poli Anak Subsp.": int(base_avg_monthly_visits/30 * 0.1), "RJ Poli Bedah Subsp.": int(base_avg_monthly_visits/30 * 0.1)}
        baseline_staffing = {
            "Dokter Umum (UGD)": {"pagi": random.randint(2,4), "sore": random.randint(2,3), "malam": random.randint(1,2)},
            "Dokter Spesialis (UGD, on-call/shift)": {"pagi":2, "sore":2, "malam":1},
            "Dokter Subspesialis (total, terjadwal)": {"pagi": len(layanan_unggulan) - 2 , "sore": max(2, int((len(layanan_unggulan) -2)*0.6) ) },
            "Perawat (UGD)": {"pagi": random.randint(5,8), "sore": random.randint(5,8), "malam": random.randint(3,5)},
            "Perawat (Rawat Inap)": {"pagi": random.randint(10,15), "sore": random.randint(10,15), "malam": random.randint(8,12)},
            "Perawat (ICU)": {"pagi": random.randint(4,8), "sore": random.randint(4,8), "malam": random.randint(3,6)},
            "Perawat (Poli)": {"pagi": random.randint(8,12), "sore": random.randint(6,10)}
        }
    
    elif faskes_type_choice == "Laboratorium Klinik":
        kapasitas = {"jumlah_alat_otomatis": random.randint(2,5), "ruang_sampling": random.randint(2,4)}
        layanan_unggulan = ["Hematologi Lengkap", "Kimia Klinik", "Urinalisa", "Imunoserologi", "Mikrobiologi Dasar"]
        if random.random() > 0.5 : layanan_unggulan.append("Tes PCR (Sampel tertentu)")
        if random.random() > 0.3 : layanan_unggulan.append("Patologi Anatomi (Rujukan)")
        base_avg_monthly_visits = random.randint(1000, 3000) # Jumlah pasien/sampel
        pola_kunjungan_layanan = {"Pemeriksaan Rutin (Darah, Urin)": int(base_avg_monthly_visits/30 * 0.7), "Pemeriksaan Khusus (Imuno, Kultur)": int(base_avg_monthly_visits/30 * 0.3)}
        baseline_staffing = {
            "Dokter SpPK (Penanggung Jawab)": {"pagi": 1},
            "Analis Kesehatan": {"pagi": random.randint(2,5), "sore": random.randint(1,3)},
            "Tenaga Sampling/Flebotomis": {"pagi": random.randint(1,3), "sore": random.randint(0,1)},
            "Administrasi": {"pagi": random.randint(1,2), "sore": random.randint(0,1)},
        }


    # Ensure all keys in pola_kunjungan_layanan are positive or zero
    for key in pola_kunjungan_layanan:
        if pola_kunjungan_layanan[key] < 0:
            pola_kunjungan_layanan[key] = 0
    
    # 6. Historis Kunjungan
    historis_kunjungan = generate_historis_kunjungan(base_avg_monthly_visits)
    avg_total_monthly_from_history = sum(h["total_kunjungan"] for h in historis_kunjungan) / 12
    rata_kunjungan_harian = generate_rata_kunjungan_harian(avg_total_monthly_from_history, is_24_7)


    # 7. Periode Puncak
    periode_puncak = random.sample([
        "Awal Tahun (Jan-Feb, pasca liburan & musim hujan)",
        "Musim Pancaroba (Mar-Apr, Sep-Okt, ISPA/DBD)",
        "Libur Sekolah (Juni-Juli, Desember)",
        "Akhir Tahun (Desember, peningkatan aktivitas)",
        "Musim Haji (peningkatan vaksinasi/pemeriksaan pra-haji)"
    ], k=random.randint(1,3))

    # 8. Historis KLB (optional)
    historis_klb = []
    if random.random() < 0.25: # 25% chance of having a KLB record
        klb = random.choice(klb_types)
        start_year = random.randint(2022, 2023)
        start_month = random.randint(1,11) # avoid month 12 to make duration simple
        start_day = random.randint(1,15)
        klb_start_date = datetime.date(start_year, start_month, start_day)
        klb_end_date = klb_start_date + datetime.timedelta(days=random.randint(10, 30))
        historis_klb.append({
            "jenis_klb": klb["jenis"],
            "periode": f"{klb_start_date.strftime('%Y-%m-%d')} hingga {klb_end_date.strftime('%Y-%m-%d')}",
            f"lonjakan_{klb['pasien_tambahan'].replace(' ','_')}_harian": random.randint(klb["lonjakan_harian_range"][0], klb["lonjakan_harian_range"][1])
        })

    # Construct the faskes entry
    faskes_entry = {
        "faskes_id_internal": faskes_id_internal,
        "nama_faskes": nama_faskes,
        "jenis_faskes": faskes_type_choice,
        "alamat_lengkap": alamat,
        "koordinat": koordinat,
        "nomor_izin_operasional": nomor_izin,
        "kontak_pic": kontak_pic,
        "jam_operasional": jam_operasional,
        "kapasitas": kapasitas,
        "layanan_unggulan": layanan_unggulan,
        "historis_kunjungan_bulanan": historis_kunjungan,
        "rata_kunjungan_harian_seminggu": rata_kunjungan_harian,
        "pola_kunjungan_layanan": pola_kunjungan_layanan,
        "periode_puncak_diketahui": periode_puncak,
        "historis_klb_lokal": historis_klb,
        "baseline_staffing": baseline_staffing
    }
    generated_faskes.append(faskes_entry)

# Add the generated data to the original DUMMY_FASKES_DATA
#DUMMY_FASKES_DATA.extend(generated_faskes)

print(f"Total faskes data generated: {len(DUMMY_FASKES_DATA)}")
# For demonstration, print the first new entry and the last new entry
# import json
# print("\n--- First New Entry (FKS003) ---")
# print(json.dumps(DUMMY_FASKES_DATA[2], indent=4, ensure_ascii=False))
# print("\n--- Last New Entry ---")
# print(json.dumps(DUMMY_FASKES_DATA[-1], indent=4, ensure_ascii=False))