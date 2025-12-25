from django.db import models
from django.contrib.auth.models import User
from cari.models import Cari

class PanelDuyurusu(models.Model):
    baslik = models.CharField(max_length=200, verbose_name="Başlık")
    icerik = models.TextField(verbose_name="İçerik")
    yayin_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Yayın Tarihi")
    aktif = models.BooleanField(default=True, verbose_name="Aktif mi?")
    onemli = models.BooleanField(default=False, verbose_name="Önemli mi?")

    class Meta:
        verbose_name = "Panel Duyurusu"
        verbose_name_plural = "Panel Duyuruları"
        ordering = ['-yayin_tarihi']

    def __str__(self):
        return self.baslik

class Siparis(models.Model):
    DURUM_CHOICES = [
        ('beklemede', 'Onay Bekliyor'),
        ('onaylandi', 'Onaylandı'),
        ('reddedildi', 'Reddedildi'),
        ('faturalandi', 'Faturalandı'),
        ('iptal', 'İptal Edildi'),
    ]

    cari = models.ForeignKey(Cari, on_delete=models.CASCADE, related_name='siparisler', verbose_name="Cari")
    siparis_no = models.CharField(max_length=50, unique=True, verbose_name="Sipariş No")
    durum = models.CharField(max_length=20, choices=DURUM_CHOICES, default='beklemede', verbose_name="Durum")
    notlar = models.TextField(blank=True, null=True, verbose_name="Müşteri Notu")
    toplam_tutar = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Toplam Tutar")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")
    guncelleme_tarihi = models.DateTimeField(auto_now=True, verbose_name="Güncelleme Tarihi")

    class Meta:
        verbose_name = "Sipariş"
        verbose_name_plural = "Siparişler"
        ordering = ['-olusturma_tarihi']

    def __str__(self):
        return f"{self.siparis_no} - {self.cari.ad_soyad}"

    def save(self, *args, **kwargs):
        if not self.siparis_no:
            from datetime import datetime
            import random
            prefix = "SIP"
            tarih_str = datetime.now().strftime("%Y%m%d")
            # Basit bir sipariş numarası üretimi
            count = Siparis.objects.filter(siparis_no__startswith=f"{prefix}-{tarih_str}").count() + 1
            self.siparis_no = f"{prefix}-{tarih_str}-{count:03d}"
        super().save(*args, **kwargs)

    def hesapla_toplam(self):
        self.toplam_tutar = sum(item.toplam_tutar for item in self.kalemler.all())
        Siparis.objects.filter(pk=self.pk).update(toplam_tutar=self.toplam_tutar)

class SiparisKalem(models.Model):
    siparis = models.ForeignKey(Siparis, on_delete=models.CASCADE, related_name='kalemler', verbose_name="Sipariş")
    urun = models.ForeignKey('stok.Urun', on_delete=models.CASCADE, verbose_name="Ürün")
    miktar = models.PositiveIntegerField(default=1, verbose_name="Miktar")
    birim_fiyat = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Birim Fiyat")
    toplam_tutar = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Toplam Tutar")

    class Meta:
        verbose_name = "Sipariş Kalemi"
        verbose_name_plural = "Sipariş Kalemleri"

    def __str__(self):
        return f"{self.siparis.siparis_no} - {self.urun.ad}"

    def save(self, *args, **kwargs):
        self.toplam_tutar = self.miktar * self.birim_fiyat
        super().save(*args, **kwargs)
        self.siparis.hesapla_toplam()
