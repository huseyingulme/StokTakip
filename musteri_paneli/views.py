from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .decorators import musteri_required
from fatura.models import Fatura
from cari.models import CariHareketi
from django.db import transaction, models
from django.db.models import Sum
from decimal import Decimal
from .models import PanelDuyurusu, Siparis, SiparisKalem
from stok.models import Urun
from .forms import MusteriProfilForm
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from fatura.models import Fatura, FaturaKalem
from stoktakip.services.stok_service import create_stok_hareketleri_from_fatura
from stoktakip.services.cari_service import create_or_update_cari_hareketi_from_fatura

def siparis_faturalandir(request, siparis):
    """Siparişi faturalandırıp Fatura modeline aktaran yardımcı fonk."""
    if siparis.durum != 'faturalandi':
        with transaction.atomic():
            fatura = Fatura.objects.create(
                cari=siparis.cari,
                fatura_tarihi=timezone.now().date(),
                fatura_tipi='Satis',
                durum='AcikHesap',
                aciklama=f"Sipariş No: {siparis.siparis_no} üzerinden otomatik oluşturuldu.",
                olusturan=request.user
            )
            for kalem in siparis.kalemler.all():
                FaturaKalem.objects.create(
                    fatura=fatura,
                    urun=kalem.urun,
                    urun_adi=kalem.urun.ad,
                    miktar=kalem.miktar,
                    birim_fiyat=kalem.birim_fiyat,
                    kdv_orani=20
                )
            
            # Fatura toplamlarını hesapla ve hareketleri oluştur
            fatura.refresh_from_db()
            create_stok_hareketleri_from_fatura(fatura, request.user)
            create_or_update_cari_hareketi_from_fatura(fatura, request.user)
            
            siparis.durum = 'faturalandi'
            siparis.save()
            return True
    return False

@musteri_required
def index(request):
    cari = request.user.cari_account

    # Duyurular
    duyurular = PanelDuyurusu.objects.filter(
        aktif=True
    ).order_by('-onemli', '-yayin_tarihi')[:3]

    # Son 5 fatura
    son_faturalar = Fatura.objects.filter(
        cari=cari
    ).order_by('-fatura_tarihi', '-id')[:5]

    # Son 5 hareket
    son_hareketler = CariHareketi.objects.filter(
        cari=cari
    ).order_by('-tarih', '-id')[:5]

    # Finansal özet
    borc_toplam = CariHareketi.objects.filter(
        cari=cari,
        hareket_turu__in=['satis_faturasi', 'odeme']
    ).aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0.00')

    alacak_toplam = CariHareketi.objects.filter(
        cari=cari,
        hareket_turu__in=['alis_faturasi', 'tahsilat']
    ).aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0.00')

    bakiye = borc_toplam - alacak_toplam

    context = {
        'cari': cari,
        'duyurular': duyurular,
        'son_faturalar': son_faturalar,
        'son_hareketler': son_hareketler,

        # 🔑 dashboard için
        'bakiye': bakiye,
        'bakiye_mutlak': abs(bakiye),
        'borc_toplam': borc_toplam,
        'alacak_toplam': alacak_toplam,
    }

    return render(request, 'musteri_paneli/dashboard.html', context)

@musteri_required
def fatura_listesi(request):
    cari = request.user.cari_account
    faturalar = Fatura.objects.filter(cari=cari).order_by('-fatura_tarihi', '-id')
    return render(request, 'musteri_paneli/fatura_listesi.html', {'faturalar': faturalar})

@musteri_required
def fatura_detay(request, pk):
    cari = request.user.cari_account
    fatura = get_object_or_404(Fatura, pk=pk, cari=cari)
    return render(request, 'musteri_paneli/fatura_detay.html', {'fatura': fatura})

@musteri_required
def tahsilat_listesi(request):
    cari = request.user.cari_account
    tahsilatlar = CariHareketi.objects.filter(
        cari=cari, 
        hareket_turu__in=['tahsilat', 'odeme']
    ).order_by('-tarih', '-id')
    return render(request, 'musteri_paneli/tahsilat_listesi.html', {'tahsilatlar': tahsilatlar})

@musteri_required
def ekstre(request):
    cari = request.user.cari_account
    hareketler_sirali = CariHareketi.objects.filter(cari=cari).order_by('tarih', 'id')
    
    ekstre_verisi = []
    yuruyen_bakiye = Decimal('0.00')
    
    for h in hareketler_sirali:
        if h.hareket_turu in ['satis_faturasi', 'odeme']:
            borc = h.tutar
            alacak = Decimal('0.00')
            yuruyen_bakiye += h.tutar
        else:
            borc = Decimal('0.00')
            alacak = h.tutar
            yuruyen_bakiye -= h.tutar
            
        ekstre_verisi.append({
            'obj': h,
            'borc': borc,
            'alacak': alacak,
            'bakiye': yuruyen_bakiye,
            'bakiye_abs': abs(yuruyen_bakiye)
        })
    
    ekstre_verisi.reverse()
    
    return render(request, 'musteri_paneli/ekstre.html', {'ekstre_verisi': ekstre_verisi})

@musteri_required
def profil(request):
    cari = request.user.cari_account
    if request.method == 'POST':
        form = MusteriProfilForm(request.POST, instance=cari, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil bilgileriniz başarıyla güncellendi.")
            return redirect('musteri_paneli:profil')
    else:
        form = MusteriProfilForm(instance=cari, user=request.user)
    
    return render(request, 'musteri_paneli/profil.html', {
        'cari': cari, 
        'form': form,
        'is_customer_panel': True # Sidebar linkleri için ipucu
    })

@musteri_required
def siparis_listesi(request):
    cari = request.user.cari_account
    siparisler = Siparis.objects.filter(cari=cari).order_by('-olusturma_tarihi')
    return render(request, 'musteri_paneli/siparis_listesi.html', {'siparisler': siparisler})

@musteri_required
def siparis_olustur(request):
    cari = request.user.cari_account
    urunler = Urun.objects.all().order_by('ad')
    
    if request.method == 'POST':
        urun_idleri = request.POST.getlist('urun_id')
        miktarlar = request.POST.getlist('miktar')
        notlar = request.POST.get('notlar', '')
        
        valid_items = False
        with transaction.atomic():
            siparis = Siparis.objects.create(cari=cari, notlar=notlar)
            for urun_id, miktar in zip(urun_idleri, miktarlar):
                if int(miktar) > 0:
                    urun = get_object_or_404(Urun, id=urun_id)
                    SiparisKalem.objects.create(
                        siparis=siparis,
                        urun=urun,
                        miktar=int(miktar),
                        birim_fiyat=urun.fiyat
                    )
                    valid_items = True
            
            if not valid_items:
                siparis.delete()
                messages.error(request, "Lütfen en az bir ürün seçiniz.")
                return redirect('musteri_paneli:siparis_olustur')
            
            siparis.hesapla_toplam()
            messages.success(request, "Siparişiniz başarıyla oluşturuldu.")
            return redirect('musteri_paneli:siparis_listesi')
            
    return render(request, 'musteri_paneli/siparis_form.html', {'urunler': urunler})

@musteri_required
def siparis_detay(request, pk):
    cari = request.user.cari_account
    siparis = get_object_or_404(Siparis, pk=pk, cari=cari)
    return render(request, 'musteri_paneli/siparis_detay.html', {'siparis': siparis})


# ===================== ADMIN GÖRÜNÜMLERİ =====================

@staff_member_required
def admin_siparis_listesi(request):
    durum_filter = request.GET.get('durum')
    siparisler = Siparis.objects.all().order_by('-olusturma_tarihi')
    
    if durum_filter:
        siparisler = siparisler.filter(durum=durum_filter)
        
    return render(request, 'musteri_paneli/admin_siparis_listesi.html', {
        'siparisler': siparisler,
        'durum_filter': durum_filter
    })

@staff_member_required
def admin_siparis_islem(request, pk, islem):
    siparis = get_object_or_404(Siparis, pk=pk)
    
    if islem == 'onayla':
        if siparis.durum == 'beklemede':
            siparis.durum = 'onaylandi'
            siparis.save()
            messages.success(request, f"{siparis.siparis_no} onaylandı ve hazırlık aşamasına alındı.")
            
    elif islem == 'reddet':
        if siparis.durum in ['beklemede', 'onaylandi']:
            siparis.durum = 'reddedildi'
            siparis.save()
            messages.warning(request, f"{siparis.siparis_no} reddedildi.")
            
    elif islem == 'faturalandir':
        if siparis.durum in ['beklemede', 'onaylandi']:
            if siparis_faturalandir(request, siparis):
                messages.success(request, f"{siparis.siparis_no} faturalandırıldı.")
            else:
                messages.warning(request, f"{siparis.siparis_no} zaten faturalandırılmış.")
            
    return redirect('musteri_paneli:admin_siparis_listesi')
@staff_member_required
def admin_siparis_detay(request, pk):
    siparis = get_object_or_404(Siparis, pk=pk)
    
    if request.method == 'POST':
        yeni_durum = request.POST.get('durum')
        admin_notu = request.POST.get('admin_notu', '')
        
        if siparis.durum == 'faturalandi':
            messages.warning(request, "Faturalanmış siparişin durumu değiştirilemez.")
            return redirect('musteri_paneli:admin_siparis_detay', pk=pk)

        if yeni_durum in dict(Siparis.DURUM_CHOICES):
            if yeni_durum == 'faturalandi':
                siparis_faturalandir(request, siparis)
            else:
                siparis.durum = yeni_durum
            
            siparis.notlar = admin_notu # Notları güncelle
            siparis.save()
            messages.success(request, f"{siparis.siparis_no} güncellendi.")
            return redirect('musteri_paneli:admin_siparis_detay', pk=pk)
            
    return render(request, 'musteri_paneli/admin_siparis_detay.html', {
        'siparis': siparis
    })
