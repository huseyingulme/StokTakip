from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.http import HttpResponse
from datetime import datetime, timedelta
from decimal import Decimal
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from stok.models import Urun, StokHareketi
from cari.models import Cari, CariHareketi
from fatura.models import Fatura, FaturaKalem
from accounts.utils import log_action
from .utils import create_excel_file, create_excel_response


@login_required
def dashboard(request):
    """Ana dashboard sayfası - Genel istatistikler"""
    
    # Stok istatistikleri
    toplam_urun_sayisi = Urun.objects.count()
    dusuk_stoklu_urunler = 0  # Min stok her zaman 0 olduğu için düşük stok uyarısı yok
    stoksuz_urunler = sum(1 for u in Urun.objects.all() if u.mevcut_stok == 0)
    toplam_stok_degeri = sum(urun.fiyat * urun.mevcut_stok for urun in Urun.objects.all())
    
    # Cari istatistikleri
    toplam_cari_sayisi = Cari.objects.filter(durum='aktif').count()
    musteri_sayisi = Cari.objects.filter(durum='aktif', kategori__in=['musteri', 'her_ikisi']).count()
    tedarikci_sayisi = Cari.objects.filter(durum='aktif', kategori__in=['tedarikci', 'her_ikisi']).count()
    toplam_alacak = sum(cari.bakiye for cari in Cari.objects.filter(durum='aktif') if cari.bakiye > 0)
    
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
    
    son_6_ay = []
    for i in range(6):
        ay_tarihi = timezone.now() - timedelta(days=30*i)
        ay_baslangic = ay_tarihi.replace(day=1)
        if i == 0:
            ay_bitis = timezone.now()
        else:
            sonraki_ay = ay_baslangic + timedelta(days=32)
            ay_bitis = sonraki_ay.replace(day=1) - timedelta(days=1)
        
        satis_tutar = Fatura.objects.filter(
            fatura_tipi='Satis',
            fatura_tarihi__gte=ay_baslangic.date(),
            fatura_tarihi__lte=ay_bitis.date()
        ).aggregate(toplam=Sum('genel_toplam'))['toplam'] or Decimal('0.00')
        
        son_6_ay.append({
            'ay': ay_baslangic.strftime('%Y-%m'),
            'ay_adi': ay_baslangic.strftime('%B %Y'),
            'satis': float(satis_tutar)
        })
    
    son_6_ay.reverse()
    
    urun_kategori_dagilimi = {}
    for urun in Urun.objects.select_related('kategori'):
        kategori_adi = urun.kategori.ad if urun.kategori else 'Kategorisiz'
        if kategori_adi not in urun_kategori_dagilimi:
            urun_kategori_dagilimi[kategori_adi] = 0
        urun_kategori_dagilimi[kategori_adi] += 1
    
    son_eklenenler = Urun.objects.all().order_by('-olusturma_tarihi')[:5]
    son_cariler = Cari.objects.filter(durum='aktif').order_by('-olusturma_tarihi')[:5]
    son_faturalar = Fatura.objects.all().order_by('-olusturma_tarihi')[:5]
    
    bugun = timezone.now().date()
    bu_hafta_baslangic = bugun - timedelta(days=bugun.weekday())
    gecen_hafta_baslangic = bu_hafta_baslangic - timedelta(days=7)
    gecen_hafta_bitis = bu_hafta_baslangic - timedelta(days=1)
    
    bugun_satis = Fatura.objects.filter(
        fatura_tipi='Satis',
        fatura_tarihi=bugun
    ).aggregate(toplam=Sum('genel_toplam'))['toplam'] or Decimal('0.00')
    
    bu_hafta_satis = Fatura.objects.filter(
        fatura_tipi='Satis',
        fatura_tarihi__gte=bu_hafta_baslangic
    ).aggregate(toplam=Sum('genel_toplam'))['toplam'] or Decimal('0.00')
    
    gecen_hafta_satis = Fatura.objects.filter(
        fatura_tipi='Satis',
        fatura_tarihi__gte=gecen_hafta_baslangic,
        fatura_tarihi__lte=gecen_hafta_bitis
    ).aggregate(toplam=Sum('genel_toplam'))['toplam'] or Decimal('0.00')
    
    gecen_ay_baslangic = (bugun.replace(day=1) - timedelta(days=1)).replace(day=1)
    gecen_ay_bitis = bugun.replace(day=1) - timedelta(days=1)
    
    gecen_ay_ciro = Fatura.objects.filter(
        fatura_tipi='Satis',
        fatura_tarihi__gte=gecen_ay_baslangic,
        fatura_tarihi__lte=gecen_ay_bitis,
        durum='Odendi'
    ).aggregate(toplam=Sum('genel_toplam'))['toplam'] or Decimal('0.00')
    
    en_cok_satan_urunler = FaturaKalem.objects.filter(
        fatura__fatura_tipi='Satis',
        fatura__fatura_tarihi__year=timezone.now().year,
        fatura__fatura_tarihi__month=timezone.now().month
    ).values('urun_adi').annotate(
        toplam_miktar=Sum('miktar'),
        toplam_tutar=Sum('toplam_tutar')
    ).order_by('-toplam_miktar')[:5]
    
    vadesi_yaklasan = Fatura.objects.filter(
        vade_tarihi__gte=bugun,
        vade_tarihi__lte=bugun + timedelta(days=7),
        durum='Beklemede'
    ).order_by('vade_tarihi')[:10]
    
    import json
    
    context = {
        'toplam_urun_sayisi': toplam_urun_sayisi,
        'dusuk_stoklu_urunler': dusuk_stoklu_urunler,
        'stoksuz_urunler': stoksuz_urunler,
        'toplam_stok_degeri': toplam_stok_degeri,
        'toplam_cari_sayisi': toplam_cari_sayisi,
        'musteri_sayisi': musteri_sayisi,
        'tedarikci_sayisi': tedarikci_sayisi,
        'toplam_alacak': toplam_alacak,
        'toplam_fatura_sayisi': toplam_fatura_sayisi,
        'bu_ay_fatura': bu_ay_fatura,
        'bu_ay_ciro': bu_ay_ciro,
        'bekleyen_faturalar': bekleyen_faturalar,
        'son_urunler': son_eklenenler,
        'son_cariler': son_cariler,
        'son_faturalar': son_faturalar,
        'son_6_ay_satis': json.dumps(son_6_ay),
        'urun_kategori_dagilimi': json.dumps(urun_kategori_dagilimi),
        'bugun_satis': bugun_satis,
        'bu_hafta_satis': bu_hafta_satis,
        'gecen_hafta_satis': gecen_hafta_satis,
        'gecen_ay_ciro': gecen_ay_ciro,
        'en_cok_satan_urunler': en_cok_satan_urunler,
        'vadesi_yaklasan': vadesi_yaklasan,
    }
    
    return render(request, 'raporlar/dashboard.html', context)


@login_required
def kar_maliyet_raporu(request):
    tarih_baslangic = request.GET.get('tarih_baslangic', '')
    tarih_bitis = request.GET.get('tarih_bitis', '')

    if not tarih_baslangic:
        tarih_baslangic = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not tarih_bitis:
        tarih_bitis = timezone.now().strftime('%Y-%m-%d')

    satis_faturalari = Fatura.objects.filter(
        fatura_tipi='Satis',
        fatura_tarihi__gte=tarih_baslangic,
        fatura_tarihi__lte=tarih_bitis
    )

    alis_faturalari = Fatura.objects.filter(
        fatura_tipi='Alis',
        fatura_tarihi__gte=tarih_baslangic,
        fatura_tarihi__lte=tarih_bitis
    )

    toplam_satis = satis_faturalari.aggregate(toplam=Sum('genel_toplam'))['toplam'] or Decimal('0.00')
    toplam_alis = alis_faturalari.aggregate(toplam=Sum('genel_toplam'))['toplam'] or Decimal('0.00')

    kar = toplam_satis - toplam_alis
    kar_yuzdesi = (kar / toplam_satis * 100) if toplam_satis > 0 else Decimal('0.00')

    satis_detay = []
    for fatura in satis_faturalari:
        for kalem in fatura.kalemler.all():
            satis_detay.append({
                'fatura_no': fatura.fatura_no,
                'tarih': fatura.fatura_tarihi,
                'urun': kalem.urun_adi,
                'miktar': kalem.miktar,
                'birim_fiyat': kalem.birim_fiyat,
                'toplam': kalem.toplam_tutar,
            })

    alis_detay = []
    for fatura in alis_faturalari:
        for kalem in fatura.kalemler.all():
            alis_detay.append({
                'fatura_no': fatura.fatura_no,
                'tarih': fatura.fatura_tarihi,
                'urun': kalem.urun_adi,
                'miktar': kalem.miktar,
                'birim_fiyat': kalem.birim_fiyat,
                'toplam': kalem.toplam_tutar,
            })

    context = {
        'tarih_baslangic': tarih_baslangic,
        'tarih_bitis': tarih_bitis,
        'toplam_satis': toplam_satis,
        'toplam_alis': toplam_alis,
        'kar': kar,
        'kar_yuzdesi': kar_yuzdesi,
        'satis_detay': satis_detay,
        'alis_detay': alis_detay,
    }
    return render(request, 'raporlar/kar_maliyet_raporu.html', context)


@login_required
def alis_raporu(request):
    tarih_baslangic = request.GET.get('tarih_baslangic', '')
    tarih_bitis = request.GET.get('tarih_bitis', '')
    cari_id = request.GET.get('cari', '')

    if not tarih_baslangic:
        tarih_baslangic = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not tarih_bitis:
        tarih_bitis = timezone.now().strftime('%Y-%m-%d')

    faturalar = Fatura.objects.filter(
        fatura_tipi='Alis',
        fatura_tarihi__gte=tarih_baslangic,
        fatura_tarihi__lte=tarih_bitis
    )

    if cari_id:
        faturalar = faturalar.filter(cari_id=cari_id)

    toplam_tutar = faturalar.aggregate(toplam=Sum('genel_toplam'))['toplam'] or Decimal('0.00')
    toplam_kdv = faturalar.aggregate(toplam=Sum('kdv_tutari'))['toplam'] or Decimal('0.00')

    cari_bazli = {}
    for fatura in faturalar:
        cari_adi = fatura.cari.ad_soyad if fatura.cari else 'Cari Yok'
        if cari_adi not in cari_bazli:
            cari_bazli[cari_adi] = {
                'toplam': Decimal('0.00'),
                'fatura_sayisi': 0,
                'faturalar': []
            }
        cari_bazli[cari_adi]['toplam'] += fatura.genel_toplam
        cari_bazli[cari_adi]['fatura_sayisi'] += 1
        cari_bazli[cari_adi]['faturalar'].append(fatura)

    context = {
        'tarih_baslangic': tarih_baslangic,
        'tarih_bitis': tarih_bitis,
        'cari_id': cari_id,
        'cariler': Cari.objects.filter(durum='aktif', kategori__in=['tedarikci', 'her_ikisi']).order_by('ad_soyad'),
        'faturalar': faturalar.order_by('-fatura_tarihi'),
        'toplam_tutar': toplam_tutar,
        'toplam_kdv': toplam_kdv,
        'cari_bazli': cari_bazli,
    }
    return render(request, 'raporlar/alis_raporu.html', context)


@login_required
def satis_raporu(request):
    tarih_baslangic = request.GET.get('tarih_baslangic', '')
    tarih_bitis = request.GET.get('tarih_bitis', '')
    cari_id = request.GET.get('cari', '')

    if not tarih_baslangic:
        tarih_baslangic = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not tarih_bitis:
        tarih_bitis = timezone.now().strftime('%Y-%m-%d')

    faturalar = Fatura.objects.filter(
        fatura_tipi='Satis',
        fatura_tarihi__gte=tarih_baslangic,
        fatura_tarihi__lte=tarih_bitis
    )

    if cari_id:
        faturalar = faturalar.filter(cari_id=cari_id)

    toplam_tutar = faturalar.aggregate(toplam=Sum('genel_toplam'))['toplam'] or Decimal('0.00')
    toplam_kdv = faturalar.aggregate(toplam=Sum('kdv_tutari'))['toplam'] or Decimal('0.00')

    cari_bazli = {}
    for fatura in faturalar:
        cari_adi = fatura.cari.ad_soyad if fatura.cari else 'Cari Yok'
        if cari_adi not in cari_bazli:
            cari_bazli[cari_adi] = {
                'toplam': Decimal('0.00'),
                'fatura_sayisi': 0,
                'faturalar': []
            }
        cari_bazli[cari_adi]['toplam'] += fatura.genel_toplam
        cari_bazli[cari_adi]['fatura_sayisi'] += 1
        cari_bazli[cari_adi]['faturalar'].append(fatura)

    context = {
        'tarih_baslangic': tarih_baslangic,
        'tarih_bitis': tarih_bitis,
        'cari_id': cari_id,
        'cariler': Cari.objects.filter(durum='aktif', kategori__in=['musteri', 'her_ikisi']).order_by('ad_soyad'),
        'faturalar': faturalar.order_by('-fatura_tarihi'),
        'toplam_tutar': toplam_tutar,
        'toplam_kdv': toplam_kdv,
        'cari_bazli': cari_bazli,
    }
    return render(request, 'raporlar/satis_raporu.html', context)


@login_required
def satis_raporu_excel(request):
    tarih_baslangic = request.GET.get('tarih_baslangic', '')
    tarih_bitis = request.GET.get('tarih_bitis', '')
    cari_id = request.GET.get('cari', '')

    if not tarih_baslangic:
        tarih_baslangic = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not tarih_bitis:
        tarih_bitis = timezone.now().strftime('%Y-%m-%d')

    faturalar = Fatura.objects.filter(
        fatura_tipi='Satis',
        fatura_tarihi__gte=tarih_baslangic,
        fatura_tarihi__lte=tarih_bitis
    )

    if cari_id:
        faturalar = faturalar.filter(cari_id=cari_id)

    headers = ['Fatura No', 'Tarih', 'Cari', 'Toplam Tutar', 'KDV', 'Genel Toplam', 'Durum']
    data = []
    for fatura in faturalar:
        data.append([
            fatura.fatura_no,
            fatura.fatura_tarihi.strftime('%d.%m.%Y'),
            fatura.cari.ad_soyad if fatura.cari else '-',
            f'{fatura.toplam_tutar:,.2f}',
            f'{fatura.kdv_tutari:,.2f}',
            f'{fatura.genel_toplam:,.2f}',
            fatura.get_durum_display()
        ])

    wb = create_excel_file(data, headers, f'Satış Raporu ({tarih_baslangic} - {tarih_bitis})')
    response = create_excel_response(f'Satis_Raporu_{datetime.now().strftime("%Y%m%d")}.xlsx')
    wb.save(response)
    log_action(request.user, 'export', description=f'Satış raporu Excel export: {tarih_baslangic} - {tarih_bitis}')
    return response


@login_required
def alis_raporu_excel(request):
    tarih_baslangic = request.GET.get('tarih_baslangic', '')
    tarih_bitis = request.GET.get('tarih_bitis', '')
    cari_id = request.GET.get('cari', '')

    if not tarih_baslangic:
        tarih_baslangic = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not tarih_bitis:
        tarih_bitis = timezone.now().strftime('%Y-%m-%d')

    faturalar = Fatura.objects.filter(
        fatura_tipi='Alis',
        fatura_tarihi__gte=tarih_baslangic,
        fatura_tarihi__lte=tarih_bitis
    )

    if cari_id:
        faturalar = faturalar.filter(cari_id=cari_id)

    headers = ['Fatura No', 'Tarih', 'Cari', 'Toplam Tutar', 'KDV', 'Genel Toplam', 'Durum']
    data = []
    for fatura in faturalar:
        data.append([
            fatura.fatura_no,
            fatura.fatura_tarihi.strftime('%d.%m.%Y'),
            fatura.cari.ad_soyad if fatura.cari else '-',
            f'{fatura.toplam_tutar:,.2f}',
            f'{fatura.kdv_tutari:,.2f}',
            f'{fatura.genel_toplam:,.2f}',
            fatura.get_durum_display()
        ])

    wb = create_excel_file(data, headers, f'Alış Raporu ({tarih_baslangic} - {tarih_bitis})')
    response = create_excel_response(f'Alis_Raporu_{datetime.now().strftime("%Y%m%d")}.xlsx')
    wb.save(response)
    log_action(request.user, 'export', description=f'Alış raporu Excel export: {tarih_baslangic} - {tarih_bitis}')
    return response
