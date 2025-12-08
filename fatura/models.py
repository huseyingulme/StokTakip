from django.db import models
from django.utils import timezone
from django.db.models import Sum
from django.contrib.auth.models import User
from datetime import datetime, time
from decimal import Decimal
from cari.models import Cari, CariHareketi
from stok.models import Urun, StokHareketi


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

    fatura_no = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="Fatura No")
    cari = models.ForeignKey(Cari, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Cari")
    fatura_tarihi = models.DateField(verbose_name="Fatura Tarihi")
    vade_tarihi = models.DateField(blank=True, null=True, verbose_name="Vade Tarihi")
    toplam_tutar = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Toplam Tutar")
    kdv_tutari = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="KDV Tutarı")
    genel_toplam = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Genel Toplam")
    fatura_tipi = models.CharField(max_length=20, choices=TIP_SECENEKLERI, default='Satis', verbose_name="Fatura Tipi")
    durum = models.CharField(max_length=20, choices=DURUM_SECENEKLERI, default='Beklemede', verbose_name="Durum")
    iskonto_orani = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), verbose_name="İskonto Oranı (%)")
    iskonto_tutari = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="İskonto Tutarı")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    olusturan = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Oluşturan")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")
    guncelleme_tarihi = models.DateTimeField(auto_now=True, verbose_name="Güncelleme Tarihi")

    class Meta:
        verbose_name = "Fatura"
        verbose_name_plural = "Faturalar"
        ordering = ['-fatura_tarihi', '-olusturma_tarihi']
        db_table = 'fatura_fatura'

    def __str__(self):
        return f"{self.fatura_no} - {self.fatura_tarihi}"
    
    def olustur_fatura_no(self):
        from django.db.models import Max
        from datetime import datetime
        
        prefix = 'SATIS' if self.fatura_tipi == 'Satis' else 'ALIS'
        yil = self.fatura_tarihi.year if self.fatura_tarihi else datetime.now().year
        ay = self.fatura_tarihi.month if self.fatura_tarihi else datetime.now().month
        gun = self.fatura_tarihi.day if self.fatura_tarihi else datetime.now().day
        
        tarih_str = f"{yil}{ay:02d}{gun:02d}"
        arama_pattern = f"{prefix}-{tarih_str}-"
        
        son_fatura = Fatura.objects.filter(
            fatura_no__startswith=arama_pattern
        ).aggregate(Max('fatura_no'))
        
        if son_fatura['fatura_no__max']:
            try:
                son_no_str = son_fatura['fatura_no__max'].split('-')[-1]
                son_no = int(son_no_str)
                yeni_no = son_no + 1
            except (ValueError, IndexError):
                yeni_no = 1
        else:
            yeni_no = 1
        
        return f"{prefix}-{tarih_str}-{yeni_no:03d}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        olusturan_user = kwargs.pop('olusturan_user', None)
        
        if is_new and not self.fatura_no:
            self.fatura_no = self.olustur_fatura_no()
        
        super().save(*args, **kwargs)
        self.hesapla_toplamlar()
        
        if self.cari and self.genel_toplam > 0:
            hareket_turu = 'satis_faturasi' if self.fatura_tipi == 'Satis' else 'alis_faturasi'
            
            if is_new:
                CariHareketi.objects.create(
                    cari=self.cari,
                    hareket_turu=hareket_turu,
                    tutar=self.genel_toplam,
                    aciklama=f"Fatura: {self.fatura_no}",
                    belge_no=self.fatura_no,
                    tarih=datetime.combine(self.fatura_tarihi, time.min),
                    olusturan=self.olusturan
                )
            else:
                cari_hareket = CariHareketi.objects.filter(belge_no=self.fatura_no).first()
                if cari_hareket:
                    cari_hareket.tutar = self.genel_toplam
                    cari_hareket.tarih = datetime.combine(self.fatura_tarihi, time.min)
                    cari_hareket.aciklama = f"Fatura: {self.fatura_no}"
                    cari_hareket.save()
                else:
                    CariHareketi.objects.create(
                        cari=self.cari,
                        hareket_turu=hareket_turu,
                        tutar=self.genel_toplam,
                        aciklama=f"Fatura: {self.fatura_no}",
                        belge_no=self.fatura_no,
                        tarih=datetime.combine(self.fatura_tarihi, time.min),
                        olusturan=self.olusturan
                    )
            
            if is_new:
                for kalem in self.kalemler.all():
                    if kalem.urun:
                        stok_islem_turu = 'giriş' if self.fatura_tipi == 'Alis' else 'çıkış'
                        StokHareketi.objects.create(
                            urun=kalem.urun,
                            islem_turu=stok_islem_turu,
                            miktar=kalem.miktar,
                            aciklama=f"Fatura: {self.fatura_no}",
                            tarih=datetime.combine(self.fatura_tarihi, time.min),
                            olusturan=olusturan_user or self.olusturan
                        )
            else:
                StokHareketi.objects.filter(aciklama__startswith=f"Fatura: {self.fatura_no}").delete()
                for kalem in self.kalemler.all():
                    if kalem.urun:
                        stok_islem_turu = 'giriş' if self.fatura_tipi == 'Alis' else 'çıkış'
                        StokHareketi.objects.create(
                            urun=kalem.urun,
                            islem_turu=stok_islem_turu,
                            miktar=kalem.miktar,
                            aciklama=f"Fatura: {self.fatura_no}",
                            tarih=datetime.combine(self.fatura_tarihi, time.min),
                            olusturan=olusturan_user or self.olusturan
                        )

    def hesapla_toplamlar(self):
        kalemler = self.kalemler.all()
        toplam_tutar = kalemler.aggregate(toplam=Sum('toplam_tutar'))['toplam'] or Decimal('0.00')
        kdv_tutari = kalemler.aggregate(toplam=Sum('kdv_tutari'))['toplam'] or Decimal('0.00')
        
        iskonto_tutari = Decimal('0.00')
        if self.iskonto_orani > 0:
            iskonto_tutari = toplam_tutar * (self.iskonto_orani / Decimal('100'))
        
        genel_toplam = toplam_tutar + kdv_tutari - iskonto_tutari
        
        Fatura.objects.filter(pk=self.pk).update(
            toplam_tutar=toplam_tutar,
            kdv_tutari=kdv_tutari,
            iskonto_tutari=iskonto_tutari,
            genel_toplam=genel_toplam
        )
        self.refresh_from_db()


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

    def save(self, *args, **kwargs):
        from decimal import Decimal
        ara_toplam = Decimal(str(self.birim_fiyat)) * Decimal(str(self.miktar))
        self.kdv_tutari = ara_toplam * (Decimal(str(self.kdv_orani)) / Decimal('100'))
        self.toplam_tutar = ara_toplam
        
        if not self.sira_no or self.sira_no == 0:
            max_sira = FaturaKalem.objects.filter(fatura=self.fatura).aggregate(
                max_sira=models.Max('sira_no')
            )['max_sira'] or 0
            self.sira_no = max_sira + 1
        
        super().save(*args, **kwargs)
        if self.fatura_id:
            self.fatura.hesapla_toplamlar()
