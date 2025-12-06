from django.db import models


class Urun(models.Model):
    ad = models.CharField(max_length=100, verbose_name="Ürün Adı")
    barkod = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="Barkod")
    fiyat = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Fiyat")
    stok_adedi = models.IntegerField(default=0, verbose_name="Stok Adedi")
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
