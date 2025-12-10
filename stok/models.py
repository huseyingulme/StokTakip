from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum, Q
from django.core.exceptions import ValidationError


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
    alis_fiyati = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Alış Fiyatı (₺)")
    fiyat = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Satış Fiyatı (₺)")
    min_stok_adedi = models.IntegerField(default=0, verbose_name="Minimum Stok Seviyesi", editable=False)
    resim = models.ImageField(upload_to='urunler/', blank=True, null=True, verbose_name="Ürün Resmi")
    qr_kod = models.ImageField(upload_to='qr_kodlar/', blank=True, null=True, verbose_name="QR Kod")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")

    class Meta:
        verbose_name = "Ürün"
        verbose_name_plural = "Ürünler"
        ordering = ['ad']
        db_table = 'stok_urun'
        indexes = [
            models.Index(fields=['ad'], name='urun_ad_idx'),
        ]

    def __str__(self):
        return self.ad
    
    def clean(self):
        """Model-level validation for Urun."""
        errors = {}
        
        # Alış fiyatı kontrolü
        if self.alis_fiyati < 0:
            errors['alis_fiyati'] = 'Alış fiyatı negatif olamaz.'
        
        # Satış fiyatı kontrolü
        if self.fiyat < 0:
            errors['fiyat'] = 'Satış fiyatı negatif olamaz.'
        
        # Barkod unique kontrolü (form'da var ama model'de de olmalı)
        if self.barkod:
            existing = Urun.objects.filter(barkod=self.barkod).exclude(pk=self.pk)
            if existing.exists():
                errors['barkod'] = 'Bu barkod numarası zaten kullanılıyor.'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        # Minimum stok seviyesi her zaman 0 olacak
        self.min_stok_adedi = 0
        self.full_clean()  # clean() metodunu çağır
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
        indexes = [
            models.Index(fields=['tarih'], name='stokhareketi_tarih_idx'),
            models.Index(fields=['islem_turu'], name='stokhareketi_islem_turu_idx'),
            models.Index(fields=['urun', 'tarih'], name='stokhareketi_urun_tarih_idx'),
        ]

    def __str__(self):
        return f"{self.urun.ad} - {self.get_islem_turu_display()} - {self.miktar} {self.urun.birim}"
    
    def clean(self):
        """Model-level validation for StokHareketi."""
        errors = {}
        
        # Miktar kontrolü
        if self.miktar <= 0:
            errors['miktar'] = 'Miktar 0\'dan büyük olmalıdır.'
        
        # Stok kontrolü kaldırıldı - negatif stok olabilir
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        self.full_clean()  # clean() metodunu çağır
        super().save(*args, **kwargs)
