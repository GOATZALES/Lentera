from emergency.models import EmergencyEvent
from authentication.models import Faskes
from django.utils import timezone
from django.contrib.auth.models import User

# Buat 2 Faskes
f1 = Faskes.objects.create(
    faskes_id_internal="F001",
    nama_faskes="RSU Harapan Bangsa",
    jenis_faskes="Rumah Sakit",
    alamat_jalan="Jl. Merdeka No. 10",
    alamat_kelurahan_desa="Kel. Sukamaju",
    alamat_kecamatan="Kec. Sukamakmur",
    alamat_kota_kabupaten="Kota Bandung",
    alamat_provinsi="Jawa Barat",
    alamat_kode_pos="40123",
    koordinat_latitude=-6.914744,
    koordinat_longitude=107.609810,
    nomor_izin_operasional="123/RS/2020",
    pic_nama="Dr. Andi",
    pic_telepon="08123456789",
    pic_email="andi@rsuhb.com",
    ops_hari="Senin - Sabtu",
    ops_jam_buka="08:00",
    ops_jam_tutup="20:00",
    kapasitas_info_json={"tempat_tidur": 150, "poli_aktif": 6},
    layanan_unggulan_json=["UGD", "Poli Umum"],
)

f2 = Faskes.objects.create(
    faskes_id_internal="F002",
    nama_faskes="Puskesmas Sehat Sentosa",
    jenis_faskes="Puskesmas",
    alamat_jalan="Jl. Sehat No. 5",
    alamat_kelurahan_desa="Kel. Mekarsari",
    alamat_kecamatan="Kec. Cibeunying",
    alamat_kota_kabupaten="Kota Yogyakarta",
    alamat_provinsi="DI Yogyakarta",
    alamat_kode_pos="55223",
    koordinat_latitude=-7.801194,
    koordinat_longitude=110.364917,
    kapasitas_info_json={"tempat_tidur": 20, "poli_aktif": 2},
    layanan_unggulan_json=["Imunisasi", "KIA"],
)

# Ambil user admin untuk relasi (jika ada)
admin_user = User.objects.filter(is_superuser=True).first()

# Buat 2 EmergencyEvent
e1 = EmergencyEvent.objects.create(
    disaster_type="Gempa Bumi",
    location_description="Kab. Cianjur",
    severity_level=3,
    affected_regions_input="Kab. Cianjur, Kab. Sukabumi",
    description="Gempa berkekuatan 6.1 SR mengguncang wilayah Cianjur",
    is_active=True,
    activation_time=timezone.now(),
    manually_triggered_by=admin_user,
    matching_acceleration_enabled=True,
    expanded_matching_radius_km=50,
)

e2 = EmergencyEvent.objects.create(
    disaster_type="Wabah Penyakit",
    location_description="Kota Palu",
    severity_level=2,
    affected_regions_input="Kota Palu, Kab. Donggala",
    description="Wabah demam berdarah meningkat tajam",
    is_active=False,
    matching_acceleration_enabled=False,
)
