from django.contrib import admin
from .models import HesapKart, FinansHareketi


@admin.register(HesapKart)
class HesapKartAdmin(admin.ModelAdmin):
    list_display = ['ad', 'hesap_tipi', 'hesap_no', 'bakiye', 'durum', 'olusturma_tarihi']
    list_filter = ['hesap_tipi', 'durum']
    search_fields = ['ad', 'hesap_no', 'aciklama']
    list_editable = ['durum']
    readonly_fields = ['olusturma_tarihi', 'guncelleme_tarihi']
    fieldsets = (
        ('Hesap Bilgileri', {
            'fields': ('ad', 'hesap_tipi', 'hesap_no', 'bakiye')
        }),
        ('Diğer', {
            'fields': ('aciklama', 'durum', 'olusturma_tarihi', 'guncelleme_tarihi')
        }),
    )


@admin.register(FinansHareketi)
class FinansHareketiAdmin(admin.ModelAdmin):
    list_display = ['hareket_no', 'hesap', 'hareket_tipi', 'tutar', 'tarih', 'olusturan']
    list_filter = ['hareket_tipi', 'tarih']
    search_fields = ['hareket_no', 'aciklama', 'belge_no']
    readonly_fields = ['olusturma_tarihi']
    date_hierarchy = 'tarih'
    fieldsets = (
        ('Hareket Bilgileri', {
            'fields': ('hareket_no', 'hesap', 'hedef_hesap', 'hareket_tipi', 'tutar', 'tarih')
        }),
        ('Diğer', {
            'fields': ('aciklama', 'belge_no', 'olusturan', 'olusturma_tarihi')
        }),
    )
