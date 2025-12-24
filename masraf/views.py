from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from typing import Any
import logging
from .models import Masraf
from .forms import MasrafForm
from accounts.utils import log_action
from stoktakip.error_handling import handle_view_errors, database_transaction
from stoktakip.security_utils import (
    sanitize_string, sanitize_decimal, validate_date_range, validate_search_query
)
from stoktakip.cache_utils import cache_view_result

logger = logging.getLogger(__name__)


@cache_view_result(timeout=300, key_prefix='masraf_index')
@handle_view_errors(error_message="Masraf listesi yüklenirken bir hata oluştu.")
@login_required
def index(request: Any) -> Any:
    """
    Masraf listesi sayfası.
    
    Muhasebe yetkisi gerektirir. Filtreleme, arama ve sayfalama desteği ile
    masraf listesini gösterir. Input validation ve error handling ile güvenli hale getirilmiştir.
    """
    try:
        masraf_list = Masraf.objects.select_related('olusturan').order_by('-tarih', '-id')

        # Arama - Input validation ile
        search_query = request.GET.get('search', '')
        if search_query:
            try:
                search_query = validate_search_query(search_query, max_length=100)
                masraf_list = masraf_list.filter(
                    Q(masraf_no__icontains=search_query) |
                    Q(aciklama__icontains=search_query)
                )
            except Exception as e:
                logger.warning(f"Geçersiz arama sorgusu: {str(e)}")
                messages.warning(request, "Geçersiz arama sorgusu.")
                search_query = ''


        # Durum filtresi - Input validation
        durum_filter = request.GET.get('durum', '')
        if durum_filter:
            if durum_filter in ['onaylandi', 'beklemede', 'reddedildi']:
                masraf_list = masraf_list.filter(durum=durum_filter)
            else:
                durum_filter = ''

        # Tarih aralığı filtresi - Input validation
        tarih_baslangic = request.GET.get('tarih_baslangic', '')
        tarih_bitis = request.GET.get('tarih_bitis', '')
        if tarih_baslangic and tarih_bitis:
            try:
                tarih_baslangic, tarih_bitis = validate_date_range(tarih_baslangic, tarih_bitis)
                masraf_list = masraf_list.filter(
                    tarih__gte=tarih_baslangic,
                    tarih__lte=tarih_bitis
                )
            except Exception as e:
                logger.warning(f"Geçersiz tarih aralığı: {str(e)}")
                messages.warning(request, "Geçersiz tarih aralığı.")
                tarih_baslangic = ''
                tarih_bitis = ''
        elif tarih_baslangic:
            masraf_list = masraf_list.filter(tarih__gte=tarih_baslangic)
        elif tarih_bitis:
            masraf_list = masraf_list.filter(tarih__lte=tarih_bitis)

        # Toplam tutar hesapla
        toplam_tutar = masraf_list.aggregate(toplam=Sum('tutar'))['toplam'] or 0

        # Sayfalama - Input validation
        try:
            page_number = request.GET.get('page', '1')
            page_number = int(page_number)
            if page_number < 1:
                page_number = 1
        except (ValueError, TypeError):
            page_number = 1

        paginator = Paginator(masraf_list, 20)
        masraflar = paginator.get_page(page_number)

        context = {
            'masraflar': masraflar,
            'toplam_tutar': toplam_tutar,
            'search_query': search_query,
            'kategori_filter': '',
            'durum_filter': durum_filter,
            'tarih_baslangic': tarih_baslangic,
            'tarih_bitis': tarih_bitis,
        }
        return render(request, 'masraf/index.html', context)
    except Exception as e:
        logger.error(f"Masraf index hatası: {str(e)}", exc_info=True)
        raise  # handle_view_errors decorator'ı yakalayacak


@handle_view_errors(
    error_message="Masraf eklenirken bir hata oluştu. Lütfen tekrar deneyin.",
    redirect_url="masraf:index"
)
@database_transaction
@login_required
def masraf_ekle(request: Any) -> Any:
    """
    Yeni masraf ekler.
    
    Transaction içinde çalışır, hata durumunda rollback yapar.
    Input validation ve error handling ile güvenli hale getirilmiştir.
    """
    from django.core.exceptions import ValidationError
    
    if request.method == 'POST':
        try:
            form = MasrafForm(request.POST)
            if form.is_valid():
                # Transaction içinde masraf oluştur
                with transaction.atomic():
                    masraf = form.save(commit=False)
                    if not masraf.olusturan:
                        masraf.olusturan = request.user
                    
                    # Tutar validation
                    if masraf.tutar and masraf.tutar < 0:
                        raise ValidationError("Tutar negatif olamaz.")
                    
                    masraf.save()
                    
                    log_action(request.user, 'create', masraf, 
                             f'Masraf eklendi: {masraf.masraf_no or masraf.aciklama[:50]}', request)
                    messages.success(request, 'Masraf başarıyla eklendi.')
                    return redirect('masraf:index')
            else:
                messages.error(request, 'Lütfen form hatalarını düzeltin.')
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            logger.error(f"Masraf ekleme hatası: {str(e)}", exc_info=True)
            raise  # handle_view_errors decorator'ı yakalayacak
    else:
        form = MasrafForm()

    return render(request, 'masraf/masraf_form.html', {'form': form, 'title': 'Yeni Masraf Ekle'})


@handle_view_errors(
    error_message="Masraf güncellenirken bir hata oluştu.",
    redirect_url="masraf:index"
)
@login_required
def masraf_duzenle(request: Any, pk: int) -> Any:
    """
    Masraf düzenler.
    
    Input validation ve error handling ile güvenli hale getirilmiştir.
    """
    from django.core.exceptions import ValidationError
    
    try:
        masraf = get_object_or_404(Masraf, pk=pk)

        if request.method == 'POST':
            try:
                form = MasrafForm(request.POST, instance=masraf)
                if form.is_valid():
                    # Tutar validation
                    if form.cleaned_data.get('tutar', 0) < 0:
                        raise ValidationError("Tutar negatif olamaz.")
                    
                    form.save()
                    
                    log_action(request.user, 'update', masraf, 
                             f'Masraf güncellendi: {masraf.masraf_no or masraf.aciklama[:50]}', request)
                    messages.success(request, 'Masraf başarıyla güncellendi.')
                    return redirect('masraf:index')
                else:
                    messages.error(request, 'Lütfen form hatalarını düzeltin.')
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Masraf düzenleme hatası: {str(e)}", exc_info=True)
                raise
        else:
            form = MasrafForm(instance=masraf)

        return render(request, 'masraf/masraf_form.html', {'form': form, 'title': 'Masraf Düzenle', 'masraf': masraf})
    except Exception as e:
        logger.error(f"Masraf düzenleme hatası: {str(e)}", exc_info=True)
        raise


@handle_view_errors(
    error_message="Masraf silinirken bir hata oluştu.",
    redirect_url="masraf:index"
)
@database_transaction
@login_required
def masraf_sil(request: Any, pk: int) -> Any:
    """
    Masraf siler.
    
    Transaction içinde çalışır, hata durumunda rollback yapar.
    """
    try:
        masraf = get_object_or_404(Masraf, pk=pk)

        if request.method == 'POST':
            try:
                with transaction.atomic():
                    masraf_no = masraf.masraf_no or masraf.aciklama[:50]
                    masraf.delete()
                    
                    log_action(request.user, 'delete', None, 
                             f'Masraf silindi: {masraf_no}', request)
                    messages.success(request, 'Masraf başarıyla silindi.')
                    return redirect('masraf:index')
            except Exception as e:
                logger.error(f"Masraf silme hatası: {str(e)}", exc_info=True)
                raise
        else:
            return render(request, 'masraf/masraf_sil.html', {'masraf': masraf})
    except Exception as e:
        logger.error(f"Masraf silme hatası: {str(e)}", exc_info=True)
        raise
