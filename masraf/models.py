from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal


class MasrafKategori(models.Model):
    ad = models.CharField(max_length=100, verbose_name="Kategori Adı")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")

    class Meta:
        verbose_name = "Masraf Kategorisi"
        verbose_name_plural = "Masraf Kategorileri"
        ordering = ['ad']
        db_table = 'masraf_masrafkategori'

    def __str__(self):
        return self.ad


class Masraf(models.Model):
    ODEME_YONTEMI_CHOICES = [
        ('nakit', 'Nakit'),
        ('havale', 'Havale'),
        ('kredi_karti', 'Kredi Kartı'),
        ('cek', 'Çek'),
    ]

    DURUM_CHOICES = [
        ('odendi', 'Ödendi'),
        ('beklemede', 'Beklemede'),
        ('iptal', 'İptal'),
    ]

    masraf_no = models.CharField(max_length=50, unique=True, verbose_name="Masraf No")
    kategori = models.ForeignKey(MasrafKategori, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Kategori")
    aciklama = models.TextField(verbose_name="Açıklama")
    tutar = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Tutar (₺)")
    tarih = models.DateField(verbose_name="Tarih")
    odeme_yontemi = models.CharField(max_length=20, choices=ODEME_YONTEMI_CHOICES, verbose_name="Ödeme Yöntemi")
    durum = models.CharField(max_length=20, choices=DURUM_CHOICES, default='beklemede', verbose_name="Durum")
    belge_no = models.CharField(max_length=100, blank=True, null=True, verbose_name="Belge No")
    olusturan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Oluşturan")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")
    guncelleme_tarihi = models.DateTimeField(auto_now=True, verbose_name="Güncelleme Tarihi")

    class Meta:
        verbose_name = "Masraf"
        verbose_name_plural = "Masraflar"
        ordering = ['-tarih', '-id']
        db_table = 'masraf_masraf'

    def __str__(self):
        return f"{self.masraf_no} - {self.aciklama[:50]} - {self.tutar} ₺"
    
    def clean(self):
        """Model-level validation for Masraf."""
        errors = {}
        
        # Tutar kontrolü
        if self.tutar < 0:
            errors['tutar'] = 'Tutar negatif olamaz.'
        
        # Tarih gelecek tarih kontrolü
        if self.tarih and self.tarih > timezone.now().date():
            errors['tarih'] = 'Gelecek tarih seçilemez.'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        self.full_clean()  # clean() metodunu çağır
        super().save(*args, **kwargs)
