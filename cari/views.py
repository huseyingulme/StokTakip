from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from .models import Cari, CariHareketi, CariNotu, TahsilatMakbuzu, TediyeMakbuzu
from .forms import CariForm, CariHareketiForm, CariNotuForm, TahsilatMakbuzuForm, TediyeMakbuzuForm


@login_required
def index(request):
    cari_list = Cari.objects.filter(durum='aktif').order_by('ad_soyad')

    search_query = request.GET.get('search', '')
    if search_query:
        cari_list = cari_list.filter(
            Q(ad_soyad__icontains=search_query) |
            Q(vergi_no__icontains=search_query) |
            Q(tc_vkn__icontains=search_query) |
            Q(telefon__icontains=search_query)
        )

    kategori_filter = request.GET.get('kategori', '')
    if kategori_filter:
        cari_list = cari_list.filter(kategori=kategori_filter)

    bakiye_filter = request.GET.get('bakiye', '')
    if bakiye_filter == 'borc':
        cari_list = [c for c in cari_list if c.bakiye > 0]
    elif bakiye_filter == 'alacak':
        cari_list = [c for c in cari_list if c.bakiye < 0]

    paginator = Paginator(cari_list, 20)
    page_number = request.GET.get('page')
    cariler = paginator.get_page(page_number)

    context = {
        'cariler': cariler,
        'search_query': search_query,
        'kategori_filter': kategori_filter,
        'bakiye_filter': bakiye_filter,
    }
    return render(request, 'cari/index.html', context)


@login_required
def cari_ekle(request):
    if request.method == 'POST':
        form = CariForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cari başarıyla eklendi.')
            return redirect('cari:index')
    else:
        form = CariForm()

    return render(request, 'cari/cari_form.html', {'form': form, 'title': 'Yeni Cari Ekle'})


@login_required
def cari_duzenle(request, pk):
    cari = get_object_or_404(Cari, pk=pk)

    if request.method == 'POST':
        form = CariForm(request.POST, instance=cari)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cari başarıyla güncellendi.')
            return redirect('cari:detay', pk=pk)
    else:
        form = CariForm(instance=cari)

    return render(request, 'cari/cari_form.html', {'form': form, 'title': 'Cari Düzenle', 'cari': cari})


@login_required
def cari_sil(request, pk):
    cari = get_object_or_404(Cari, pk=pk)

    if cari.hareketler.exists():
        if request.method == 'POST':
            cari.durum = 'pasif'
            cari.save()
            messages.success(request, 'Cari pasif duruma getirildi.')
            return redirect('cari:index')
        return render(request, 'cari/cari_sil.html', {'cari': cari})
    else:
        if request.method == 'POST':
            cari.delete()
            messages.success(request, 'Cari başarıyla silindi.')
            return redirect('cari:index')
        return render(request, 'cari/cari_sil.html', {'cari': cari})


@login_required
def cari_detay(request, pk):
    cari = get_object_or_404(Cari, pk=pk)
    hareketler = cari.hareketler.all()[:50]
    notlar = cari.notlar.all()[:10]

    context = {
        'cari': cari,
        'hareketler': hareketler,
        'notlar': notlar,
    }
    return render(request, 'cari/cari_detay.html', context)


@login_required
def hareket_ekle(request, cari_pk=None):
    if cari_pk:
        cari = get_object_or_404(Cari, pk=cari_pk)
    else:
        cari = None

    if request.method == 'POST':
        form = CariHareketiForm(request.POST)
        if form.is_valid():
            hareket = form.save(commit=False)
            if not hareket.olusturan:
                hareket.olusturan = request.user
            hareket.save()

            if cari and cari.risk_limiti > 0 and cari.bakiye > cari.risk_limiti:
                messages.warning(request, f'UYARI: Cari risk limitini aştı! Mevcut bakiye: {cari.bakiye:,.2f} ₺')

            messages.success(request, 'Hareket başarıyla eklendi.')
            if cari:
                return redirect('cari:detay', pk=cari_pk)
            return redirect('cari:hareket_listesi')
    else:
        form = CariHareketiForm(initial={'cari': cari, 'tarih': timezone.now()})

    return render(request, 'cari/hareket_form.html', {'form': form, 'title': 'Yeni Hareket Ekle', 'cari': cari})


@login_required
def hareket_duzenle(request, pk):
    hareket = get_object_or_404(CariHareketi, pk=pk)

    if request.method == 'POST':
        form = CariHareketiForm(request.POST, instance=hareket)
        if form.is_valid():
            form.save()
            messages.success(request, 'Hareket başarıyla güncellendi.')
            return redirect('cari:detay', pk=hareket.cari.pk)
    else:
        form = CariHareketiForm(instance=hareket)

    return render(request, 'cari/hareket_form.html', {'form': form, 'title': 'Hareket Düzenle', 'hareket': hareket})


@login_required
def hareket_sil(request, pk):
    hareket = get_object_or_404(CariHareketi, pk=pk)
    cari_pk = hareket.cari.pk

    if request.method == 'POST':
        hareket.delete()
        messages.success(request, 'Hareket başarıyla silindi.')
        return redirect('cari:detay', pk=cari_pk)

    return render(request, 'cari/hareket_sil.html', {'hareket': hareket})


@login_required
def hareket_listesi(request):
    hareket_list = CariHareketi.objects.all().order_by('-tarih', '-id')

    cari_filter = request.GET.get('cari', '')
    if cari_filter:
        hareket_list = hareket_list.filter(cari_id=cari_filter)

    hareket_turu_filter = request.GET.get('hareket_turu', '')
    if hareket_turu_filter:
        hareket_list = hareket_list.filter(hareket_turu=hareket_turu_filter)

    tarih_baslangic = request.GET.get('tarih_baslangic', '')
    tarih_bitis = request.GET.get('tarih_bitis', '')
    if tarih_baslangic:
        hareket_list = hareket_list.filter(tarih__gte=tarih_baslangic)
    if tarih_bitis:
        hareket_list = hareket_list.filter(tarih__lte=tarih_bitis)

    paginator = Paginator(hareket_list, 50)
    page_number = request.GET.get('page')
    hareketler = paginator.get_page(page_number)

    context = {
        'hareketler': hareketler,
        'cariler': Cari.objects.filter(durum='aktif').order_by('ad_soyad'),
    }
    return render(request, 'cari/hareket_listesi.html', context)


@login_required
def cari_ekstre(request, pk):
    cari = get_object_or_404(Cari, pk=pk)

    tarih_baslangic = request.GET.get('tarih_baslangic', '')
    tarih_bitis = request.GET.get('tarih_bitis', '')

    if not tarih_baslangic:
        tarih_baslangic = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not tarih_bitis:
        tarih_bitis = timezone.now().strftime('%Y-%m-%d')

    hareketler = cari.hareketler.filter(
        tarih__gte=tarih_baslangic,
        tarih__lte=tarih_bitis
    ).order_by('tarih', 'id')

    acilis_bakiye = Decimal('0.00')
    onceki_hareketler = cari.hareketler.filter(tarih__lt=tarih_baslangic)
    if onceki_hareketler.exists():
        onceki_borc = onceki_hareketler.filter(
            hareket_turu__in=['satis_faturasi', 'odeme']
        ).aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0.00')
        onceki_alacak = onceki_hareketler.filter(
            hareket_turu__in=['alis_faturasi', 'tahsilat']
        ).aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0.00')
        acilis_bakiye = onceki_borc - onceki_alacak

    bakiye = acilis_bakiye
    ekstre_satirlari = []

    for hareket in hareketler:
        if hareket.hareket_turu in ['satis_faturasi', 'odeme']:
            bakiye += hareket.tutar
            borc = hareket.tutar
            alacak = Decimal('0.00')
        else:
            bakiye -= hareket.tutar
            borc = Decimal('0.00')
            alacak = hareket.tutar

        ekstre_satirlari.append({
            'tarih': hareket.tarih,
            'aciklama': hareket.aciklama or hareket.get_hareket_turu_display(),
            'belge': hareket.belge_no or '',
            'borc': borc,
            'alacak': alacak,
            'bakiye': bakiye,
        })

    kapanis_bakiye = bakiye

    context = {
        'cari': cari,
        'tarih_baslangic': tarih_baslangic,
        'tarih_bitis': tarih_bitis,
        'acilis_bakiye': acilis_bakiye,
        'kapanis_bakiye': kapanis_bakiye,
        'ekstre_satirlari': ekstre_satirlari,
    }
    return render(request, 'cari/cari_ekstre.html', context)


@login_required
def not_ekle(request, cari_pk):
    cari = get_object_or_404(Cari, pk=cari_pk)

    if request.method == 'POST':
        form = CariNotuForm(request.POST)
        if form.is_valid():
            notu = form.save(commit=False)
            notu.cari = cari
            notu.olusturan = request.user
            notu.save()
            messages.success(request, 'Not başarıyla eklendi.')
            return redirect('cari:detay', pk=cari_pk)
    else:
        form = CariNotuForm()

    return render(request, 'cari/not_form.html', {'form': form, 'title': 'Yeni Not Ekle', 'cari': cari})


@login_required
def not_duzenle(request, pk):
    notu = get_object_or_404(CariNotu, pk=pk)

    if request.method == 'POST':
        form = CariNotuForm(request.POST, instance=notu)
        if form.is_valid():
            form.save()
            messages.success(request, 'Not başarıyla güncellendi.')
            return redirect('cari:detay', pk=notu.cari.pk)
    else:
        form = CariNotuForm(instance=notu)

    return render(request, 'cari/not_form.html', {'form': form, 'title': 'Not Düzenle', 'notu': notu})


@login_required
def not_sil(request, pk):
    notu = get_object_or_404(CariNotu, pk=pk)
    cari_pk = notu.cari.pk

    if request.method == 'POST':
        notu.delete()
        messages.success(request, 'Not başarıyla silindi.')
        return redirect('cari:detay', pk=cari_pk)

    return render(request, 'cari/not_sil.html', {'notu': notu})


@login_required
def tahsilat_makbuzu_ekle(request, cari_pk=None):
    if cari_pk:
        cari = get_object_or_404(Cari, pk=cari_pk)
    else:
        cari = None

    if request.method == 'POST':
        form = TahsilatMakbuzuForm(request.POST)
        if form.is_valid():
            makbuz = form.save(commit=False)
            if not makbuz.olusturan:
                makbuz.olusturan = request.user
            makbuz.save()
            messages.success(request, 'Tahsilat makbuzu başarıyla oluşturuldu.')
            if cari:
                return redirect('cari:detay', pk=cari_pk)
            return redirect('cari:tahsilat_listesi')
    else:
        form = TahsilatMakbuzuForm(initial={'cari': cari})

    return render(request, 'cari/tahsilat_makbuzu_form.html', {'form': form, 'title': 'Yeni Tahsilat Makbuzu', 'cari': cari})


@login_required
def tahsilat_makbuzu_listesi(request):
    makbuz_list = TahsilatMakbuzu.objects.all().order_by('-tarih', '-id')

    cari_filter = request.GET.get('cari', '')
    if cari_filter:
        makbuz_list = makbuz_list.filter(cari_id=cari_filter)

    tarih_baslangic = request.GET.get('tarih_baslangic', '')
    tarih_bitis = request.GET.get('tarih_bitis', '')
    if tarih_baslangic:
        makbuz_list = makbuz_list.filter(tarih__gte=tarih_baslangic)
    if tarih_bitis:
        makbuz_list = makbuz_list.filter(tarih__lte=tarih_bitis)

    paginator = Paginator(makbuz_list, 50)
    page_number = request.GET.get('page')
    makbuzlar = paginator.get_page(page_number)

    context = {
        'makbuzlar': makbuzlar,
        'cariler': Cari.objects.filter(durum='aktif').order_by('ad_soyad'),
    }
    return render(request, 'cari/tahsilat_makbuzu_listesi.html', context)


@login_required
def tediye_makbuzu_ekle(request, cari_pk=None):
    if cari_pk:
        cari = get_object_or_404(Cari, pk=cari_pk)
    else:
        cari = None

    if request.method == 'POST':
        form = TediyeMakbuzuForm(request.POST)
        if form.is_valid():
            makbuz = form.save(commit=False)
            if not makbuz.olusturan:
                makbuz.olusturan = request.user
            makbuz.save()
            messages.success(request, 'Tediye makbuzu başarıyla oluşturuldu.')
            if cari:
                return redirect('cari:detay', pk=cari_pk)
            return redirect('cari:tediye_listesi')
    else:
        form = TediyeMakbuzuForm(initial={'cari': cari})

    return render(request, 'cari/tediye_makbuzu_form.html', {'form': form, 'title': 'Yeni Tediye Makbuzu', 'cari': cari})


@login_required
def tediye_makbuzu_listesi(request):
    makbuz_list = TediyeMakbuzu.objects.all().order_by('-tarih', '-id')

    cari_filter = request.GET.get('cari', '')
    if cari_filter:
        makbuz_list = makbuz_list.filter(cari_id=cari_filter)

    tarih_baslangic = request.GET.get('tarih_baslangic', '')
    tarih_bitis = request.GET.get('tarih_bitis', '')
    if tarih_baslangic:
        makbuz_list = makbuz_list.filter(tarih__gte=tarih_baslangic)
    if tarih_bitis:
        makbuz_list = makbuz_list.filter(tarih__lte=tarih_bitis)

    paginator = Paginator(makbuz_list, 50)
    page_number = request.GET.get('page')
    makbuzlar = paginator.get_page(page_number)

    context = {
        'makbuzlar': makbuzlar,
        'cariler': Cari.objects.filter(durum='aktif').order_by('ad_soyad'),
    }
    return render(request, 'cari/tediye_makbuzu_listesi.html', context)
