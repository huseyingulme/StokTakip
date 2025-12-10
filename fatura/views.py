from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from datetime import datetime
from .models import Fatura, FaturaKalem
from .forms import FaturaForm, FaturaKalemForm
from accounts.utils import log_action
from accounts.decorators import satis_required, muhasebe_required, admin_required
from stok.models import Urun


@login_required
def index(request):
    """Fatura listesi sayfası"""
    fatura_list = Fatura.objects.all().select_related('cari').order_by('-fatura_tarihi', '-olusturma_tarihi')
    
    # Arama
    search_query = request.GET.get('search', '')
    if search_query:
        fatura_list = fatura_list.filter(
            Q(fatura_no__icontains=search_query) |
            Q(cari__ad_soyad__icontains=search_query)
        )
    
    # Durum filtresi
    durum_filter = request.GET.get('durum', '')
    if durum_filter:
        fatura_list = fatura_list.filter(durum=durum_filter)
    
    # Tip filtresi
    tip_filter = request.GET.get('tip', '')
    if tip_filter:
        fatura_list = fatura_list.filter(fatura_tipi=tip_filter)
    
    # Tarih aralığı filtresi
    tarih_baslangic = request.GET.get('tarih_baslangic', '')
    tarih_bitis = request.GET.get('tarih_bitis', '')
    if tarih_baslangic:
        fatura_list = fatura_list.filter(fatura_tarihi__gte=tarih_baslangic)
    if tarih_bitis:
        fatura_list = fatura_list.filter(fatura_tarihi__lte=tarih_bitis)
    
    # Tutar aralığı filtresi
    tutar_min = request.GET.get('tutar_min', '')
    tutar_max = request.GET.get('tutar_max', '')
    if tutar_min:
        try:
            fatura_list = fatura_list.filter(genel_toplam__gte=float(tutar_min))
        except ValueError:
            pass
    if tutar_max:
        try:
            fatura_list = fatura_list.filter(genel_toplam__lte=float(tutar_max))
        except ValueError:
            pass
    
    # Sayfalama
    paginator = Paginator(fatura_list, 20)
    page_number = request.GET.get('page')
    faturalar = paginator.get_page(page_number)
    
    context = {
        'faturalar': faturalar,
        'search_query': search_query,
        'durum_filter': durum_filter,
        'tip_filter': tip_filter,
        'tarih_baslangic': tarih_baslangic,
        'tarih_bitis': tarih_bitis,
        'tutar_min': tutar_min,
        'tutar_max': tutar_max,
    }
    return render(request, 'fatura/index.html', context)


@satis_required
@login_required
def fatura_ekle(request):
    from decimal import Decimal
    from django.utils import timezone
    from datetime import timedelta
    
    tip = request.GET.get('tip', 'Satis')
    
    if request.method == 'POST':
        post_data = request.POST.copy()
        if 'fatura_tipi' not in post_data:
            post_data['fatura_tipi'] = tip
        fatura_form = FaturaForm(post_data)
        
        if fatura_form.is_valid():
            fatura = fatura_form.save(commit=False)
            fatura.olusturan = request.user
            if not fatura.fatura_no:
                fatura.fatura_no = fatura.olustur_fatura_no()
            fatura.save(olusturan_user=request.user)
            
            urun_ids = request.POST.getlist('urun_id[]')
            miktarlar = request.POST.getlist('miktar[]')
            birim_fiyatlar = request.POST.getlist('birim_fiyat[]')
            kdv_oranlari = request.POST.getlist('kdv_orani[]')
            kdv_dahil_fiyatlar = request.POST.getlist('kdv_dahil_fiyat[]')
            
            kalem_sayisi = 0
            for i in range(len(urun_ids)):
                if urun_ids[i] and miktarlar[i]:
                    try:
                        urun = Urun.objects.get(pk=urun_ids[i])
                        miktar = int(miktarlar[i])
                        kdv_orani = int(kdv_oranlari[i]) if kdv_oranlari[i] else 20
                        
                        if kdv_dahil_fiyatlar[i] and float(kdv_dahil_fiyatlar[i]) > 0:
                            kdv_dahil = Decimal(str(kdv_dahil_fiyatlar[i]))
                            birim_fiyat = kdv_dahil / (Decimal('1') + Decimal(str(kdv_orani)) / Decimal('100'))
                        else:
                            birim_fiyat = Decimal(str(birim_fiyatlar[i])) if birim_fiyatlar[i] else urun.fiyat
                        
                        FaturaKalem.objects.create(
                            fatura=fatura,
                            urun=urun,
                            urun_adi=urun.ad,
                            miktar=miktar,
                            birim_fiyat=birim_fiyat,
                            kdv_orani=kdv_orani,
                            sira_no=kalem_sayisi + 1
                        )
                        kalem_sayisi += 1
                    except (Urun.DoesNotExist, ValueError, TypeError) as e:
                        continue
            
            if kalem_sayisi == 0:
                messages.error(request, 'En az bir ürün eklemelisiniz!')
                fatura.delete()
                urunler = Urun.objects.all().order_by('ad')
                title = 'Yeni Alış Faturası' if tip == 'Alis' else 'Yeni Satış Faturası'
                return render(request, 'fatura/fatura_form.html', {
                    'form': fatura_form,
                    'title': title,
                    'tip': tip,
                    'urunler': urunler
                })
            
            fatura.hesapla_toplamlar()
            log_action(request.user, 'create', fatura, f'Fatura oluşturuldu: {fatura.fatura_no}')
            messages.success(request, f'Fatura {fatura.fatura_no} başarıyla oluşturuldu.')
            return redirect('fatura:detay', pk=fatura.pk)
    else:
        bugun = timezone.now().date()
        fatura_form = FaturaForm(initial={
            'fatura_tipi': tip,
            'fatura_tarihi': bugun,
            'vade_tarihi': bugun + timedelta(days=30),
            'durum': 'Beklemede',
            'iskonto_orani': 0
        })
    
    urunler = Urun.objects.all().order_by('ad')
    title = 'Yeni Alış Faturası' if tip == 'Alis' else 'Yeni Satış Faturası'
    
    if request.method == 'POST' and not fatura_form.is_valid():
        messages.error(request, 'Lütfen form hatalarını düzeltin.')
    
    return render(request, 'fatura/fatura_form.html', {
        'form': fatura_form,
        'title': title,
        'tip': tip,
        'urunler': urunler
    })


@login_required
def fatura_detay(request, pk):
    """Fatura detay sayfası"""
    fatura = get_object_or_404(Fatura, pk=pk)
    kalemler = fatura.kalemler.all().order_by('sira_no')
    
    context = {
        'fatura': fatura,
        'kalemler': kalemler,
    }
    return render(request, 'fatura/fatura_detay.html', context)


@satis_required
@login_required
def fatura_duzenle(request, pk):
    """Fatura düzenleme"""
    fatura = get_object_or_404(Fatura, pk=pk)
    
    if request.method == 'POST':
        form = FaturaForm(request.POST, instance=fatura)
        if form.is_valid():
            fatura = form.save(commit=False)
            fatura.save(olusturan_user=request.user)
            log_action(request.user, 'update', fatura, f'Fatura güncellendi: {fatura.fatura_no}')
            messages.success(request, 'Fatura başarıyla güncellendi.')
            return redirect('fatura:detay', pk=fatura.pk)
    else:
        form = FaturaForm(instance=fatura)
    
    return render(request, 'fatura/fatura_form.html', {'form': form, 'title': 'Fatura Düzenle', 'fatura': fatura})


@muhasebe_required
@login_required
def fatura_sil(request, pk):
    from cari.models import CariHareketi
    from stok.models import StokHareketi
    
    fatura = get_object_or_404(Fatura, pk=pk)
    
    if request.method == 'POST':
        fatura_no = fatura.fatura_no
        
        CariHareketi.objects.filter(belge_no=fatura_no).delete()
        
        for kalem in fatura.kalemler.all():
            if kalem.urun:
                StokHareketi.objects.filter(
                    urun=kalem.urun,
                    aciklama__contains=f"Fatura: {fatura_no}"
                ).delete()
        
        fatura.delete()
        log_action(request.user, 'delete', None, f'Fatura silindi: {fatura_no}')
        messages.success(request, f'Fatura {fatura_no} ve ilişkili kayıtlar başarıyla silindi.')
        return redirect('fatura:index')
    
    return render(request, 'fatura/fatura_sil.html', {'fatura': fatura})


@satis_required
@login_required
def kalem_ekle(request, fatura_pk):
    fatura = get_object_or_404(Fatura, pk=fatura_pk)
    
    if request.method == 'POST':
        form = FaturaKalemForm(request.POST)
        if form.is_valid():
            kalem = form.save(commit=False)
            kalem.fatura = fatura
            if kalem.urun:
                kalem.urun_adi = kalem.urun.ad
                if not kalem.birim_fiyat or kalem.birim_fiyat == 0:
                    kalem.birim_fiyat = kalem.urun.fiyat
            kalem.save()
            log_action(request.user, 'create', kalem, f'Fatura kalemi eklendi: {kalem.urun_adi}')
            messages.success(request, 'Fatura kalemi başarıyla eklendi.')
            return redirect('fatura:detay', pk=fatura_pk)
    else:
        form = FaturaKalemForm()
    
    return render(request, 'fatura/kalem_form.html', {'form': form, 'fatura': fatura, 'title': 'Yeni Kalem Ekle'})


@login_required
def urun_bilgi_api(request, urun_id):
    from django.http import JsonResponse
    try:
        urun = Urun.objects.get(pk=urun_id)
        return JsonResponse({
            'success': True,
            'urun_adi': urun.ad,
            'birim_fiyat': str(urun.fiyat),
            'birim': urun.birim,
            'mevcut_stok': urun.mevcut_stok
        })
    except Urun.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Ürün bulunamadı'})


@satis_required
@login_required
def kalem_duzenle(request, pk):
    kalem = get_object_or_404(FaturaKalem, pk=pk)
    fatura = kalem.fatura
    
    if request.method == 'POST':
        form = FaturaKalemForm(request.POST, instance=kalem)
        if form.is_valid():
            kalem = form.save(commit=False)
            if kalem.urun:
                kalem.urun_adi = kalem.urun.ad
                if not kalem.birim_fiyat or kalem.birim_fiyat == 0:
                    kalem.birim_fiyat = kalem.urun.fiyat
            kalem.save()
            log_action(request.user, 'update', kalem, f'Fatura kalemi güncellendi: {kalem.urun_adi}')
            messages.success(request, 'Fatura kalemi başarıyla güncellendi.')
            return redirect('fatura:detay', pk=fatura.pk)
    else:
        form = FaturaKalemForm(instance=kalem)
    
    return render(request, 'fatura/kalem_form.html', {'form': form, 'fatura': fatura, 'kalem': kalem, 'title': 'Kalem Düzenle'})


@satis_required
@login_required
def kalem_sil(request, pk):
    kalem = get_object_or_404(FaturaKalem, pk=pk)
    fatura_pk = kalem.fatura.pk
    
    if request.method == 'POST':
        kalem.delete()
        log_action(request.user, 'delete', kalem, f'Fatura kalemi silindi: {kalem.urun_adi}')
        messages.success(request, 'Fatura kalemi başarıyla silindi.')
        return redirect('fatura:detay', pk=fatura_pk)
    
    return render(request, 'fatura/kalem_sil.html', {'kalem': kalem})


@login_required
def fatura_pdf(request, pk):
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from io import BytesIO
    import os
    
    fatura = get_object_or_404(Fatura, pk=pk)
    kalemler = fatura.kalemler.all().order_by('sira_no')
    
    # Response oluştur
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                           rightMargin=30, leftMargin=30, 
                           topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    # Türkçe karakter desteği için font ayarları
    try:
        # Sistem fontlarını kullan (Türkçe karakter desteği için)
        from reportlab.pdfbase.pdfmetrics import registerFontFamily
        # Helvetica fontları Türkçe karakterleri destekler
    except:
        pass
    
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
    
    # Başlık
    fatura_tipi = fatura.get_fatura_tipi_display().upper()
    elements.append(Paragraph(f'{fatura_tipi} FATURASI', title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Firma bilgileri ve fatura bilgileri
    from reportlab.platypus import KeepTogether
    
    # Sol taraf - Firma bilgileri (varsa)
    firma_bilgileri = []
    if fatura.cari:
        firma_bilgileri.append(Paragraph(f'<b>FATURAYI ALAN:</b>', styles['Normal']))
        firma_bilgileri.append(Paragraph(f'{fatura.cari.ad_soyad}', styles['Normal']))
        if fatura.cari.telefon:
            firma_bilgileri.append(Paragraph(f'Tel: {fatura.cari.telefon}', styles['Normal']))
        if fatura.cari.email:
            firma_bilgileri.append(Paragraph(f'E-posta: {fatura.cari.email}', styles['Normal']))
        if fatura.cari.adres:
            firma_bilgileri.append(Paragraph(f'{fatura.cari.adres}', styles['Normal']))
    
    # Sağ taraf - Fatura bilgileri
    info_data = [
        ['<b>Fatura No:</b>', fatura.fatura_no or '-'],
        ['<b>Fatura Tarihi:</b>', fatura.fatura_tarihi.strftime('%d.%m.%Y')],
        ['<b>Vade Tarihi:</b>', fatura.vade_tarihi.strftime('%d.%m.%Y') if fatura.vade_tarihi else '-'],
        ['<b>Durum:</b>', fatura.get_durum_display()],
    ]
    
    # Bilgi tablosu
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
    
    # Kalem tablosu
    kalem_headers = ['Sıra', 'Ürün/Hizmet', 'Miktar', 'Birim Fiyat', 'KDV %', 'Toplam']
    kalem_data = [kalem_headers]
    
    for kalem in kalemler:
        kalem_data.append([
            str(kalem.sira_no),
            kalem.urun_adi[:40] if len(kalem.urun_adi) > 40 else kalem.urun_adi,  # Uzun isimleri kısalt
            f'{kalem.miktar}',
            f'{kalem.birim_fiyat:,.2f} ₺',
            f'%{kalem.kdv_orani}',
            f'{kalem.toplam_tutar:,.2f} ₺'
        ])
    
    # Tablo genişlikleri - sayfa genişliğine uygun
    page_width = A4[0] - 60  # Margin'ler çıkarıldı
    kalem_table = Table(kalem_data, colWidths=[
        0.4*inch,      # Sıra
        2.8*inch,      # Ürün
        0.7*inch,      # Miktar
        1.0*inch,      # Birim Fiyat
        0.6*inch,      # KDV %
        1.0*inch       # Toplam
    ])
    
    kalem_table.setStyle(TableStyle([
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
        ('ALIGN', (0, 1), (0, -1), TA_CENTER),  # Sıra
        ('ALIGN', (1, 1), (1, -1), TA_LEFT),    # Ürün
        ('ALIGN', (2, 1), (2, -1), TA_CENTER), # Miktar
        ('ALIGN', (3, 1), (3, -1), TA_RIGHT),   # Birim Fiyat
        ('ALIGN', (4, 1), (4, -1), TA_CENTER),  # KDV
        ('ALIGN', (5, 1), (5, -1), TA_RIGHT),   # Toplam
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
    
    elements.append(kalem_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Toplam tablosu
    toplam_data = [
        ['<b>Ara Toplam:</b>', f'{fatura.toplam_tutar:,.2f} ₺'],
        ['<b>KDV Tutarı:</b>', f'{fatura.kdv_tutari:,.2f} ₺'],
    ]
    
    if fatura.iskonto_tutari > 0:
        toplam_data.append([f'<b>İskonto (%{fatura.iskonto_orani}):</b>', f'-{fatura.iskonto_tutari:,.2f} ₺'])
    
    toplam_data.append([f'<b><font size=14>GENEL TOPLAM:</font></b>', f'<b><font size=14>{fatura.genel_toplam:,.2f} ₺</font></b>'])
    
    toplam_table = Table(toplam_data, colWidths=[3.5*inch, 2.5*inch])
    toplam_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), TA_RIGHT),
        ('ALIGN', (1, 0), (1, -1), TA_RIGHT),
        ('FONTNAME', (0, 0), (0, -2), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -2), 10),
        ('FONTSIZE', (-1, -1), (-1, -1), 14),
        ('TEXTCOLOR', (-1, -1), (-1, -1), colors.HexColor('#d32f2f')),
        ('BACKGROUND', (-1, -1), (-1, -1), colors.HexColor('#fff3e0')),
        ('TOPPADDING', (-1, -1), (-1, -1), 10),
        ('BOTTOMPADDING', (-1, -1), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, -1), (-1, -1), 2, colors.HexColor('#d32f2f')),
    ]))
    
    elements.append(toplam_table)
    
    # Açıklama varsa ekle
    if fatura.aciklama:
        elements.append(Spacer(1, 0.2*inch))
        aciklama_style = ParagraphStyle(
            'Aciklama',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#666666'),
            alignment=TA_LEFT
        )
        elements.append(Paragraph(f'<b>Açıklama:</b> {fatura.aciklama}', aciklama_style))
    
    # PDF oluştur
    doc.build(elements)
    
    # Response hazırla
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(content_type='application/pdf; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="Fatura_{fatura.fatura_no}.pdf"'
    response.write(pdf)
    
    log_action(request.user, 'export', fatura, f'Fatura PDF export: {fatura.fatura_no}')
    return response


@login_required
def fatura_onizleme(request, pk):
    fatura = get_object_or_404(Fatura, pk=pk)
    kalemler = fatura.kalemler.all().order_by('sira_no')
    log_action(request.user, 'view', fatura, f'Fatura önizleme: {fatura.fatura_no}')
    return render(request, 'fatura/fatura_onizleme.html', {
        'fatura': fatura,
        'kalemler': kalemler
    })


@login_required
def fatura_kopyala(request, pk):
    orijinal_fatura = get_object_or_404(Fatura, pk=pk)
    
    yeni_fatura = Fatura.objects.create(
        fatura_no=f"{orijinal_fatura.fatura_no}_KOPYA_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        cari=orijinal_fatura.cari,
        fatura_tarihi=datetime.now().date(),
        vade_tarihi=orijinal_fatura.vade_tarihi,
        fatura_tipi=orijinal_fatura.fatura_tipi,
        durum='Beklemede',
        aciklama=f"Kopya: {orijinal_fatura.fatura_no}",
        olusturan=request.user
    )
    
    for kalem in orijinal_fatura.kalemler.all():
        FaturaKalem.objects.create(
            fatura=yeni_fatura,
            urun=kalem.urun,
            urun_adi=kalem.urun_adi,
            miktar=kalem.miktar,
            birim_fiyat=kalem.birim_fiyat,
            kdv_orani=kalem.kdv_orani,
            sira_no=kalem.sira_no
        )
    
    yeni_fatura.hesapla_toplamlar()
    log_action(request.user, 'create', yeni_fatura, f'Fatura kopyalandı: {orijinal_fatura.fatura_no} -> {yeni_fatura.fatura_no}')
    messages.success(request, f'Fatura başarıyla kopyalandı. Yeni fatura no: {yeni_fatura.fatura_no}')
    return redirect('fatura:detay', pk=yeni_fatura.pk)
