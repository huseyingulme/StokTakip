"""
Template helper functions to reduce HTML code in templates.
These functions generate HTML strings that can be used in templates.
"""
from typing import Any, Optional, Dict, List
from django.core.paginator import Page
from django.utils.safestring import SafeString, mark_safe
from django.urls import reverse
from urllib.parse import urlencode


def generate_pagination_html(
    page_obj: Page, 
    request_params: Optional[Dict[str, Any]] = None,
    base_path: str = ''
) -> SafeString:
    """
    Generate pagination HTML from a page object.
    Reduces HTML code in templates.
    
    Args:
        page_obj: Django Page object from Paginator
        request_params: Dictionary of query parameters to preserve in pagination links
        base_path: Base path for the URL (e.g., '/stok/' or request.path)
    
    Returns:
        Safe HTML string for pagination navigation
    """
    if not page_obj.has_other_pages():
        return ''
    
    request_params = request_params or {}
    # Remove 'page' from params if exists
    clean_params = {k: v for k, v in request_params.items() if v and k != 'page'}
    
    html_parts = ['<nav aria-label="Sayfa navigasyonu"><ul class="pagination">']
    
    # First and Previous
    if page_obj.has_previous():
        # First page
        first_params = clean_params.copy()
        first_params['page'] = 1
        first_url = f"{base_path}?{urlencode(first_params)}" if first_params else f"{base_path}?page=1"
        html_parts.append(f'<li class="page-item"><a class="page-link" href="{first_url}">İlk</a></li>')
        
        # Previous page
        prev_params = clean_params.copy()
        prev_params['page'] = page_obj.previous_page_number
        prev_url = f"{base_path}?{urlencode(prev_params)}" if prev_params else f"{base_path}?page={page_obj.previous_page_number}"
        html_parts.append(f'<li class="page-item"><a class="page-link" href="{prev_url}">Önceki</a></li>')
    
    # Current page
    html_parts.append(f'<li class="page-item active"><span class="page-link">Sayfa {page_obj.number} / {page_obj.paginator.num_pages}</span></li>')
    
    # Next and Last
    if page_obj.has_next():
        # Next page
        next_params = clean_params.copy()
        next_params['page'] = page_obj.next_page_number
        next_url = f"{base_path}?{urlencode(next_params)}" if next_params else f"{base_path}?page={page_obj.next_page_number}"
        html_parts.append(f'<li class="page-item"><a class="page-link" href="{next_url}">Sonraki</a></li>')
        
        # Last page
        last_params = clean_params.copy()
        last_params['page'] = page_obj.paginator.num_pages
        last_url = f"{base_path}?{urlencode(last_params)}" if last_params else f"{base_path}?page={page_obj.paginator.num_pages}"
        html_parts.append(f'<li class="page-item"><a class="page-link" href="{last_url}">Son</a></li>')
    
    html_parts.append('</ul></nav>')
    return mark_safe(''.join(html_parts))


def generate_badge_html(
    text: str, 
    badge_type: str = 'primary', 
    extra_classes: str = ''
) -> SafeString:
    """
    Generate badge HTML.
    
    Args:
        text: Badge text content
        badge_type: Badge type (primary, success, danger, warning, info, secondary)
        extra_classes: Additional CSS classes
    
    Returns:
        Safe HTML string for badge
    """
    classes = f'badge bg-{badge_type}'
    if extra_classes:
        classes += f' {extra_classes}'
    return mark_safe(f'<span class="{classes}">{text}</span>')


def generate_action_buttons(actions: List[Dict[str, Any]]) -> SafeString:
    """
    Generate action buttons HTML.
    
    Args:
        actions: List of dicts with keys: url, icon, title, btn_class
    
    Returns:
        Safe HTML string for action buttons
    """
    html_parts = ['<div class="action-buttons">']
    for action in actions:
        btn_class = action.get('btn_class', 'btn-sm btn-info')
        icon = action.get('icon', 'bi-circle')
        title = action.get('title', '')
        url = action.get('url', '#')
        html_parts.append(f'<a href="{url}" class="btn {btn_class}" title="{title}"><i class="bi {icon}"></i></a>')
    html_parts.append('</div>')
    return mark_safe(''.join(html_parts))


def generate_table_row(
    row_data: List[Any], 
    row_type: str = 'td'
) -> SafeString:
    """
    Generate table row HTML.
    
    Args:
        row_data: List of cell values
        row_type: 'td' or 'th'
    
    Returns:
        Safe HTML string for table row
    """
    cells = ''.join([f'<{row_type}>{cell}</{row_type}>' for cell in row_data])
    return mark_safe(f'<tr>{cells}</tr>')


def generate_table_html(
    headers: List[str], 
    rows: List[List[Any]], 
    table_classes: str = 'table table-hover', 
    extra_attrs: str = ''
) -> SafeString:
    """
    Generate complete table HTML.
    
    Args:
        headers: List of header texts
        rows: List of lists (row data)
        table_classes: CSS classes for table
        extra_attrs: Additional HTML attributes
    
    Returns:
        Safe HTML string for complete table
    """
    html_parts = [f'<div class="table-responsive"><table class="{table_classes}" {extra_attrs}>']
    
    # Header
    if headers:
        header_row = ''.join([f'<th>{h}</th>' for h in headers])
        html_parts.append(f'<thead><tr>{header_row}</tr></thead>')
    
    # Body
    html_parts.append('<tbody>')
    for row in rows:
        row_cells = ''.join([f'<td>{cell}</td>' for cell in row])
        html_parts.append(f'<tr>{row_cells}</tr>')
    html_parts.append('</tbody>')
    
    html_parts.append('</table></div>')
    return mark_safe(''.join(html_parts))


def generate_filter_form_html(
    filters: List[Dict[str, Any]], 
    form_action: str = '', 
    form_method: str = 'get'
) -> SafeString:
    """
    Generate filter form HTML.
    
    Args:
        filters: List of dicts with keys: name, label, input_type, value, options (for select)
        form_action: Form action URL
        form_method: HTTP method (get/post)
    
    Returns:
        Safe HTML string for filter form
    """
    html_parts = [f'<form method="{form_method}" action="{form_action}" class="mb-4">']
    html_parts.append('<div class="row g-3 mb-3">')
    
    for filter_item in filters:
        name = filter_item.get('name', '')
        label = filter_item.get('label', '')
        input_type = filter_item.get('input_type', 'text')
        value = filter_item.get('value', '')
        placeholder = filter_item.get('placeholder', '')
        col_class = filter_item.get('col_class', 'col-md-3')
        options = filter_item.get('options', [])
        
        html_parts.append(f'<div class="{col_class}">')
        if label:
            html_parts.append(f'<label class="form-label">{label}</label>')
        
        if input_type == 'select' and options:
            html_parts.append(f'<select name="{name}" class="form-select">')
            for opt in options:
                opt_value = opt.get('value', '')
                opt_text = opt.get('text', '')
                selected = 'selected' if str(opt_value) == str(value) else ''
                html_parts.append(f'<option value="{opt_value}" {selected}>{opt_text}</option>')
            html_parts.append('</select>')
        else:
            html_parts.append(f'<input type="{input_type}" name="{name}" class="form-control" value="{value}" placeholder="{placeholder}">')
        
        html_parts.append('</div>')
    
    html_parts.append('</div>')
    html_parts.append('<div class="row"><div class="col-md-12">')
    html_parts.append('<button type="submit" class="btn btn-primary"><i class="bi bi-search"></i> Filtrele</button>')
    html_parts.append('</div></div>')
    html_parts.append('</form>')
    
    return mark_safe(''.join(html_parts))


def prepare_cari_table_data(cariler: Any) -> List[Dict[str, Any]]:
    """
    Prepare cari data for table display.
    
    Args:
        cariler: QuerySet or list of Cari objects
    
    Returns:
        List of dicts with formatted data for table display
    """
    table_data = []
    for cari in cariler:
        # Format kategori badge
        kategori_map = {
            'musteri': ('Müşteri', 'primary'),
            'tedarikci': ('Tedarikçi', 'warning'),
            'her_ikisi': ('Her İkisi', 'info')
        }
        kategori_text, kategori_class = kategori_map.get(cari.kategori, ('-', 'secondary'))
        kategori_badge = f'<span class="badge bg-{kategori_class}">{kategori_text}</span>'
        if cari.durum == 'pasif':
            kategori_badge += ' <span class="badge bg-secondary">Pasif</span>'
        
        # Format bakiye
        # Bakiye mantığı: bakiye = alacak_toplam - borc_toplam
        # Pozitif bakiye = biz ona borçluyuz (biz ona borçluyuz)
        # Negatif bakiye = o bize borçlu (bizden alacaklıyız)
        # 
        # Renk kodlaması:
        # Yeşil: Onun bize borcu var (bizden alacaklıyız) = Negatif bakiye
        # Kırmızı: Bizim ona borcumuz var (biz ona borçluyuz) = Pozitif bakiye
        # 
        # Müşteri için: Pozitif bakiye = Biz müşteriye borçluyuz = Kırmızı
        # Müşteri için: Negatif bakiye = Müşteri bize borçlu = Yeşil
        # 
        # Tedarikçi için: Pozitif bakiye = Biz tedarikçiye borçluyuz = Kırmızı
        # Tedarikçi için: Negatif bakiye = Tedarikçi bize borçlu = Yeşil
        bakiye_abs = abs(cari.bakiye)
        
        if cari.kategori == 'musteri':
            # Müşteri için: Pozitif = Kırmızı (Biz müşteriye borçluyuz), Negatif = Yeşil (Müşteri bize borçlu)
            if cari.bakiye > 0:
                bakiye_html = f'<span class="badge bg-danger">{cari.bakiye:.2f} ₺</span>'
            elif cari.bakiye < 0:
                bakiye_html = f'<span class="badge bg-success">{bakiye_abs:.2f} ₺</span>'
            else:
                bakiye_html = '<span class="badge bg-secondary">0.00 ₺</span>'
        else:
            # Tedarikçi veya her_ikisi için: Pozitif = Kırmızı (Biz tedarikçiye borçluyuz), Negatif = Yeşil (Tedarikçi bize borçlu)
            if cari.bakiye > 0:
                bakiye_html = f'<span class="badge bg-danger">{cari.bakiye:.2f} ₺</span>'
            elif cari.bakiye < 0:
                bakiye_html = f'<span class="badge bg-success">{bakiye_abs:.2f} ₺</span>'
            else:
                bakiye_html = '<span class="badge bg-secondary">0.00 ₺</span>'
        
        # Risk uyarısı
        risk_icon = ''
        if hasattr(cari, 'risk_asimi_var_mi') and cari.risk_asimi_var_mi:
            risk_icon = '<span class="badge bg-danger ms-2" title="Risk limiti aşıldı!">⚠</span>'
        
        # Action buttons
        actions = [
            {'url': reverse('cari:detay', args=[cari.pk]), 'icon': 'bi-eye', 'title': 'Detay', 'btn_class': 'btn-sm btn-info'},
            {'url': reverse('cari:duzenle', args=[cari.pk]), 'icon': 'bi-pencil', 'title': 'Düzenle', 'btn_class': 'btn-sm btn-warning'},
            {'url': reverse('cari:sil', args=[cari.pk]), 'icon': 'bi-trash', 'title': 'Sil', 'btn_class': 'btn-sm btn-danger'}
        ]
        action_buttons = generate_action_buttons(actions)
        
        table_data.append({
            'id': cari.id,
            'ad_soyad': f'<strong>{cari.ad_soyad}</strong>{risk_icon}',
            'kategori': kategori_badge,
            'tc_vkn': cari.tc_vkn or '-',
            'telefon': cari.telefon or '-',
            'email': cari.email or '-',
            'bakiye': bakiye_html,
            'son_islem': cari.son_islem_tarihi.strftime('%d.%m.%Y') if hasattr(cari, 'son_islem_tarihi') and cari.son_islem_tarihi else '-',
            'actions': action_buttons
        })
    
    return table_data


def prepare_urun_table_data(urunler: Any) -> List[Dict[str, Any]]:
    """
    Prepare urun data for table display.
    
    Args:
        urunler: QuerySet or list of Urun objects
    
    Returns:
        List of dicts with formatted data for table display
    """
    table_data = []
    for urun in urunler:
        # Stok badge - Renk kodlaması: Negatif = Kırmızı, Pozitif = Yeşil, Sıfır = Beyaz
        if urun.mevcut_stok < 0:
            stok_class = 'bg-danger'
        elif urun.mevcut_stok > 0:
            stok_class = 'bg-success'
        else:
            stok_class = 'bg-secondary'  # Sıfır için beyaz/gri
        stok_badge = f'<span class="badge {stok_class}">{urun.mevcut_stok} {urun.birim}</span>'
        
        # Action buttons
        actions = [
            {'url': reverse('stok:stok_duzenle', args=[urun.pk]), 'icon': 'bi-pencil-square', 'title': 'Stok Düzenle', 'btn_class': 'btn-sm btn-info'},
            {'url': reverse('stok:hareketler', args=[urun.pk]), 'icon': 'bi-list-ul', 'title': 'Hareketler', 'btn_class': 'btn-sm btn-secondary'},
            {'url': reverse('stok:duzenle', args=[urun.pk]), 'icon': 'bi-pencil', 'title': 'Düzenle', 'btn_class': 'btn-sm btn-warning'},
            {'url': reverse('stok:sil', args=[urun.pk]), 'icon': 'bi-trash', 'title': 'Sil', 'btn_class': 'btn-sm btn-danger'}
        ]
        action_buttons = generate_action_buttons(actions)
        
        table_data.append({
            'kod': urun.id,
            'ad': f'<strong>{urun.ad}</strong>',
            'kategori': urun.kategori.ad if urun.kategori else '-',
            'barkod': urun.barkod or '-',
            'birim': urun.birim,
            'fiyat': f'{urun.fiyat:.2f} ₺',
            'stok': stok_badge,
            'actions': action_buttons
        })
    
    return table_data


def prepare_fatura_table_data(faturalar: Any) -> List[Dict[str, Any]]:
    """
    Prepare fatura data for table display.
    
    Args:
        faturalar: QuerySet or list of Fatura objects
    
    Returns:
        List of dicts with formatted data for table display
    """
    table_data = []
    for fatura in faturalar:
        # Tip badge
        tip_class = 'bg-success' if fatura.fatura_tipi == 'Satis' else 'bg-warning'
        tip_badge = f'<span class="badge {tip_class}">{fatura.get_fatura_tipi_display()}</span>'
        
        # Durum badge
        durum_map = {
            'Odendi': 'bg-success',
            'Iptal': 'bg-danger',
            'Beklemede': 'bg-warning'
        }
        durum_class = durum_map.get(fatura.durum, 'bg-secondary')
        durum_badge = f'<span class="badge {durum_class}">{fatura.get_durum_display()}</span>'
        
        # Action buttons
        actions = [
            {'url': reverse('fatura:detay', args=[fatura.pk]), 'icon': 'bi-eye', 'title': 'Detay', 'btn_class': 'btn-sm btn-info'},
            {'url': reverse('fatura:duzenle', args=[fatura.pk]), 'icon': 'bi-pencil', 'title': 'Düzenle', 'btn_class': 'btn-sm btn-warning'},
            {'url': reverse('fatura:sil', args=[fatura.pk]), 'icon': 'bi-trash', 'title': 'Sil', 'btn_class': 'btn-sm btn-danger'}
        ]
        action_buttons = generate_action_buttons(actions)
        
        table_data.append({
            'fatura_no': f'<strong>{fatura.fatura_no}</strong>',
            'tarih': fatura.fatura_tarihi.strftime('%d.%m.%Y'),
            'cari': fatura.cari.ad_soyad if fatura.cari else '-',
            'tip': tip_badge,
            'genel_toplam': f'{fatura.genel_toplam:.2f} ₺',
            'durum': durum_badge,
            'actions': action_buttons
        })
    
    return table_data

