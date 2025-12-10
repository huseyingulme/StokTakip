from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Urun
from .utils import generate_barcode, generate_qr_code
import qrcode
from io import BytesIO


@login_required
def barcode_image(request, pk):
    """Ürün barkod görselini döndürür"""
    urun = get_object_or_404(Urun, pk=pk)
    buffer = generate_barcode(urun)
    
    if buffer:
        response = HttpResponse(buffer.getvalue(), content_type='image/png')
        response['Content-Disposition'] = f'inline; filename="barcode_{urun.id}.png"'
        return response
    else:
        return HttpResponse("Barkod oluşturulamadı", status=400)


@login_required
def qr_code_image(request, pk):
    """Ürün QR kod görselini döndürür"""
    urun = get_object_or_404(Urun, pk=pk)
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr_data = f"URUN:{urun.id}:{urun.barkod or ''}"
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    response = HttpResponse(buffer.getvalue(), content_type='image/png')
    response['Content-Disposition'] = f'inline; filename="qr_{urun.id}.png"'
    return response


@login_required
def barcode_scanner(request):
    """Barkod scanner sayfası"""
    from django.shortcuts import render
    return render(request, 'stok/barcode_scanner.html')

