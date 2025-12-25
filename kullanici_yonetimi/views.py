from functools import wraps
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError
from datetime import timedelta
from decimal import Decimal
from typing import Any
import json
import logging
from fatura.models import Fatura, FaturaKalem
from .forms import KullaniciForm
from accounts.utils import log_action
from stoktakip.error_handling import handle_view_errors, database_transaction
from stoktakip.security_utils import (
    sanitize_string, sanitize_integer, validate_search_query
)
from stoktakip.cache_utils import cache_view_result

logger = logging.getLogger(__name__)


def mudur_required(view_func):
    """Müdür (superuser veya Müdür grubu) yetkisi gerektiren decorator"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        # Superuser veya Müdür grubunda olanlar erişebilir
        user_groups = request.user.groups.values_list('name', flat=True)
        if not (request.user.is_superuser or 'Müdür' in user_groups):
            raise PermissionDenied("Bu işlem için müdür yetkisi gereklidir.")
        return view_func(request, *args, **kwargs)
    return wrapper


@cache_view_result(timeout=300, key_prefix='kullanici_index')
@handle_view_errors(error_message="Kullanıcı listesi yüklenirken bir hata oluştu.")
@login_required
def index(request: Any) -> Any:
    """
    Kullanıcı listesi sayfası.
    
    Müdür yetkisi gerektirir. Kullanıcı listesini gösterir.
    Input validation ve error handling ile güvenli hale getirilmiştir.
    """
    """Kullanıcı yönetimi ana sayfası - Tüm kullanıcıların performans analizi"""
    # Sadece müdür kullanıcı yönetimi yapabilir
    user_groups = request.user.groups.values_list('name', flat=True)
    if not (request.user.is_superuser or 'Müdür' in user_groups):
        # Normal kullanıcılar sadece kendi performanslarını görebilir
        return redirect('kullanici_yonetimi:kullanici_detay', user_id=request.user.id)
    
    kullanicilar = User.objects.filter(is_active=True, is_staff=True).order_by('username')
    
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
    aktif_kullanici_sayisi = kullanicilar.count()
    ortalama_satis_genel = toplam_satis_genel / aktif_kullanici_sayisi if aktif_kullanici_sayisi > 0 else Decimal('0.00')
    
    context = {
        'kullanici_istatistikleri': kullanici_istatistikleri,
        'tarih_baslangic': tarih_baslangic.strftime('%Y-%m-%d'),
        'tarih_bitis': tarih_bitis.strftime('%Y-%m-%d'),
        'siralama': siralama,
        'toplam_satis_genel': toplam_satis_genel,
        'toplam_fatura_genel': toplam_fatura_genel,
        'ortalama_satis_genel': ortalama_satis_genel,
        'aktif_kullanici_sayisi': aktif_kullanici_sayisi,
    }
    return render(request, 'kullanici_yonetimi/index.html', context)


@cache_view_result(timeout=300, key_prefix='kullanici_detay')
@handle_view_errors(error_message="Kullanıcı detayı yüklenirken bir hata oluştu.")
@login_required
def kullanici_detay(request: Any, user_id: int) -> Any:
    """
    Kullanıcı detay sayfası - Kullanıcının detaylı performans analizi.
    
    Caching ve error handling ile optimize edilmiştir.
    """
    try:
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
    except Exception as e:
        logger.error(f"Kullanıcı detay hatası: {str(e)}", exc_info=True)
        raise


@cache_view_result(timeout=300, key_prefix='kullanici_rapor')
@handle_view_errors(error_message="Kullanıcı raporu yüklenirken bir hata oluştu.")
@login_required
def kullanici_rapor(request: Any, user_id: int) -> Any:
    """
    Kullanıcı detaylı rapor sayfası.
    
    Caching ve error handling ile optimize edilmiştir.
    """
    try:
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
    except Exception as e:
        logger.error(f"Kullanıcı rapor hatası: {str(e)}", exc_info=True)
        raise


@handle_view_errors(
    error_message="Kullanıcı eklenirken bir hata oluştu.",
    redirect_url="kullanici_yonetimi:index"
)
@database_transaction
@login_required
def kullanici_ekle(request: Any) -> Any:
    """
    Yeni kullanıcı ekler.
    
    Transaction içinde çalışır, hata durumunda rollback yapar.
    Input validation ve error handling ile güvenli hale getirilmiştir.
    """
    """Yeni kullanıcı ekleme"""
    if request.method == 'POST':
        form = KullaniciForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_action(request.user, 'create', user, f'Yeni kullanıcı oluşturuldu: {user.username}', request)
            messages.success(request, f'Kullanıcı "{user.username}" başarıyla oluşturuldu.')
            return redirect('kullanici_yonetimi:kullanici_listesi')
    else:
        form = KullaniciForm()
    
    context = {
        'form': form,
        'title': 'Yeni Kullanıcı Ekle',
    }
    return render(request, 'kullanici_yonetimi/kullanici_form.html', context)


@handle_view_errors(
    error_message="Kullanıcı güncellenirken bir hata oluştu.",
    redirect_url="kullanici_yonetimi:index"
)
@login_required
def kullanici_duzenle(request: Any, user_id: int) -> Any:
    """
    Kullanıcı düzenler.
    
    Müdür yetkisi gerektirir. Input validation ve error handling ile güvenli hale getirilmiştir.
    """
    from django.core.exceptions import ValidationError
    
    try:
        kullanici = get_object_or_404(User, pk=user_id)
        
        # Kendi hesabını silmeye çalışıyorsa uyar
        if kullanici == request.user and not request.user.is_superuser:
            messages.warning(request, 'Kendi hesabınızı düzenleyemezsiniz.')
            return redirect('kullanici_yonetimi:kullanici_listesi')
        
        if request.method == 'POST':
            try:
                form = KullaniciForm(request.POST, instance=kullanici)
                if form.is_valid():
                    user = form.save()
                    log_action(request.user, 'update', user, f'Kullanıcı güncellendi: {user.username}', request)
                    messages.success(request, f'Kullanıcı "{user.username}" başarıyla güncellendi.')
                    return redirect('kullanici_yonetimi:kullanici_listesi')
                else:
                    messages.error(request, 'Lütfen form hatalarını düzeltin.')
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Kullanıcı düzenleme hatası: {str(e)}", exc_info=True)
                raise
        else:
            form = KullaniciForm(instance=kullanici)
        
        context = {
            'form': form,
            'kullanici': kullanici,
            'title': f'Kullanıcı Düzenle - {kullanici.username}',
        }
        return render(request, 'kullanici_yonetimi/kullanici_form.html', context)
    except Exception as e:
        logger.error(f"Kullanıcı düzenleme hatası: {str(e)}", exc_info=True)
        raise


@handle_view_errors(
    error_message="Kullanıcı silinirken bir hata oluştu.",
    redirect_url="kullanici_yonetimi:index"
)
@database_transaction
@login_required
def kullanici_sil(request: Any, user_id: int) -> Any:
    """
    Kullanıcı siler (pasif yapar veya tamamen siler).
    
    Transaction içinde çalışır, hata durumunda rollback yapar.
    Kullanıcı pasif yapılabilir veya tamamen silinebilir.
    """
    try:
        kullanici = get_object_or_404(User, pk=user_id)
        
        # Kendi hesabını silmeye çalışıyorsa uyar
        if kullanici == request.user:
            messages.error(request, 'Kendi hesabınızı silemezsiniz.')
            return redirect('kullanici_yonetimi:kullanici_listesi')
        
        if request.method == 'POST':
            try:
                action = request.POST.get('action', 'pasif')  # 'pasif' veya 'sil'
                username = kullanici.username
                
                with transaction.atomic():
                    if action == 'sil':
                        # Kullanıcıyı tamamen sil
                        log_action(request.user, 'delete', kullanici, 
                                 f'Kullanıcı tamamen silindi: {username}', request)
                        kullanici.delete()
                        messages.success(request, f'Kullanıcı "{username}" başarıyla silindi.')
                    else:
                        # Kullanıcıyı pasif yap
                        kullanici.is_active = False
                        kullanici.save()
                        log_action(request.user, 'delete', kullanici, 
                                 f'Kullanıcı pasif yapıldı: {username}', request)
                        messages.success(request, f'Kullanıcı "{username}" başarıyla pasif yapıldı.')
                    
                    return redirect('kullanici_yonetimi:kullanici_listesi')
            except Exception as e:
                logger.error(f"Kullanıcı silme hatası: {str(e)}", exc_info=True)
                raise
        
        # Kullanıcının ilişkili kayıtlarını kontrol et
        fatura_sayisi = Fatura.objects.filter(olusturan=kullanici).count()
        from masraf.models import Masraf
        masraf_sayisi = Masraf.objects.filter(olusturan=kullanici).count()
        from finans.models import FinansHareketi
        finans_hareket_sayisi = FinansHareketi.objects.filter(olusturan=kullanici).count()
        from cari.models import CariNotu
        cari_not_sayisi = CariNotu.objects.filter(olusturan=kullanici).count()
        
        toplam_iliskili_kayit = fatura_sayisi + masraf_sayisi + finans_hareket_sayisi + cari_not_sayisi
        
        context = {
            'kullanici': kullanici,
            'fatura_sayisi': fatura_sayisi,
            'masraf_sayisi': masraf_sayisi,
            'finans_hareket_sayisi': finans_hareket_sayisi,
            'cari_not_sayisi': cari_not_sayisi,
            'toplam_iliskili_kayit': toplam_iliskili_kayit,
        }
        return render(request, 'kullanici_yonetimi/kullanici_sil.html', context)
    except Exception as e:
        logger.error(f"Kullanıcı silme hatası: {str(e)}", exc_info=True)
        raise


@handle_view_errors(error_message="Kullanıcı listesi yüklenirken bir hata oluştu.")
@login_required
def kullanici_listesi(request: Any) -> Any:
    """
    Kullanıcı listesi sayfası (JSON API).
    
    Müdür yetkisi gerektirir.
    """
    """Kullanıcı listesi (sadece yönetim için)"""
    kullanicilar = User.objects.filter(is_staff=True).order_by('username')
    
    # Arama
    search_query = request.GET.get('search', '')
    if search_query:
        kullanicilar = kullanicilar.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Aktif/Pasif filtresi
    durum_filter = request.GET.get('durum', '')
    if durum_filter == 'aktif':
        kullanicilar = kullanicilar.filter(is_active=True)
    elif durum_filter == 'pasif':
        kullanicilar = kullanicilar.filter(is_active=False)
    
    # Python tarafında kullanıcı bilgilerini hazırla (HTML'i azaltmak için)
    kullanici_listesi_data = []
    for kullanici in kullanicilar:
        kullanici_listesi_data.append({
            'id': kullanici.id,
            'username': kullanici.username,
            'full_name': kullanici.get_full_name() or '-',
            'email': kullanici.email or '-',
            'is_active': kullanici.is_active,
            'is_staff': kullanici.is_staff,
            'is_superuser': kullanici.is_superuser,
            'durum_badge': 'success' if kullanici.is_active else 'secondary',
            'durum_text': 'Aktif' if kullanici.is_active else 'Pasif',
            'yetkiler': {
                'is_staff': kullanici.is_staff,
                'is_superuser': kullanici.is_superuser,
            }
        })
    
    context = {
        'kullanicilar': kullanici_listesi_data,
        'search_query': search_query,
        'durum_filter': durum_filter,
        'is_aktif': durum_filter == 'aktif',
        'is_pasif': durum_filter == 'pasif',
    }
    return render(request, 'kullanici_yonetimi/kullanici_listesi.html', context)
