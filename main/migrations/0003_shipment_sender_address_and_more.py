# Generated by Django 5.1.6 on 2025-02-25 14:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_address_shipment_shipmenttrackingupdate'),
    ]

    operations = [
        migrations.AddField(
            model_name='shipment',
            name='sender_address',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='sender_address', to='main.address'),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='recipient_address',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='receiver_address', to='main.address'),
        ),
    ]
