# emergency/migrations/000X_seed_initial_task_categories.py 
# (Ganti X dengan nomor migrasi yang sebenarnya)
from django.db import migrations

def create_initial_task_categories(apps, schema_editor):
    TaskCategory = apps.get_model('emergency', 'TaskCategory') # Ambil model historis
    
    categories_data = [
        {"name": "Logistik & Distribusi", "description": "Pengelolaan dan pendistribusian bantuan logistik."},
        {"name": "Dapur Umum", "description": "Menyiapkan dan menyajikan makanan."},
        {"name": "Administrasi & Pendataan", "description": "Membantu pencatatan data dan pelaporan."},
        {"name": "Transportasi Lokal", "description": "Membantu mobilitas korban atau barang."},
        {"name": "Dukungan Psikososial Dasar", "description": "Memberikan dukungan emosional awal."},
        # ... (tambahkan kategori lain seperti di Cara 1) ...
    ]

    for cat_data in categories_data:
        # Di sini kita tidak menggunakan get_or_create karena migrasi seharusnya hanya berjalan sekali
        # Namun, jika ada kemungkinan migrasi ini di-rollback dan dijalankan lagi,
        # Anda mungkin ingin menambahkan pengecekan if not TaskCategory.objects.filter(name=cat_data["name"]).exists():
        if not TaskCategory.objects.filter(name=cat_data["name"]).exists():
            TaskCategory.objects.create(name=cat_data["name"], description=cat_data.get("description", ""))

def remove_initial_task_categories(apps, schema_editor):
    # Logika untuk menghapus data jika migrasi di-rollback (opsional)
    TaskCategory = apps.get_model('emergency', 'TaskCategory')
    categories_names = [
        "Logistik & Distribusi", "Dapur Umum", "Administrasi & Pendataan", 
        "Transportasi Lokal", "Dukungan Psikososial Dasar",
        # ... (nama kategori lain) ...
    ]
    TaskCategory.objects.filter(name__in=categories_names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('emergency', '0003_taskcategory_volunteerprofile_volunteerapplication'), 
    ]

    operations = [
        migrations.RunPython(create_initial_task_categories, remove_initial_task_categories),
    ]