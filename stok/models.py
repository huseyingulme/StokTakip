from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum, Q


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
    kategori = models.ForeignKey(Kategori, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Kategori")
    ad = models.CharField(max_length=200, verbose_name="Ürün Adı")
    barkod = models.CharField(max_length=100, blank=True, null=True, unique=True, verbose_name="Barkod")
    birim = models.CharField(max_length=20, default='Adet', verbose_name="Birim")
    fiyat = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Satış Fiyatı")
    min_stok_adedi = models.IntegerField(default=0, verbose_name="Minimum Stok Seviyesi", editable=False)
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")

    class Meta:
        verbose_name = "Ürün"
        verbose_name_plural = "Ürünler"
        ordering = ['ad']
        db_table = 'stok_urun'

    def __str__(self):
        return self.ad
    
    def save(self, *args, **kwargs):
        # Minimum stok seviyesi her zaman 0 olacak
        self.min_stok_adedi = 0
        super().save(*args, **kwargs)

    @property
    def mevcut_stok(self):
        giris_toplam = StokHareketi.objects.filter(
            urun=self,
            islem_turu='giriş'
        ).aggregate(toplam=Sum('miktar'))['toplam'] or 0

        cikis_toplam = StokHareketi.objects.filter(
            urun=self,
            islem_turu='çıkış'
        ).aggregate(toplam=Sum('miktar'))['toplam'] or 0

        return giris_toplam - cikis_toplam


class StokHareketi(models.Model):
    ISLEM_TURU_CHOICES = [
        ('giriş', 'Giriş'),
        ('çıkış', 'Çıkış'),
    ]

    urun = models.ForeignKey(Urun, on_delete=models.CASCADE, verbose_name="Ürün")
    islem_turu = models.CharField(max_length=10, choices=ISLEM_TURU_CHOICES, verbose_name="İşlem Türü")
    miktar = models.IntegerField(verbose_name="Miktar")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    tarih = models.DateTimeField(auto_now_add=True, verbose_name="İşlem Tarihi")
    olusturan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="İşlemi Yapan Kullanıcı")

    class Meta:
        verbose_name = "Stok Hareketi"
        verbose_name_plural = "Stok Hareketleri"
        ordering = ['-tarih']
        db_table = 'stok_stokhareketi'

    def __str__(self):
        return f"{self.urun.ad} - {self.get_islem_turu_display()} - {self.miktar} {self.urun.birim}"
