from django.db import models


class Musteri(models.Model):
    TIP_SECENEKLERI = [
        ('Bireysel', 'Bireysel'),
        ('Kurumsal', 'Kurumsal'),
    ]

    ad_soyad = models.CharField(max_length=100, verbose_name="Ad Soyad")
    unvan = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ünvan")
    tc_vkn = models.CharField(max_length=20, blank=True, null=True, verbose_name="TC/ Vergi No")
    telefon = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefon")
    email = models.EmailField(blank=True, null=True, verbose_name="E-posta")
    adres = models.TextField(blank=True, null=True, verbose_name="Adres")
    sehir = models.CharField(max_length=50, blank=True, null=True, verbose_name="Şehir")
    tip = models.CharField(max_length=20, choices=TIP_SECENEKLERI, default='Bireysel', verbose_name="Tip")
    bakiye = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Bakiye")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")
    guncelleme_tarihi = models.DateTimeField(auto_now=True, verbose_name="Güncelleme Tarihi")

    class Meta:
        verbose_name = "Müşteri"
        verbose_name_plural = "Müşteriler"
        ordering = ['ad_soyad']
        db_table = 'cari_musteri'

    def __str__(self):
        return self.ad_soyad
