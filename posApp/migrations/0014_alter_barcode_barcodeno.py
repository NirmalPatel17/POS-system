# Generated by Django 4.2.2 on 2023-12-09 04:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posApp', '0013_alter_barcode_barcode'),
    ]

    operations = [
        migrations.AlterField(
            model_name='barcode',
            name='barcodeNo',
            field=models.CharField(max_length=120, null=True),
        ),
    ]
