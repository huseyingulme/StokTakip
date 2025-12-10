import qrcode
from io import BytesIO
from django.core.files import File
from django.core.files.base import ContentFile
from PIL import Image
import barcode
from barcode.writer import ImageWriter


def generate_qr_code(urun):
    """Ürün için QR kod oluşturur"""
    if urun.qr_kod:
        return urun.qr_kod.url
    
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
    
    filename = f'qr_{urun.id}.png'
    urun.qr_kod.save(filename, ContentFile(buffer.read()), save=False)
    return urun.qr_kod.url


def generate_barcode(urun):
    """Ürün için barkod oluşturur (EAN13 formatında)"""
    if not urun.barkod:
        return None
    
    try:
        # EAN13 formatında barkod oluştur
        ean = barcode.get_barcode_class('ean13')
        barcode_instance = ean(urun.barkod, writer=ImageWriter())
        buffer = BytesIO()
        barcode_instance.write(buffer)
        buffer.seek(0)
        return buffer
    except Exception as e:
        # Eğer barkod geçersizse Code128 formatını dene
        try:
            code128 = barcode.get_barcode_class('code128')
            barcode_instance = code128(urun.barkod, writer=ImageWriter())
            buffer = BytesIO()
            barcode_instance.write(buffer)
            buffer.seek(0)
            return buffer
        except:
            return None

