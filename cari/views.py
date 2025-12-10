from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Case, When, F
from django.db import models
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from .models import Cari, CariHareketi, CariNotu, TahsilatMakbuzu, TediyeMakbuzu
from .forms import CariForm, CariHareketiForm, CariNotuForm, TahsilatMakbuzuForm, TediyeMakbuzuForm
from accounts.decorators import muhasebe_required, satis_required


@login_required
def index(request):
    cari_list = Cari.objects.filter(durum='aktif').select_related().order_by('ad_soyad')

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

    paginator = Paginator(cari_list, 20)
    page_number = request.GET.get('page')
    cariler = paginator.get_page(page_number)
    
    # Her cari için bakiye mutlak değerini hesapla
    for cari in cariler:
        cari.bakiye_abs = abs(cari.bakiye)

    context = {
        'cariler': cariler,
        'search_query': search_query,
        'kategori_filter': kategori_filter,
    }
    return render(request, 'cari/index.html', context)


@satis_required
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


@satis_required
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


@muhasebe_required
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
    hareketler = cari.hareketler.select_related('olusturan').all()[:50]
    notlar = cari.notlar.select_related('olusturan').all()[:10]

    context = {
        'cari': cari,
        'hareketler': hareketler,
        'notlar': notlar,
    }
    return render(request, 'cari/cari_detay.html', context)


@muhasebe_required
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


@muhasebe_required
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


@muhasebe_required
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
    hareket_list = CariHareketi.objects.select_related('cari', 'olusturan').all().order_by('-tarih', '-id')

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

    from fatura.models import Fatura
    
    fatura_nolari = {}
    for hareket in hareketler:
        if hareket.belge_no and (hareket.hareket_turu == 'satis_faturasi' or hareket.hareket_turu == 'alis_faturasi'):
            try:
                fatura = Fatura.objects.get(fatura_no=hareket.belge_no)
                fatura_nolari[hareket.belge_no] = fatura.pk
            except Fatura.DoesNotExist:
                pass

    context = {
        'hareketler': hareketler,
        'cariler': Cari.objects.filter(durum='aktif').order_by('ad_soyad'),
        'cari_filter': cari_filter,
        'hareket_turu_filter': hareket_turu_filter,
        'tarih_baslangic': tarih_baslangic,
        'tarih_bitis': tarih_bitis,
        'fatura_nolari': fatura_nolari,
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
def cari_ekstre_pdf(request, pk):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    from django.http import HttpResponse
    from accounts.utils import log_action
    from io import BytesIO
    
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
    
    # Buffer kullan
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=30, leftMargin=30,
                           topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    # Başlık stili
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=25,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    elements.append(Paragraph('CARİ EKSTRE RAPORU', title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Bilgi tablosu
    info_data = [
        ['<b>Cari:</b>', cari.ad_soyad],
        ['<b>Tarih Aralığı:</b>', f'{tarih_baslangic} - {tarih_bitis}'],
        ['<b>Açılış Bakiyesi:</b>', f'{acilis_bakiye:,.2f} ₺'],
        ['<b>Kapanış Bakiyesi:</b>', f'<b>{kapanis_bakiye:,.2f} ₺</b>'],
    ]
    
    info_table = Table(info_data, colWidths=[2.2*inch, 3.3*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Ekstre tablosu
    headers = ['Tarih', 'Açıklama', 'Belge No', 'Borç', 'Alacak', 'Bakiye']
    table_data = [headers]
    
    for satir in ekstre_satirlari:
        table_data.append([
            satir['tarih'].strftime('%d.%m.%Y'),
            satir['aciklama'][:50] if len(satir['aciklama']) > 50 else satir['aciklama'],  # Uzun açıklamaları kısalt
            satir['belge'][:20] if len(satir['belge']) > 20 else satir['belge'],
            f'{satir["borc"]:,.2f} ₺' if satir["borc"] > 0 else '-',
            f'{satir["alacak"]:,.2f} ₺' if satir["alacak"] > 0 else '-',
            f'{satir["bakiye"]:,.2f} ₺'
        ])
    
    ekstre_table = Table(table_data, colWidths=[1.0*inch, 2.3*inch, 1.0*inch, 1.0*inch, 1.0*inch, 1.0*inch])
    ekstre_table.setStyle(TableStyle([
        # Başlık satırı
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), TA_CENTER),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        
        # Veri satırları
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (0, -1), TA_CENTER),  # Tarih
        ('ALIGN', (1, 1), (1, -1), TA_LEFT),    # Açıklama
        ('ALIGN', (2, 1), (2, -1), TA_CENTER), # Belge No
        ('ALIGN', (3, 1), (3, -1), TA_RIGHT),   # Borç
        ('ALIGN', (4, 1), (4, -1), TA_RIGHT),   # Alacak
        ('ALIGN', (5, 1), (5, -1), TA_RIGHT),   # Bakiye
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(ekstre_table)
    
    # PDF oluştur
    doc.build(elements)
    
    # Response hazırla
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(content_type='application/pdf; charset=utf-8')
    filename = f"Cari_Ekstre_{cari.ad_soyad}_{tarih_baslangic}_{tarih_bitis}.pdf"
    # Dosya adındaki özel karakterleri temizle
    filename = filename.replace(' ', '_').replace('/', '_')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write(pdf)
    
    log_action(request.user, 'export', cari, f'Cari ekstre PDF export: {cari.ad_soyad}')
    return response


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

    return render(request, 'cari/not_form.html', {'form': form, 'title': 'Not Düzenle', 'notu': notu, 'cari': notu.cari})


@login_required
def not_sil(request, pk):
    notu = get_object_or_404(CariNotu, pk=pk)
    cari_pk = notu.cari.pk

    if request.method == 'POST':
        notu.delete()
        messages.success(request, 'Not başarıyla silindi.')
        return redirect('cari:detay', pk=cari_pk)

    return render(request, 'cari/not_sil.html', {'notu': notu})


@muhasebe_required
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
        'cari_filter': cari_filter,
        'tarih_baslangic': tarih_baslangic,
        'tarih_bitis': tarih_bitis,
    }
    return render(request, 'cari/tahsilat_makbuzu_listesi.html', context)


@muhasebe_required
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
        'cari_filter': cari_filter,
        'tarih_baslangic': tarih_baslangic,
        'tarih_bitis': tarih_bitis,
    }
    return render(request, 'cari/tediye_makbuzu_listesi.html', context)


@login_required
def cari_yaslandirma(request, pk):
    cari = get_object_or_404(Cari, pk=pk)
    
    bugun = timezone.now().date()
    yaslandirma = {
        '0-30': {'borc': Decimal('0.00'), 'alacak': Decimal('0.00')},
        '31-60': {'borc': Decimal('0.00'), 'alacak': Decimal('0.00')},
        '61-90': {'borc': Decimal('0.00'), 'alacak': Decimal('0.00')},
        '90+': {'borc': Decimal('0.00'), 'alacak': Decimal('0.00')},
    }
    
    hareketler = cari.hareketler.all().order_by('tarih')
    bakiye = Decimal('0.00')
    
    for hareket in hareketler:
        gun_farki = (bugun - hareket.tarih.date()).days
        
        if hareket.hareket_turu in ['satis_faturasi', 'odeme']:
            bakiye += hareket.tutar
            if gun_farki <= 30:
                yaslandirma['0-30']['borc'] += hareket.tutar
            elif gun_farki <= 60:
                yaslandirma['31-60']['borc'] += hareket.tutar
            elif gun_farki <= 90:
                yaslandirma['61-90']['borc'] += hareket.tutar
            else:
                yaslandirma['90+']['borc'] += hareket.tutar
        else:
            bakiye -= hareket.tutar
            if gun_farki <= 30:
                yaslandirma['0-30']['alacak'] += hareket.tutar
            elif gun_farki <= 60:
                yaslandirma['31-60']['alacak'] += hareket.tutar
            elif gun_farki <= 90:
                yaslandirma['61-90']['alacak'] += hareket.tutar
            else:
                yaslandirma['90+']['alacak'] += hareket.tutar
    
    toplam_borc = sum(d['borc'] for d in yaslandirma.values())
    toplam_alacak = sum(d['alacak'] for d in yaslandirma.values())
    
    context = {
        'cari': cari,
        'yaslandirma': yaslandirma,
        'toplam_borc': toplam_borc,
        'toplam_alacak': toplam_alacak,
        'net_bakiye': bakiye,
    }
    return render(request, 'cari/cari_yaslandirma.html', context)
