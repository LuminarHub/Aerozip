# Generated by Django 5.1.6 on 2025-02-25 16:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_shipment_from_airport_shipment_from_airport_code_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='domesticairports',
            name='code',
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='internationalairports',
            name='code',
            field=models.CharField(max_length=100, unique=True),
        ),
    ]
