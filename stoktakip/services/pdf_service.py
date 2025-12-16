from __future__ import annotations

from io import BytesIO
from typing import Mapping, Any

from django.http import HttpResponse
from django.template.loader import get_template

from xhtml2pdf import pisa  # pyright: ignore[reportMissingImports]


def render_pdf_response(html: str, filename: str) -> HttpResponse:
    """
    Düşük seviye PDF wrapper'ı.

    - Verilen HTML'den PDF üretir
    - Uygun Content-Type ve Content-Disposition header'ları ile HttpResponse döner
    """
    result = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=result)

    if pisa_status.err:
        # Üst seviye wrapper'lar try/except ile bu hatayı yakalayabilir.
        raise ValueError("PDF oluşturma sırasında bir hata oluştu.")

    response = HttpResponse(result.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response


def render_template_to_pdf_response(
    template_name: str,
    context: Mapping[str, Any],
    filename: str,
) -> HttpResponse:
    """
    Yüksek seviye PDF wrapper'ı.

    - Django template'i render eder
    - Ortaya çıkan HTML'i PDF'e çevirip HttpResponse döner
    - View'ler doğrudan bu fonksiyonu kullanmalı; PDF detayını bilmemeli
    """
    template = get_template(template_name)
    html = template.render(context)
    return render_pdf_response(html, filename)

