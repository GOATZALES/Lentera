# Lentera/billing/views.py
from datetime import timedelta
from venv import logger
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required # Aktifkan jika perlu
from django.contrib import messages
from .models import Transaction # Hanya butuh Transaction model
from authentication.models import Faskes as FaskesPartner # Sesuaikan path
from django.utils import timezone
from decimal import Decimal
import random 

TIER_DETAILS = {
    '3T_REGIONS': {
        'id': '3T_REGIONS',
        'name': '3T Regions Tier',
        'transaction_fee_display': '1%', 
        'transaction_fee_percentage': Decimal('1.00'),
        'monthly_subscription_fee_rp': Decimal('0.00'),
        'description': 'Untuk Faskes di daerah terpencil. Fee transaksi sangat rendah.',
        'features': ['Matching Dasar', 'AI Forecasting (Output Dasar)', 'Dashboard Ringkas', 'Dukungan Email Prioritas Rendah']
    },
    'STANDARD': {
        'id': 'STANDARD',
        'name': 'Standard Tier',
        'transaction_fee_display': '2% - 3%', # Untuk tampilan
        'transaction_fee_percentage': Decimal('2.50'), # Kita ambil rata-rata untuk kalkulasi dummy
        'monthly_subscription_fee_rp': Decimal('0.00'),
        'description': 'Fee transaksi kompetitif per shift. Akses ke fitur standar platform.',
        'features': ['Matching Cepat', 'Dashboard Standar', 'Riwayat Transaksi', 'Dukungan Email Standar']
    },
    'PREMIUM': {
        'id': 'PREMIUM',
        'name': 'Premium Tier',
        'transaction_fee_display': '3% - 5%', # Untuk tampilan
        'transaction_fee_percentage': Decimal('4.00'), # Kita ambil rata-rata untuk kalkulasi dummy
        'monthly_subscription_fee_rp': Decimal('2000000.00'),
        'description': 'Fitur lengkap dengan AI forecasting canggih dan dukungan prioritas.',
        'features': [
            'Semua Fitur Standard', 
            'AI Forecasting Advanced (Prediksi Akurat, Rekomendasi Detail)',
            'Analytics Dashboard Kustom', 
            'Budget Planning Tools',
            'Integrasi SATUSEHAT (Prioritas)',
            'Dukungan Prioritas 24/7 (Telepon & Chat)'
        ]
    },
    'UNKNOWN': { # Fallback jika tier Faskes tidak dikenali
        'id': 'UNKNOWN',
        'name': 'Tier Tidak Diketahui',
        'transaction_fee_display': 'N/A',
        'transaction_fee_percentage': Decimal('5.00'), # Default fee tinggi
        'monthly_subscription_fee_rp': Decimal('0.00'),
        'description': 'Status langganan tidak diketahui. Silakan hubungi admin.',
        'features': ['Fitur Terbatas']
    }
}

def get_current_faskes_id_for_billing(request):
    # Contoh: Ambil dari user yang login jika ada relasi
    # if request.user.is_authenticated and hasattr(request.user, 'faskes_profile_relation_name'):
    #    return request.user.faskes_profile_relation_name.faskes_id_internal
    return "FKS001-JKTSEL" # Untuk demo

# @login_required
def faskes_billing_dashboard_view(request): # Ubah nama view
    faskes_id = get_current_faskes_id_for_billing(request)
    faskes_partner = None
    current_tier_details = TIER_DETAILS['UNKNOWN'] # Default jika Faskes tidak ditemukan
    transactions = []

    try:
        faskes_partner = FaskesPartner.objects.get(faskes_id_internal=faskes_id)
        # Dapatkan detail tier dari data hardcode berdasarkan tier_id_str Faskes
        current_tier_details = TIER_DETAILS.get(faskes_partner.subscription_tier_id_str, TIER_DETAILS['UNKNOWN'])
        
        # Ambil transaksi (ini masih dari database)
        transactions = Transaction.objects.filter(faskes=faskes_partner).order_by('-transaction_time')[:20] # Ambil 20 terbaru

        # Jika ingin membuat dummy transaction untuk demo UI jika DB kosong:
        if not transactions and faskes_partner: # Hanya buat jika DB kosong & partner ada
            for i in range(5):
                is_platform_fee = random.choice([True, False])
                amount = Decimal(random.randint(50000, 500000)) if not is_platform_fee else Decimal(random.randint(1000, 50000))
                Transaction.objects.create(
                    faskes=faskes_partner,
                    transaction_type='PLATFORM_FEE' if is_platform_fee else 'SHIFT_PAYMENT',
                    amount=amount,
                    platform_fee_charged=amount if is_platform_fee else Decimal('0.00'),
                    status=random.choice(['SUCCESSFUL', 'PENDING', 'FAILED']),
                    description=f"Dummy Transaksi Otomatis #{i+1} untuk Faskes {faskes_partner.nama_faskes}",
                    transaction_time=timezone.now() - timedelta(days=random.randint(0, 30), hours=random.randint(0,23))
                )
            transactions = Transaction.objects.filter(faskes=faskes_partner).order_by('-transaction_time')[:20]


    except FaskesPartner.DoesNotExist:
        messages.error(request, f"Faskes dengan ID {faskes_id} tidak ditemukan.")
    except Exception as e:
        messages.error(request, f"Terjadi kesalahan: {str(e)}")
        logger.error(f"Error di faskes_billing_dashboard_view: {e}", exc_info=True)


    context = {
        'faskes_partner': faskes_partner,
        'current_tier': current_tier_details, # Kirim detail tier hardcode
        'transactions': transactions,
        'page_title': f"Billing & Langganan - {faskes_partner.nama_faskes if faskes_partner else 'Faskes'}",
        'all_tiers': TIER_DETAILS# Untuk menampilkan opsi tier lain
    }
    return render(request, 'faskes_billing_dashboard.html', context) # Template baru