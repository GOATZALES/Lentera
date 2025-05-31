# Lentera/billing/models.py
from django.db import models
from django.utils import timezone
from django.conf import settings # Tidak langsung digunakan, tapi baik untuk standar
import uuid
from decimal import Decimal # Penting untuk tipe data uang

# Impor model Faskes Anda. Pastikan path ini benar.
from authentication.models import Faskes as FaskesPartner
# Impor model ShiftAssignment Anda. Pastikan path ini benar.
from management.models import ShiftAssignment


class SubscriptionTier(models.Model):
    TIER_ID_CHOICES = [
        ('3T_REGIONS', '3T Regions Tier'),
        ('STANDARD', 'Standard Tier'),
        ('PREMIUM', 'Premium Tier'),
    ]
    tier_id = models.CharField(max_length=20, choices=TIER_ID_CHOICES, unique=True, primary_key=True)
    name = models.CharField(max_length=100)
    transaction_fee_percentage_min = models.DecimalField(max_digits=5, decimal_places=2, help_text="Persentase fee transaksi minimum (misal 1.00 untuk 1%)")
    transaction_fee_percentage_max = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Persentase fee transaksi maksimum (jika ada rentang)")
    monthly_subscription_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Biaya langganan bulanan dalam Rupiah")
    description = models.TextField(blank=True)
    features_included_json = models.JSONField(default=list, blank=True, help_text="Contoh: ['AI Forecasting Basic', 'Emergency Matching']")

    def __str__(self):
        return self.name

    def get_applicable_transaction_fee_percentage(self) -> Decimal:
        if self.transaction_fee_percentage_max is not None and self.transaction_fee_percentage_max > self.transaction_fee_percentage_min:
            # Anda bisa pilih strategi, misal selalu min, selalu max, atau rata-rata.
            # Untuk contoh, kita ambil nilai min saja agar lebih sederhana dan menguntungkan Faskes.
            # Atau jika ada logika sliding scale, implementasikan di sini.
            # Untuk Hackathon, nilai min cukup.
            return self.transaction_fee_percentage_min
        return self.transaction_fee_percentage_min


class FaskesSubscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    faskes = models.OneToOneField(FaskesPartner, on_delete=models.CASCADE, related_name='subscription_info') # Ganti related_name
    tier = models.ForeignKey(SubscriptionTier, on_delete=models.PROTECT, related_name='faskes_subscriptions')
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True, help_text="Tanggal berakhir langganan (untuk Premium), atau kosong jika berkelanjutan.")
    next_billing_date_monthly = models.DateField(null=True, blank=True, help_text="Untuk Premium Tier, tanggal pembayaran langganan berikutnya") 
    is_active = models.BooleanField(default=True, help_text="Apakah langganan ini aktif?")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.faskes.nama_faskes} - {self.tier.name}"

    class Meta:
        ordering = ['-start_date']
        verbose_name = "Langganan Faskes"
        verbose_name_plural = "Langganan Faskes"


class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('SHIFT_PAYMENT', 'Pembayaran Shift Nakes'),
        ('PLATFORM_FEE', 'Biaya Platform (dari Shift)'),
        ('MONTHLY_SUBSCRIPTION', 'Biaya Langganan Bulanan'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SUCCESSFUL', 'Successful'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    faskes = models.ForeignKey(FaskesPartner, on_delete=models.SET_NULL, null=True, blank=True, related_name='billing_transactions') # Ganti related_name
    shift_assignment = models.ForeignKey(ShiftAssignment, on_delete=models.SET_NULL, null=True, blank=True, related_name='billing_transactions') # Ganti related_name
    faskes_subscription_payment_for = models.ForeignKey( # Lebih deskriptif
        FaskesSubscription, 
        on_delete=models.SET_NULL, null=True, blank=True, 
        related_name='monthly_payment_transactions', 
        help_text="Untuk pembayaran langganan bulanan"
    )

    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Jumlah total transaksi")
    platform_fee_charged = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Biaya platform yang dikenakan dari transaksi ini")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_method_details = models.CharField(max_length=255, blank=True, help_text="Contoh: Bank Transfer (BCA), GoPay")
    payment_gateway_reference_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    
    description = models.TextField(blank=True)
    transaction_time = models.DateTimeField(default=timezone.now)
    completed_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"TRX-{str(self.id)[:8]}: {self.get_transaction_type_display()} - Rp {self.amount} ({self.status})"

    class Meta:
        ordering = ['-transaction_time']
        verbose_name = "Transaksi Billing"
        verbose_name_plural = "Transaksi Billing"