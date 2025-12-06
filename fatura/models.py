from django.db import models
from cari.models import Musteri
from stok.models import Urun


class Fatura(models.Model):
    TIP_SECENEKLERI = [
        ('Satis', 'Satış'),
        ('Alis', 'Alış'),
    ]

    DURUM_SECENEKLERI = [
        ('Beklemede', 'Beklemede'),
        ('Odendi', 'Ödendi'),
        ('Iptal', 'İptal'),
    ]

    fatura_no = models.CharField(max_length=50, unique=True, verbose_name="Fatura No")
    musteri = models.ForeignKey(Musteri, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Müşteri")
    fatura_tarihi = models.DateField(verbose_name="Fatura Tarihi")
    vade_tarihi = models.DateField(blank=True, null=True, verbose_name="Vade Tarihi")
    toplam_tutar = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Toplam Tutar")
    kdv_tutari = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="KDV Tutarı")
    genel_toplam = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Genel Toplam")
    fatura_tipi = models.CharField(max_length=20, choices=TIP_SECENEKLERI, default='Satis', verbose_name="Fatura Tipi")
    durum = models.CharField(max_length=20, choices=DURUM_SECENEKLERI, default='Beklemede', verbose_name="Durum")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")
    guncelleme_tarihi = models.DateTimeField(auto_now=True, verbose_name="Güncelleme Tarihi")

    class Meta:
        verbose_name = "Fatura"
        verbose_name_plural = "Faturalar"
        ordering = ['-fatura_tarihi', '-olusturma_tarihi']
        db_table = 'fatura_fatura'

    def __str__(self):
        return f"{self.fatura_no} - {self.fatura_tarihi}"


class FaturaKalem(models.Model):
    fatura = models.ForeignKey(Fatura, on_delete=models.CASCADE, related_name='kalemler', verbose_name="Fatura")
    urun = models.ForeignKey(Urun, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ürün")
    urun_adi = models.CharField(max_length=100, verbose_name="Ürün Adı")
    miktar = models.IntegerField(default=1, verbose_name="Miktar")
    birim_fiyat = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Birim Fiyat")
    kdv_orani = models.IntegerField(default=20, verbose_name="KDV Oranı (%)")
    kdv_tutari = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="KDV Tutarı")
    toplam_tutar = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Toplam Tutar")
    sira_no = models.IntegerField(default=1, verbose_name="Sıra No")

    class Meta:
        verbose_name = "Fatura Kalemi"
        verbose_name_plural = "Fatura Kalemleri"
        ordering = ['sira_no']
        db_table = 'fatura_faturakalem'

    def __str__(self):
        return f"{self.fatura.fatura_no} - {self.urun_adi}"
