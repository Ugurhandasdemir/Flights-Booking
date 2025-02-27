# Generated by Django 5.0.10 on 2024-12-29 09:45

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("wbst", "0002_rename_id_bilet_bilet_id_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="musteri",
            name="email",
            field=models.EmailField(max_length=254),
        ),
        migrations.CreateModel(
            name="Odeme",
            fields=[
                ("odeme_id", models.AutoField(primary_key=True, serialize=False)),
                ("kart_sahibi", models.CharField(max_length=100)),
                ("kart_numarasi", models.CharField(max_length=16)),
                ("son_kullanma_tarihi", models.CharField(max_length=5)),
                ("cvc", models.CharField(max_length=4)),
                ("odeme_tutari", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "odeme_tarihi",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "bilet",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="odeme",
                        to="wbst.bilet",
                    ),
                ),
            ],
        ),
    ]
