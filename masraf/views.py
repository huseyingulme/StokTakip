from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta
from .models import MasrafKategori, Masraf
from .forms import MasrafKategoriForm, MasrafForm
from accounts.decorators import muhasebe_required


@login_required
def index(request):
    masraf_list = Masraf.objects.all().order_by('-tarih', '-id')

    search_query = request.GET.get('search', '')
    if search_query:
        masraf_list = masraf_list.filter(
            Q(masraf_no__icontains=search_query) |
            Q(aciklama__icontains=search_query)
        )

    kategori_filter = request.GET.get('kategori', '')
    if kategori_filter:
        masraf_list = masraf_list.filter(kategori_id=kategori_filter)

    durum_filter = request.GET.get('durum', '')
    if durum_filter:
        masraf_list = masraf_list.filter(durum=durum_filter)

    tarih_baslangic = request.GET.get('tarih_baslangic', '')
    tarih_bitis = request.GET.get('tarih_bitis', '')
    if tarih_baslangic:
        masraf_list = masraf_list.filter(tarih__gte=tarih_baslangic)
    if tarih_bitis:
        masraf_list = masraf_list.filter(tarih__lte=tarih_bitis)

    toplam_tutar = masraf_list.aggregate(toplam=Sum('tutar'))['toplam'] or 0

    paginator = Paginator(masraf_list, 20)
    page_number = request.GET.get('page')
    masraflar = paginator.get_page(page_number)

    context = {
        'masraflar': masraflar,
        'kategoriler': MasrafKategori.objects.all(),
        'toplam_tutar': toplam_tutar,
        'search_query': search_query,
        'kategori_filter': kategori_filter,
        'durum_filter': durum_filter,
        'tarih_baslangic': tarih_baslangic,
        'tarih_bitis': tarih_bitis,
    }
    return render(request, 'masraf/index.html', context)


@muhasebe_required
@login_required
def masraf_ekle(request):
    if request.method == 'POST':
        form = MasrafForm(request.POST)
        if form.is_valid():
            masraf = form.save(commit=False)
            if not masraf.olusturan:
                masraf.olusturan = request.user
            masraf.save()
            messages.success(request, 'Masraf başarıyla eklendi.')
            return redirect('masraf:index')
    else:
        form = MasrafForm()

    return render(request, 'masraf/masraf_form.html', {'form': form, 'title': 'Yeni Masraf Ekle'})


@muhasebe_required
@login_required
def masraf_duzenle(request, pk):
    masraf = get_object_or_404(Masraf, pk=pk)

    if request.method == 'POST':
        form = MasrafForm(request.POST, instance=masraf)
        if form.is_valid():
            form.save()
            messages.success(request, 'Masraf başarıyla güncellendi.')
            return redirect('masraf:index')
    else:
        form = MasrafForm(instance=masraf)

    return render(request, 'masraf/masraf_form.html', {'form': form, 'title': 'Masraf Düzenle', 'masraf': masraf})


@muhasebe_required
@login_required
def masraf_sil(request, pk):
    masraf = get_object_or_404(Masraf, pk=pk)

    if request.method == 'POST':
        masraf.delete()
        messages.success(request, 'Masraf başarıyla silindi.')
        return redirect('masraf:index')

    return render(request, 'masraf/masraf_sil.html', {'masraf': masraf})
