# Generated by Django 5.2.1 on 2025-05-31 17:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='faskes',
            name='subscription_tier_id_str',
            field=models.CharField(choices=[('3T_REGIONS', '3T Regions Tier'), ('STANDARD', 'Standard Tier'), ('PREMIUM', 'Premium Tier')], default='STANDARD', help_text='ID tier langganan Faskes (diset saat Faskes menjadi partner)', max_length=20),
        ),
    ]
