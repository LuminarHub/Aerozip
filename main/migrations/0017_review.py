# Generated by Django 5.1.6 on 2025-02-28 07:55

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0016_shipment_is_paid'),
    ]

    operations = [
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shipment_id', models.CharField(blank=True, max_length=20, null=True)),
                ('rating', models.IntegerField(choices=[(1, '1 - Poor'), (2, '2 - Below Average'), (3, '3 - Average'), (4, '4 - Good'), (5, '5 - Excellent')], validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('title', models.CharField(max_length=100)),
                ('comment', models.TextField()),
                ('delivery_satisfaction', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
