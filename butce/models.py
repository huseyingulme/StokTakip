from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class ButceKategori(models.Model):
    ad = models.CharField(max_length=100, verbose_name="Kategori Adı")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")

    class Meta:
        verbose_name = "Bütçe Kategorisi"
        verbose_name_plural = "Bütçe Kategorileri"
        ordering = ['ad']
        db_table = 'butce_butcekategori'

    def __str__(self):
        return self.ad


class Butce(models.Model):
    DONEM_CHOICES = [
        ('aylik', 'Aylık'),
        ('yillik', 'Yıllık'),
        ('ozel', 'Özel'),
    ]

    baslik = models.CharField(max_length=200, verbose_name="Başlık")
    kategori = models.ForeignKey(ButceKategori, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Kategori")
    donem = models.CharField(max_length=20, choices=DONEM_CHOICES, verbose_name="Dönem")
    baslangic_tarihi = models.DateField(verbose_name="Başlangıç Tarihi")
    bitis_tarihi = models.DateField(verbose_name="Bitiş Tarihi")
    butce_tutari = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Bütçe Tutarı (₺)")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    olusturan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Oluşturan")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")
    guncelleme_tarihi = models.DateTimeField(auto_now=True, verbose_name="Güncelleme Tarihi")

    class Meta:
        verbose_name = "Bütçe"
        verbose_name_plural = "Bütçeler"
        ordering = ['-baslangic_tarihi']
        db_table = 'butce_butce'

    def __str__(self):
        return f"{self.baslik} - {self.butce_tutari} ₺"

    @property
    def kalan_butce(self):
        from masraf.models import Masraf
        from django.db.models import Sum
        harcanan = Masraf.objects.filter(
            tarih__gte=self.baslangic_tarihi,
            tarih__lte=self.bitis_tarihi,
            durum='odendi'
        ).aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0.00')
        return self.butce_tutari - harcanan
