from django.db import models
from django.contrib.auth.models import User


class Kategori(models.Model):
    ad = models.CharField(max_length=100, verbose_name="Kategori Adı")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")

    class Meta:
        verbose_name = "Kategori"
        verbose_name_plural = "Kategoriler"
        ordering = ['ad']
        db_table = 'stok_kategori'

    def __str__(self):
        return self.ad


class Urun(models.Model):
    ad = models.CharField(max_length=200, verbose_name="Ürün Adı")
    kategori = models.ForeignKey(Kategori, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Kategori")
    stok_adedi = models.IntegerField(default=0, verbose_name="Stok Miktarı")
    fiyat = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Birim Fiyatı")
    barkod = models.CharField(max_length=100, blank=True, null=True, unique=True, verbose_name="Barkod")
    birim = models.CharField(max_length=20, default='Adet', verbose_name="Birim")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")
    guncelleme_tarihi = models.DateTimeField(auto_now=True, verbose_name="Güncelleme Tarihi")

    class Meta:
        verbose_name = "Ürün"
        verbose_name_plural = "Ürünler"
        ordering = ['ad']
        db_table = 'stok_urun'

    def __str__(self):
        return self.ad


class StokHareketi(models.Model):
    HAREKET_TIPLERI = [
        ('IN', 'Stok Girişi'),
        ('OUT', 'Stok Çıkışı'),
    ]

    urun = models.ForeignKey(Urun, on_delete=models.CASCADE, verbose_name="Ürün")
    hareket_tipi = models.CharField(max_length=3, choices=HAREKET_TIPLERI, verbose_name="İşlem Tipi")
    miktar = models.IntegerField(verbose_name="Miktar")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="İşlem Tarihi")
    kullanici = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Kullanıcı")

    class Meta:
        verbose_name = "Stok Hareketi"
        verbose_name_plural = "Stok Hareketleri"
        ordering = ['-olusturma_tarihi']
        db_table = 'stok_stokhareketi'

    def __str__(self):
        return f"{self.urun.ad} - {self.get_hareket_tipi_display()}"
