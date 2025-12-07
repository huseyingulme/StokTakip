from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrate_hareket_tipi_to_islem_turu(apps, schema_editor):
    StokHareketi = apps.get_model('stok', 'StokHareketi')
    for hareket in StokHareketi.objects.all():
        if hareket.hareket_tipi == 'IN':
            hareket.islem_turu = 'giriş'
        elif hareket.hareket_tipi == 'OUT':
            hareket.islem_turu = 'çıkış'
        hareket.save()


def reverse_migrate_islem_turu_to_hareket_tipi(apps, schema_editor):
    StokHareketi = apps.get_model('stok', 'StokHareketi')
    for hareket in StokHareketi.objects.all():
        if hareket.islem_turu == 'giriş':
            hareket.hareket_tipi = 'IN'
        elif hareket.islem_turu == 'çıkış':
            hareket.hareket_tipi = 'OUT'
        hareket.save()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('stok', '0002_kategori_alter_urun_ad_alter_urun_barkod_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='urun',
            name='aciklama',
        ),
        migrations.RemoveField(
            model_name='urun',
            name='guncelleme_tarihi',
        ),
        migrations.RemoveField(
            model_name='urun',
            name='stok_adedi',
        ),
        migrations.AddField(
            model_name='urun',
            name='min_stok_adedi',
            field=models.IntegerField(default=0, verbose_name='Minimum Stok Seviyesi'),
        ),
        migrations.RenameField(
            model_name='stokhareketi',
            old_name='olusturma_tarihi',
            new_name='tarih',
        ),
        migrations.RenameField(
            model_name='stokhareketi',
            old_name='kullanici',
            new_name='olusturan',
        ),
        migrations.AddField(
            model_name='stokhareketi',
            name='islem_turu',
            field=models.CharField(choices=[('giriş', 'Giriş'), ('çıkış', 'Çıkış')], default='giriş', max_length=10, verbose_name='İşlem Türü'),
        ),
        migrations.RunPython(migrate_hareket_tipi_to_islem_turu, reverse_migrate_islem_turu_to_hareket_tipi),
        migrations.RemoveField(
            model_name='stokhareketi',
            name='hareket_tipi',
        ),
        migrations.AlterField(
            model_name='urun',
            name='fiyat',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Satış Fiyatı'),
        ),
    ]
