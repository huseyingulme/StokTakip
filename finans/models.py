from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class HesapKart(models.Model):
    HESAP_TIPI_CHOICES = [
        ('banka', 'Banka'),
        ('kasa', 'Kasa'),
        ('kredi_karti', 'Kredi Kartı'),
        ('diger', 'Diğer'),
    ]

    ad = models.CharField(max_length=200, verbose_name="Hesap Adı")
    hesap_tipi = models.CharField(max_length=20, choices=HESAP_TIPI_CHOICES, verbose_name="Hesap Tipi")
    hesap_no = models.CharField(max_length=100, blank=True, null=True, verbose_name="Hesap No")
    bakiye = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Bakiye (₺)")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    durum = models.BooleanField(default=True, verbose_name="Aktif")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")
    guncelleme_tarihi = models.DateTimeField(auto_now=True, verbose_name="Güncelleme Tarihi")

    class Meta:
        verbose_name = "Hesap Kartı"
        verbose_name_plural = "Hesap Kartları"
        ordering = ['ad']
        db_table = 'finans_hesapkart'

    def __str__(self):
        return f"{self.ad} - {self.get_hesap_tipi_display()}"


class FinansHareketi(models.Model):
    HAREKET_TIPI_CHOICES = [
        ('gelir', 'Gelir'),
        ('gider', 'Gider'),
        ('transfer', 'Transfer'),
    ]

    hareket_no = models.CharField(max_length=50, unique=True, verbose_name="Hareket No")
    hesap = models.ForeignKey(HesapKart, on_delete=models.CASCADE, related_name='hareketler', verbose_name="Hesap")
    hedef_hesap = models.ForeignKey(HesapKart, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfer_hareketleri', verbose_name="Hedef Hesap")
    hareket_tipi = models.CharField(max_length=20, choices=HAREKET_TIPI_CHOICES, verbose_name="Hareket Tipi")
    tutar = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Tutar (₺)")
    aciklama = models.TextField(verbose_name="Açıklama")
    tarih = models.DateField(verbose_name="Tarih")
    belge_no = models.CharField(max_length=100, blank=True, null=True, verbose_name="Belge No")
    olusturan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Oluşturan")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")

    class Meta:
        verbose_name = "Finans Hareketi"
        verbose_name_plural = "Finans Hareketleri"
        ordering = ['-tarih', '-id']
        db_table = 'finans_finanshareketi'

    def __str__(self):
        return f"{self.hareket_no} - {self.get_hareket_tipi_display()} - {self.tutar} ₺"
