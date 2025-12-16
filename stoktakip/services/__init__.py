"""
Service (wrapper) katmanı.

Bu paket altında:
- İş kuralları (ör. fatura onayı, muhasebe fişi)
- Ortak çıktı üreticileri (PDF, Excel, mail)
gibi tekrar kullanılabilir wrapper fonksiyonları tutulur.

Kullanım:
    from stoktakip.services.fatura_service import create_fatura, update_fatura
    from stoktakip.services.stok_service import create_stok_hareketleri_from_fatura
    from stoktakip.services.cari_service import create_or_update_cari_hareketi_from_fatura
"""

# Servisleri export et (opsiyonel, ama iyi bir pratik)
from .fatura_service import (
    create_fatura,
    update_fatura,
    delete_fatura,
    copy_fatura,
    recalculate_fatura_totals,
)
from .fatura_kalem_service import (
    add_fatura_kalem,
    update_fatura_kalem,
    delete_fatura_kalem,
    add_fatura_kalemler_from_post_data,
)
from .stok_service import (
    create_stok_hareketleri_from_fatura,
    delete_stok_hareketleri_for_fatura,
    create_stok_hareketi,
)
from .cari_service import (
    create_or_update_cari_hareketi_from_fatura,
    delete_cari_hareketi_for_fatura,
    create_cari_hareketi,
)

__all__ = [
    # Fatura servisleri
    'create_fatura',
    'update_fatura',
    'delete_fatura',
    'copy_fatura',
    'recalculate_fatura_totals',
    # Fatura kalem servisleri
    'add_fatura_kalem',
    'update_fatura_kalem',
    'delete_fatura_kalem',
    'add_fatura_kalemler_from_post_data',
    # Stok servisleri
    'create_stok_hareketleri_from_fatura',
    'delete_stok_hareketleri_for_fatura',
    'create_stok_hareketi',
    # Cari servisleri
    'create_or_update_cari_hareketi_from_fatura',
    'delete_cari_hareketi_for_fatura',
    'create_cari_hareketi',
]

