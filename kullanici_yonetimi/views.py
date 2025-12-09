from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import json
from fatura.models import Fatura, FaturaKalem


@login_required
def index(request):
    """Kullanıcı yönetimi ana sayfası - Tüm kullanıcıların performans analizi"""
    kullanicilar = User.objects.filter(is_active=True).order_by('username')
    
    # Tarih filtresi
    tarih_baslangic = request.GET.get('tarih_baslangic', '')
    tarih_bitis = request.GET.get('tarih_bitis', '')
    
    from datetime import datetime as dt
    if not tarih_baslangic:
        tarih_baslangic = (timezone.now() - timedelta(days=30)).date()
    else:
        tarih_baslangic = dt.strptime(tarih_baslangic, '%Y-%m-%d').date()
    
    if not tarih_bitis:
        tarih_bitis = timezone.now().date()
    else:
        tarih_bitis = dt.strptime(tarih_bitis, '%Y-%m-%d').date()
    
    kullanici_istatistikleri = []
    
    for kullanici in kullanicilar:
        # Satış faturaları
        satis_faturalari = Fatura.objects.filter(
            olusturan=kullanici,
            fatura_tipi='Satis',
            fatura_tarihi__gte=tarih_baslangic,
            fatura_tarihi__lte=tarih_bitis
        )
        
        # Toplam satış tutarı
        toplam_satis = satis_faturalari.aggregate(
            toplam=Sum('genel_toplam')
        )['toplam'] or Decimal('0.00')
        
        # Toplam fatura sayısı
        fatura_sayisi = satis_faturalari.count()
        
        # Toplam ürün adedi (kalemlerden)
        toplam_urun_adedi = FaturaKalem.objects.filter(
            fatura__olusturan=kullanici,
            fatura__fatura_tipi='Satis',
            fatura__fatura_tarihi__gte=tarih_baslangic,
            fatura__fatura_tarihi__lte=tarih_bitis
        ).aggregate(
            toplam=Sum('miktar')
        )['toplam'] or 0
        
        # Ortalama fatura tutarı
        ortalama_fatura = toplam_satis / fatura_sayisi if fatura_sayisi > 0 else Decimal('0.00')
        
        # Bu ay satış
        bu_ay_baslangic = timezone.now().replace(day=1).date()
        bu_ay_satis = Fatura.objects.filter(
            olusturan=kullanici,
            fatura_tipi='Satis',
            fatura_tarihi__gte=bu_ay_baslangic
        ).aggregate(
            toplam=Sum('genel_toplam')
        )['toplam'] or Decimal('0.00')
        
        kullanici_istatistikleri.append({
            'kullanici': kullanici,
            'toplam_satis': toplam_satis,
            'fatura_sayisi': fatura_sayisi,
            'toplam_urun_adedi': toplam_urun_adedi,
            'ortalama_fatura': ortalama_fatura,
            'bu_ay_satis': bu_ay_satis,
        })
    
    # Sıralama
    siralama = request.GET.get('siralama', 'toplam_satis')
    if siralama == 'toplam_satis':
        kullanici_istatistikleri.sort(key=lambda x: x['toplam_satis'], reverse=True)
    elif siralama == 'fatura_sayisi':
        kullanici_istatistikleri.sort(key=lambda x: x['fatura_sayisi'], reverse=True)
    elif siralama == 'ortalama_fatura':
        kullanici_istatistikleri.sort(key=lambda x: x['ortalama_fatura'], reverse=True)
    
    # Genel istatistikler
    toplam_satis_genel = sum(ist['toplam_satis'] for ist in kullanici_istatistikleri)
    toplam_fatura_genel = sum(ist['fatura_sayisi'] for ist in kullanici_istatistikleri)
    ortalama_satis_genel = toplam_satis_genel / len(kullanici_istatistikleri) if kullanici_istatistikleri else Decimal('0.00')
    
    context = {
        'kullanici_istatistikleri': kullanici_istatistikleri,
        'tarih_baslangic': tarih_baslangic.strftime('%Y-%m-%d'),
        'tarih_bitis': tarih_bitis.strftime('%Y-%m-%d'),
        'siralama': siralama,
        'toplam_satis_genel': toplam_satis_genel,
        'toplam_fatura_genel': toplam_fatura_genel,
        'ortalama_satis_genel': ortalama_satis_genel,
    }
    return render(request, 'kullanici_yonetimi/index.html', context)


@login_required
def kullanici_detay(request, user_id):
    """Kullanıcı detay sayfası - Kullanıcının detaylı performans analizi"""
    kullanici = get_object_or_404(User, pk=user_id)
    
    # Tarih filtresi
    tarih_baslangic = request.GET.get('tarih_baslangic', '')
    tarih_bitis = request.GET.get('tarih_bitis', '')
    
    from datetime import datetime as dt
    if not tarih_baslangic:
        tarih_baslangic = (timezone.now() - timedelta(days=30)).date()
    else:
        tarih_baslangic = dt.strptime(tarih_baslangic, '%Y-%m-%d').date()
    
    if not tarih_bitis:
        tarih_bitis = timezone.now().date()
    else:
        tarih_bitis = dt.strptime(tarih_bitis, '%Y-%m-%d').date()
    
    # Satış faturaları
    satis_faturalari = Fatura.objects.filter(
        olusturan=kullanici,
        fatura_tipi='Satis',
        fatura_tarihi__gte=tarih_baslangic,
        fatura_tarihi__lte=tarih_bitis
    ).order_by('-fatura_tarihi')
    
    # İstatistikler
    toplam_satis = satis_faturalari.aggregate(
        toplam=Sum('genel_toplam')
    )['toplam'] or Decimal('0.00')
    
    fatura_sayisi = satis_faturalari.count()
    
    toplam_urun_adedi = FaturaKalem.objects.filter(
        fatura__olusturan=kullanici,
        fatura__fatura_tipi='Satis',
        fatura__fatura_tarihi__gte=tarih_baslangic,
        fatura__fatura_tarihi__lte=tarih_bitis
    ).aggregate(
        toplam=Sum('miktar')
    )['toplam'] or 0
    
    ortalama_fatura = toplam_satis / fatura_sayisi if fatura_sayisi > 0 else Decimal('0.00')
    
    # Aylık satış trendi (son 6 ay)
    aylik_satis = []
    for i in range(6):
        ay_tarihi = timezone.now() - timedelta(days=30*i)
        ay_baslangic = ay_tarihi.replace(day=1).date()
        if i == 0:
            ay_bitis = timezone.now().date()
        else:
            sonraki_ay = ay_baslangic + timedelta(days=32)
            ay_bitis = sonraki_ay.replace(day=1) - timedelta(days=1)
        
        ay_satis = Fatura.objects.filter(
            olusturan=kullanici,
            fatura_tipi='Satis',
            fatura_tarihi__gte=ay_baslangic,
            fatura_tarihi__lte=ay_bitis
        ).aggregate(
            toplam=Sum('genel_toplam')
        )['toplam'] or Decimal('0.00')
        
        # Türkçe ay isimleri
        ay_isimleri = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 
                      'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
        ay_adi = ay_isimleri[ay_baslangic.month - 1]
        
        aylik_satis.append({
            'ay': f'{ay_adi} {ay_baslangic.year}',
            'tutar': float(ay_satis)
        })
    
    aylik_satis.reverse()
    
    # En çok satılan ürünler
    en_cok_satilan = FaturaKalem.objects.filter(
        fatura__olusturan=kullanici,
        fatura__fatura_tipi='Satis',
        fatura__fatura_tarihi__gte=tarih_baslangic,
        fatura__fatura_tarihi__lte=tarih_bitis
    ).values('urun_adi').annotate(
        toplam_miktar=Sum('miktar'),
        toplam_tutar=Sum('toplam_tutar')
    ).order_by('-toplam_miktar')[:10]
    
    # En çok satış yapılan cariler
    en_cok_cariler = satis_faturalari.values('cari__ad_soyad').annotate(
        toplam_tutar=Sum('genel_toplam'),
        fatura_sayisi=Count('id')
    ).order_by('-toplam_tutar')[:10]
    
    context = {
        'kullanici': kullanici,
        'satis_faturalari': satis_faturalari[:20],  # Son 20 fatura
        'toplam_satis': toplam_satis,
        'fatura_sayisi': fatura_sayisi,
        'toplam_urun_adedi': toplam_urun_adedi,
        'ortalama_fatura': ortalama_fatura,
        'aylik_satis': json.dumps(aylik_satis),
        'en_cok_satilan': en_cok_satilan,
        'en_cok_cariler': en_cok_cariler,
        'tarih_baslangic': tarih_baslangic.strftime('%Y-%m-%d'),
        'tarih_bitis': tarih_bitis.strftime('%Y-%m-%d'),
    }
    return render(request, 'kullanici_yonetimi/kullanici_detay.html', context)


@login_required
def kullanici_rapor(request, user_id):
    """Kullanıcı detaylı rapor sayfası"""
    kullanici = get_object_or_404(User, pk=user_id)
    
    # Tarih filtresi
    tarih_baslangic = request.GET.get('tarih_baslangic', '')
    tarih_bitis = request.GET.get('tarih_bitis', '')
    
    from datetime import datetime as dt
    if not tarih_baslangic:
        tarih_baslangic = (timezone.now() - timedelta(days=30)).date()
    else:
        tarih_baslangic = dt.strptime(tarih_baslangic, '%Y-%m-%d').date()
    
    if not tarih_bitis:
        tarih_bitis = timezone.now().date()
    else:
        tarih_bitis = dt.strptime(tarih_bitis, '%Y-%m-%d').date()
    
    # Tüm satış faturaları
    satis_faturalari = Fatura.objects.filter(
        olusturan=kullanici,
        fatura_tipi='Satis',
        fatura_tarihi__gte=tarih_baslangic,
        fatura_tarihi__lte=tarih_bitis
    ).order_by('-fatura_tarihi')
    
    context = {
        'kullanici': kullanici,
        'satis_faturalari': satis_faturalari,
        'tarih_baslangic': tarih_baslangic.strftime('%Y-%m-%d'),
        'tarih_bitis': tarih_bitis.strftime('%Y-%m-%d'),
    }
    return render(request, 'kullanici_yonetimi/kullanici_rapor.html', context)
