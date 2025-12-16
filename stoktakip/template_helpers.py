from __future__ import annotations

from datetime import datetime
from typing import Iterable, Mapping, Sequence

from django.urls import reverse
from django.utils.http import urlencode


def _format_currency(value) -> str:
    try:
        return f"{float(value):,.2f} ₺"
    except Exception:
        return str(value)


def generate_table_html(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    """
    Basit Bootstrap uyumlu tablo HTML'i üretir.
    """
    header_html = "".join(f"<th scope='col'>{h}</th>" for h in headers)
    body_html_parts: list[str] = []
    for row in rows:
        cols = "".join(f"<td>{cell}</td>" for cell in row)
        body_html_parts.append(f"<tr>{cols}</tr>")
    body_html = "".join(body_html_parts)
    return (
        "<div class='table-responsive'>"
        "<table class='table table-striped table-hover align-middle'>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{body_html}</tbody>"
        "</table>"
        "</div>"
    )


def generate_pagination_html(page_obj, request_params: Mapping[str, str], base_path: str) -> str:
    """
    Basit sayfalama HTML'i üretir. Mevcut query parametrelerini korur.
    """
    params = {k: v for k, v in request_params.items() if v not in (None, "", [])}
    items: list[str] = []

    def page_link(page_number: int, label: str, disabled: bool = False, active: bool = False) -> str:
        query = params | {"page": page_number}
        href = f"{base_path}?{urlencode(query)}"
        cls = ["page-item"]
        if disabled:
            cls.append("disabled")
        if active:
            cls.append("active")
        class_attr = " ".join(cls)
        return f"<li class='{class_attr}'><a class='page-link' href='{href}'>{label}</a></li>"

    # Prev
    items.append(page_link(page_obj.previous_page_number() if page_obj.has_previous() else 1, "&laquo;", not page_obj.has_previous()))

    # Numbers (yakındaki 5 sayfa)
    current = page_obj.number
    start = max(current - 2, 1)
    end = min(current + 2, page_obj.paginator.num_pages)
    for num in range(start, end + 1):
        items.append(page_link(num, str(num), active=(num == current)))

    # Next
    items.append(page_link(page_obj.next_page_number() if page_obj.has_next() else page_obj.paginator.num_pages, "&raquo;", not page_obj.has_next()))

    return f"<nav><ul class='pagination'>{''.join(items)}</ul></nav>"


def prepare_urun_table_data(urunler: Iterable) -> list[dict]:
    data = []
    for urun in urunler:
        data.append(
            {
                "kod": f"UR-{urun.pk}",
                "ad": urun.ad,
                "kategori": getattr(urun.kategori, "ad", "-") or "-",
                "barkod": urun.barkod or "-",
                "birim": urun.birim or "-",
                "fiyat": _format_currency(urun.fiyat),
                "stok": urun.mevcut_stok,
                "actions": _urun_actions(urun),
            }
        )
    return data


def prepare_cari_table_data(cariler: Iterable) -> list[dict]:
    data = []
    for cari in cariler:
        son_islem = cari.son_islem_tarihi
        son_islem_str = son_islem.strftime("%d.%m.%Y %H:%M") if son_islem else "-"
        data.append(
            {
                "id": cari.pk,
                "ad_soyad": cari.ad_soyad,
                "kategori": getattr(cari, "get_kategori_display", lambda: cari.kategori)(),
                "tc_vkn": cari.tc_vkn or "-",
                "telefon": cari.telefon or "-",
                "email": cari.email or "-",
                "bakiye": _format_currency(cari.bakiye),
                "son_islem": son_islem_str,
                "actions": _cari_actions(cari),
            }
        )
    return data


def prepare_fatura_table_data(faturalar: Iterable) -> list[dict]:
    data = []
    for fatura in faturalar:
        tarih = fatura.fatura_tarihi.strftime("%d.%m.%Y") if fatura.fatura_tarihi else "-"
        tip = getattr(fatura, "get_fatura_tipi_display", lambda: fatura.fatura_tipi)()
        durum = getattr(fatura, "get_durum_display", lambda: fatura.durum)()
        data.append(
            {
                "fatura_no": fatura.fatura_no or "-",
                "tarih": tarih,
                "cari": getattr(fatura.cari, "ad_soyad", "-") if fatura.cari else "-",
                "tip": tip,
                "genel_toplam": _format_currency(fatura.genel_toplam),
                "durum": durum,
                "actions": _fatura_actions(fatura),
            }
        )
    return data


def _urun_actions(urun) -> str:
    return (
        f"<a class='btn btn-sm btn-outline-primary me-1' href='{reverse('stok:duzenle', args=[urun.pk])}'>Düzenle</a>"
        f"<a class='btn btn-sm btn-outline-info me-1' href='{reverse('stok:hareketler', args=[urun.pk])}'>Hareketler</a>"
        f"<a class='btn btn-sm btn-outline-danger' href='{reverse('stok:sil', args=[urun.pk])}'>Sil</a>"
    )


def _cari_actions(cari) -> str:
    return (
        f"<a class='btn btn-sm btn-outline-primary me-1' href='{reverse('cari:detay', args=[cari.pk])}'>Detay</a>"
        f"<a class='btn btn-sm btn-outline-secondary me-1' href='{reverse('cari:duzenle', args=[cari.pk])}'>Düzenle</a>"
        f"<a class='btn btn-sm btn-outline-danger' href='{reverse('cari:sil', args=[cari.pk])}'>Sil</a>"
    )


def _fatura_actions(fatura) -> str:
    return (
        f"<a class='btn btn-sm btn-outline-primary me-1' href='{reverse('fatura:detay', args=[fatura.pk])}'>Detay</a>"
        f"<a class='btn btn-sm btn-outline-secondary me-1' href='{reverse('fatura:duzenle', args=[fatura.pk])}'>Düzenle</a>"
        f"<a class='btn btn-sm btn-outline-danger' href='{reverse('fatura:sil', args=[fatura.pk])}'>Sil</a>"
    )

