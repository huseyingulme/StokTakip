from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from finans.models import Account, JournalEntry, JournalLine
from fatura.models import Fatura


def _get_or_create_account(code: str, name: str, acc_type: str) -> Account:
    """
    Yardımcı fonksiyon: Hesap planında hesabi bulur veya oluşturur.
    """

    account, _ = Account.objects.get_or_create(
        code=code,
        defaults={"name": name, "type": acc_type},
    )
    # İsim/tip güncel değilse güncelle
    changed = False
    if account.name != name:
        account.name = name
        changed = True
    if account.type != acc_type:
        account.type = acc_type
        changed = True
    if changed:
        account.save(update_fields=["name", "type"])
    return account


@transaction.atomic
def create_sales_journal(fatura: Fatura) -> JournalEntry:
    

    if not fatura.fatura_no:
        raise ValueError("Muhasebe fişi için fatura numarası zorunludur.")

    # Zaten fiş oluşturulmuş mu?
    existing = JournalEntry.objects.filter(
        source_invoice_number=fatura.fatura_no
    ).first()
    if existing:
        return existing

    # Hesapları hazırla
    acc_120 = _get_or_create_account("120", "Alıcılar", "Varlık")
    acc_600 = _get_or_create_account("600", "Yurtiçi Satışlar", "Gelir")
    acc_391 = _get_or_create_account("391", "Hesaplanan KDV", "Yükümlülük")

    # Tutarlar
    toplam = fatura.genel_toplam or Decimal("0.00")
    kdv = fatura.kdv_tutari or Decimal("0.00")
    net = toplam - kdv

    if toplam <= 0:
        raise ValueError("Genel toplamı 0 veya negatif olan faturadan fiş üretilemez.")

    # Fiş no basit format: FIS-YYYYMMDD-<fatura_no>
    tarih = fatura.fatura_tarihi or timezone.now().date()
    fis_no = f"FIS-{tarih.strftime('%Y%m%d')}-{fatura.fatura_no}"

    entry = JournalEntry.objects.create(
        fis_no=fis_no,
        date=tarih,
        description=f"Satış Faturası {fatura.fatura_no}",
        source_invoice_number=fatura.fatura_no,
    )

    JournalLine.objects.bulk_create(
        [
            JournalLine(
                entry=entry,
                account=acc_120,
                debit=toplam,
                credit=Decimal("0.00"),
            ),
            JournalLine(
                entry=entry,
                account=acc_600,
                debit=Decimal("0.00"),
                credit=net,
            ),
            JournalLine(
                entry=entry,
                account=acc_391,
                debit=Decimal("0.00"),
                credit=kdv,
            ),
        ]
    )

    # Borç = Alacak kontrolü
    if not entry.is_balanced:
        raise ValueError("Oluşturulan muhasebe fişi dengede değil (borç != alacak).")

    return entry

