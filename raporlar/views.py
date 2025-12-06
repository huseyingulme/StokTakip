from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from stok.models import Urun
from cari.models import Musteri
from fatura.models import Fatura


@login_required
def dashboard(request):
    """Ana dashboard sayfası - Genel istatistikler"""
    
    # Stok istatistikleri
    toplam_urun_sayisi = Urun.objects.count()
    dusuk_stoklu_urunler = Urun.objects.filter(stok_adedi__lt=10).count()
    stoksuz_urunler = Urun.objects.filter(stok_adedi=0).count()
    # Toplam stok değeri hesaplama
    toplam_stok_degeri = sum(urun.fiyat * urun.stok_adedi for urun in Urun.objects.all())
    
    # Müşteri istatistikleri
    toplam_musteri_sayisi = Musteri.objects.count()
    bireysel_musteri = Musteri.objects.filter(tip='Bireysel').count()
    kurumsal_musteri = Musteri.objects.filter(tip='Kurumsal').count()
    toplam_alacak = Musteri.objects.aggregate(
        toplam=Sum('bakiye')
    )['toplam'] or 0
    
    # Fatura istatistikleri
    toplam_fatura_sayisi = Fatura.objects.count()
    bu_ay_fatura = Fatura.objects.filter(
        fatura_tarihi__year=timezone.now().year,
        fatura_tarihi__month=timezone.now().month
    ).count()
    
    bu_ay_ciro = Fatura.objects.filter(
        fatura_tarihi__year=timezone.now().year,
        fatura_tarihi__month=timezone.now().month,
        durum='Odendi'
    ).aggregate(
        toplam=Sum('genel_toplam')
    )['toplam'] or 0
    
    bekleyen_faturalar = Fatura.objects.filter(durum='Beklemede').count()
    
    # Son eklenenler
    son_urunler = Urun.objects.all().order_by('-olusturma_tarihi')[:5]
    son_musteriler = Musteri.objects.all().order_by('-olusturma_tarihi')[:5]
    son_faturalar = Fatura.objects.all().order_by('-olusturma_tarihi')[:5]
    
    context = {
        # Stok
        'toplam_urun_sayisi': toplam_urun_sayisi,
        'dusuk_stoklu_urunler': dusuk_stoklu_urunler,
        'stoksuz_urunler': stoksuz_urunler,
        'toplam_stok_degeri': toplam_stok_degeri,
        
        # Müşteri
        'toplam_musteri_sayisi': toplam_musteri_sayisi,
        'bireysel_musteri': bireysel_musteri,
        'kurumsal_musteri': kurumsal_musteri,
        'toplam_alacak': toplam_alacak,
        
        # Fatura
        'toplam_fatura_sayisi': toplam_fatura_sayisi,
        'bu_ay_fatura': bu_ay_fatura,
        'bu_ay_ciro': bu_ay_ciro,
        'bekleyen_faturalar': bekleyen_faturalar,
        
        # Son eklenenler
        'son_urunler': son_urunler,
        'son_musteriler': son_musteriler,
        'son_faturalar': son_faturalar,
    }
    
    return render(request, 'raporlar/dashboard.html', context)
