# Generated manually
from django.db import migrations


def set_min_stok_to_zero(apps, schema_editor):
    """Tüm ürünlerin min_stok_adedi değerini 0 yap"""
    Urun = apps.get_model('stok', 'Urun')
    Urun.objects.all().update(min_stok_adedi=0)


def reverse_func(apps, schema_editor):
    """Geri alma işlemi - gerekli değil"""
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('stok', '0007_alter_urun_min_stok_adedi'),
    ]

    operations = [
        migrations.RunPython(set_min_stok_to_zero, reverse_func),
    ]

