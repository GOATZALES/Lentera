from django.core.management.base import BaseCommand
from authentication.models import Faskes 
from .dummy_faskes_data import DUMMY_FASKES_DATA 

class Command(BaseCommand):
    help = 'Seeds the database with dummy Faskes Partner data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding Faskes Partner data...')
        for data in DUMMY_FASKES_DATA:
            partner, created = Faskes.objects.update_or_create(
                faskes_id_internal=data["faskes_id_internal"],
                defaults={
                    "nama_faskes": data["nama_faskes"],
                    "jenis_faskes": data["jenis_faskes"],
                    "alamat_jalan": data["alamat_lengkap"]["jalan"],
                    "alamat_kelurahan_desa": data["alamat_lengkap"]["kelurahan_desa"],
                    "alamat_kecamatan": data["alamat_lengkap"]["kecamatan"],
                    "alamat_kota_kabupaten": data["alamat_lengkap"]["kota_kabupaten"],
                    "alamat_provinsi": data["alamat_lengkap"]["provinsi"],
                    "alamat_kode_pos": data["alamat_lengkap"]["kode_pos"],
                    "koordinat_latitude": data["koordinat"]["latitude"],
                    "koordinat_longitude": data["koordinat"]["longitude"],
                    "nomor_izin_operasional": data["nomor_izin_operasional"],
                    "pic_nama": data["kontak_pic"]["nama"],
                    "pic_telepon": data["kontak_pic"]["telepon"],
                    "pic_email": data["kontak_pic"]["email"],
                    "ops_hari": data["jam_operasional"]["hari"],
                    "ops_jam_buka": data["jam_operasional"]["jam_buka"] if data["jam_operasional"]["jam_buka"] != "00:00" or data["jam_operasional"]["jam_tutup"] != "23:59" else None, # Handle 24 jam
                    "ops_jam_tutup": data["jam_operasional"]["jam_tutup"] if data["jam_operasional"]["jam_buka"] != "00:00" or data["jam_operasional"]["jam_tutup"] != "23:59" else None,
                    "ops_catatan": data["jam_operasional"]["catatan"],
                    "kapasitas_info_json": data["kapasitas"],
                    "layanan_unggulan_json": data["layanan_unggulan"],
                    "historis_kunjungan_bulanan_json": data["historis_kunjungan_bulanan"],
                    "rata_kunjungan_harian_seminggu_json": data["rata_kunjungan_harian_seminggu"],
                    "pola_kunjungan_layanan_json": data["pola_kunjungan_layanan"],
                    "periode_puncak_diketahui_json": data["periode_puncak_diketahui"],
                    "historis_klb_lokal_json": data["historis_klb_lokal"],
                    "baseline_staffing_json": data["baseline_staffing"],
                    "is_active_partner": True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Successfully created Faskes Partner: {partner.nama_faskes}'))
            else:
                self.stdout.write(f'Updated Faskes Partner: {partner.nama_faskes}')
        self.stdout.write(self.style.SUCCESS('Finished seeding Faskes Partner data.'))