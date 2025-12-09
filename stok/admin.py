from django.contrib import admin
from .models import Kategori, Urun, StokHareketi


@admin.register(Kategori)
class KategoriAdmin(admin.ModelAdmin):
    list_display = ['ad', 'olusturma_tarihi']
    search_fields = ['ad', 'aciklama']
    readonly_fields = ['olusturma_tarihi']


@admin.register(Urun)
class UrunAdmin(admin.ModelAdmin):
    list_display = ['ad', 'kategori', 'barkod', 'fiyat', 'mevcut_stok', 'birim', 'olusturma_tarihi']
    list_filter = ['kategori', 'birim', 'olusturma_tarihi']
    search_fields = ['ad', 'barkod']
    list_editable = ['fiyat']
    readonly_fields = ['olusturma_tarihi', 'mevcut_stok', 'min_stok_adedi']
    fieldsets = (
        ('Ürün Bilgileri', {
            'fields': ('ad', 'kategori', 'barkod', 'birim')
        }),
        ('Fiyat ve Stok', {
            'fields': ('fiyat', 'mevcut_stok', 'min_stok_adedi')
        }),
        ('Tarihler', {
            'fields': ('olusturma_tarihi',),
            'classes': ('collapse',)
        }),
    )


@admin.register(StokHareketi)
class StokHareketiAdmin(admin.ModelAdmin):
    list_display = ['urun', 'islem_turu', 'miktar', 'olusturan', 'tarih']
    list_filter = ['islem_turu', 'tarih']
    search_fields = ['urun__ad', 'aciklama']
    readonly_fields = ['tarih']
    fieldsets = (
        ('Hareket Bilgileri', {
            'fields': ('urun', 'islem_turu', 'miktar', 'olusturan')
        }),
        ('Diğer', {
            'fields': ('aciklama', 'tarih')
        }),
    )

