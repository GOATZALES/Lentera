# Lentera/billing/apps.py
from django.apps import AppConfig
from django.db.models.signals import post_migrate # Import signal
from django.dispatch import receiver # Import receiver decorator

# Pindahkan fungsi create_initial_subscription_tiers ke sini
def seed_subscription_tiers(sender, **kwargs):
    # Import model di dalam fungsi untuk menghindari AppRegistryNotReady saat Django startup awal
    from .models import SubscriptionTier 
    from decimal import Decimal

    tiers_data = [
        {
            'tier_id': '3T_REGIONS', 'name': '3T Regions Tier',
            'transaction_fee_percentage_min': Decimal('1.00'), 
            'monthly_subscription_fee': Decimal('0.00'),
            'description': 'Untuk Faskes di daerah 3T. Fee transaksi rendah, fitur dasar gratis.',
            'features_included_json': ['AI Forecasting Basic', 'Emergency Matching', 'Basic Dashboard']
        },
        {
            'tier_id': 'STANDARD', 'name': 'Standard Tier',
            'transaction_fee_percentage_min': Decimal('2.00'), 
            'transaction_fee_percentage_max': Decimal('3.00'),
            'monthly_subscription_fee': Decimal('0.00'),
            'description': 'Fee transaksi per shift. Akses fitur dasar.',
            'features_included_json': ['Standard Matching', 'Dashboard', 'Email Support']
        },
        {
            'tier_id': 'PREMIUM', 'name': 'Premium Tier',
            'transaction_fee_percentage_min': Decimal('3.00'), 
            'transaction_fee_percentage_max': Decimal('5.00'),
            'monthly_subscription_fee': Decimal('2000000.00'),
            'description': 'Kombinasi fee transaksi dan langganan bulanan untuk fitur lanjutan.',
            'features_included_json': ['AI Forecasting Advanced', 'Custom Dashboard', '24/7 Support', 'All Standard Features']
        }
    ]

    print("Attempting to seed/update subscription tiers...")
    for data in tiers_data:
        tier, created = SubscriptionTier.objects.update_or_create(
            tier_id=data['tier_id'],
            defaults=data
        )
        if created:
            print(f'CREATED tier: {tier.name}')
        else:
            print(f'UPDATED/VERIFIED tier: {tier.name}')
    print("Subscription tiers seeding/update process finished.")


class BillingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'billing'

    def ready(self):
        # Hubungkan signal post_migrate dengan fungsi seeding
        # Ini akan menjalankan seed_subscription_tiers setelah migrasi untuk aplikasi 'billing' selesai
        # dan juga saat aplikasi pertama kali dimuat jika tabel sudah ada.
        post_migrate.connect(seed_subscription_tiers, sender=self)
        
        # Jika Anda ingin ini dijalankan setiap kali server start (bukan hanya setelah migrate),
        # Anda bisa memanggilnya langsung, TAPI hati-hati jika ada operasi DB berat.
        # Untuk seeding data statis seperti ini, post_migrate lebih aman.
        # if settings.DEBUG: # Mungkin hanya jalankan di DEBUG atau jika tabel kosong
        #     seed_subscription_tiers(sender=self)