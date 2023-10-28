# Generated by Django 4.2.2 on 2023-10-02 13:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posApp', '0009_rename_product_barcode'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='barcode',
            name='country_id',
        ),
        migrations.RemoveField(
            model_name='barcode',
            name='manufacturer_id',
        ),
        migrations.RemoveField(
            model_name='barcode',
            name='product_id',
        ),
        migrations.AddField(
            model_name='barcode',
            name='random',
            field=models.CharField(max_length=12, null=True),
        ),
    ]
