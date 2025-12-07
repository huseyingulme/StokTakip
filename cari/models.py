from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum, Q
from decimal import Decimal


class Cari(models.Model):
    KATEGORI_CHOICES = [
        ('musteri', 'Müşteri'),
        ('tedarikci', 'Tedarikçi'),
        ('her_ikisi', 'Her İkisi'),
    ]

    DURUM_CHOICES = [
        ('aktif', 'Aktif'),
        ('pasif', 'Pasif'),
    ]

    ad_soyad = models.CharField(max_length=200, verbose_name="Ad Soyad / Firma Adı")
    vergi_dairesi = models.CharField(max_length=100, blank=True, null=True, verbose_name="Vergi Dairesi")
    vergi_no = models.CharField(max_length=20, blank=True, null=True, verbose_name="Vergi Numarası")
    tc_vkn = models.CharField(max_length=20, blank=True, null=True, verbose_name="TCKN / VKN")
    telefon = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefon")
    email = models.EmailField(blank=True, null=True, verbose_name="E-posta")
    adres = models.TextField(blank=True, null=True, verbose_name="Adres")
    sehir = models.CharField(max_length=50, blank=True, null=True, verbose_name="Şehir")
    ilce = models.CharField(max_length=50, blank=True, null=True, verbose_name="İlçe")
    kategori = models.CharField(max_length=20, choices=KATEGORI_CHOICES, default='musteri', verbose_name="Kategori")
    durum = models.CharField(max_length=10, choices=DURUM_CHOICES, default='aktif', verbose_name="Durum")
    risk_limiti = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name="Risk Limiti (₺)")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")
    guncelleme_tarihi = models.DateTimeField(auto_now=True, verbose_name="Güncelleme Tarihi")

    class Meta:
        verbose_name = "Cari"
        verbose_name_plural = "Cariler"
        ordering = ['ad_soyad']
        db_table = 'cari_cari'

    def __str__(self):
        return self.ad_soyad

    @property
    def bakiye(self):
        borc_toplam = CariHareketi.objects.filter(
            cari=self,
            hareket_turu__in=['satis_faturasi', 'odeme']
        ).aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0.00')

        alacak_toplam = CariHareketi.objects.filter(
            cari=self,
            hareket_turu__in=['alis_faturasi', 'tahsilat']
        ).aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0.00')

        return borc_toplam - alacak_toplam

    @property
    def risk_asimi_var_mi(self):
        if self.risk_limiti > 0:
            return self.bakiye > self.risk_limiti
        return False

    @property
    def son_islem_tarihi(self):
        son_hareket = CariHareketi.objects.filter(cari=self).order_by('-tarih').first()
        return son_hareket.tarih if son_hareket else None


class CariHareketi(models.Model):
    HAREKET_TURU_CHOICES = [
        ('satis_faturasi', 'Satış Faturası'),
        ('alis_faturasi', 'Alış Faturası'),
        ('tahsilat', 'Tahsilat (Ödeme Alındı)'),
        ('odeme', 'Ödeme (Para Ödendi)'),
        ('iade', 'İade / İptal'),
    ]

    ODEME_YONTEMI_CHOICES = [
        ('nakit', 'Nakit'),
        ('havale', 'Havale'),
        ('kredi_karti', 'Kredi Kartı'),
        ('cek', 'Çek'),
        ('senet', 'Senet'),
    ]

    cari = models.ForeignKey(Cari, on_delete=models.CASCADE, related_name='hareketler', verbose_name="Cari")
    hareket_turu = models.CharField(max_length=20, choices=HAREKET_TURU_CHOICES, verbose_name="Hareket Türü")
    tutar = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Tutar (₺)")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    belge_no = models.CharField(max_length=100, blank=True, null=True, verbose_name="Belge Numarası")
    tarih = models.DateTimeField(verbose_name="Tarih")
    odeme_yontemi = models.CharField(max_length=20, choices=ODEME_YONTEMI_CHOICES, blank=True, null=True, verbose_name="Ödeme Yöntemi")
    olusturan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="İşlemi Yapan")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")

    class Meta:
        verbose_name = "Cari Hareketi"
        verbose_name_plural = "Cari Hareketleri"
        ordering = ['-tarih', '-id']
        db_table = 'cari_carihareketi'

    def __str__(self):
        return f"{self.cari.ad_soyad} - {self.get_hareket_turu_display()} - {self.tutar} ₺"


class CariNotu(models.Model):
    cari = models.ForeignKey(Cari, on_delete=models.CASCADE, related_name='notlar', verbose_name="Cari")
    baslik = models.CharField(max_length=200, verbose_name="Başlık")
    icerik = models.TextField(verbose_name="İçerik")
    olusturan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Oluşturan")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")
    guncelleme_tarihi = models.DateTimeField(auto_now=True, verbose_name="Güncelleme Tarihi")

    class Meta:
        verbose_name = "Cari Notu"
        verbose_name_plural = "Cari Notları"
        ordering = ['-olusturma_tarihi']
        db_table = 'cari_carinotu'

    def __str__(self):
        return f"{self.cari.ad_soyad} - {self.baslik}"


class TahsilatMakbuzu(models.Model):
    ODEME_YONTEMI_CHOICES = [
        ('nakit', 'Nakit'),
        ('havale', 'Havale'),
        ('kredi_karti', 'Kredi Kartı'),
        ('cek', 'Çek'),
        ('senet', 'Senet'),
    ]

    makbuz_no = models.CharField(max_length=50, unique=True, verbose_name="Makbuz No")
    cari = models.ForeignKey(Cari, on_delete=models.CASCADE, related_name='tahsilat_makbuzlari', verbose_name="Cari")
    tutar = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Tutar (₺)")
    odeme_yontemi = models.CharField(max_length=20, choices=ODEME_YONTEMI_CHOICES, verbose_name="Ödeme Yöntemi")
    tarih = models.DateField(verbose_name="Tarih")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    dekont_no = models.CharField(max_length=100, blank=True, null=True, verbose_name="Dekont No")
    olusturan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Oluşturan")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")

    class Meta:
        verbose_name = "Tahsilat Makbuzu"
        verbose_name_plural = "Tahsilat Makbuzları"
        ordering = ['-tarih', '-id']
        db_table = 'cari_tahsilatmakbuzu'

    def __str__(self):
        return f"{self.makbuz_no} - {self.cari.ad_soyad} - {self.tutar} ₺"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        CariHareketi.objects.create(
            cari=self.cari,
            hareket_turu='tahsilat',
            tutar=self.tutar,
            aciklama=f"Tahsilat Makbuzu: {self.makbuz_no}",
            belge_no=self.makbuz_no,
            tarih=self.tarih,
            odeme_yontemi=self.odeme_yontemi,
            olusturan=self.olusturan
        )


class TediyeMakbuzu(models.Model):
    ODEME_YONTEMI_CHOICES = [
        ('nakit', 'Nakit'),
        ('havale', 'Havale'),
        ('kredi_karti', 'Kredi Kartı'),
        ('cek', 'Çek'),
        ('senet', 'Senet'),
    ]

    makbuz_no = models.CharField(max_length=50, unique=True, verbose_name="Makbuz No")
    cari = models.ForeignKey(Cari, on_delete=models.CASCADE, related_name='tediye_makbuzlari', verbose_name="Cari")
    tutar = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Tutar (₺)")
    odeme_yontemi = models.CharField(max_length=20, choices=ODEME_YONTEMI_CHOICES, verbose_name="Ödeme Yöntemi")
    tarih = models.DateField(verbose_name="Tarih")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    dekont_no = models.CharField(max_length=100, blank=True, null=True, verbose_name="Dekont No")
    olusturan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Oluşturan")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")

    class Meta:
        verbose_name = "Tediye Makbuzu"
        verbose_name_plural = "Tediye Makbuzları"
        ordering = ['-tarih', '-id']
        db_table = 'cari_tediyemakbuzu'

    def __str__(self):
        return f"{self.makbuz_no} - {self.cari.ad_soyad} - {self.tutar} ₺"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        CariHareketi.objects.create(
            cari=self.cari,
            hareket_turu='odeme',
            tutar=self.tutar,
            aciklama=f"Tediye Makbuzu: {self.makbuz_no}",
            belge_no=self.makbuz_no,
            tarih=self.tarih,
            odeme_yontemi=self.odeme_yontemi,
            olusturan=self.olusturan
        )
