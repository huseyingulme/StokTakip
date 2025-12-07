from django.contrib import admin
from .models import Kategori, Urun, StokHareketi


@admin.register(Kategori)
class KategoriAdmin(admin.ModelAdmin):
    list_display = ['ad', 'olusturma_tarihi']
    search_fields = ['ad', 'aciklama']
    readonly_fields = ['olusturma_tarihi']


@admin.register(Urun)
class UrunAdmin(admin.ModelAdmin):
    list_display = ['ad', 'kategori', 'barkod', 'fiyat', 'stok_adedi', 'birim', 'olusturma_tarihi']
    list_filter = ['kategori', 'birim', 'olusturma_tarihi']
    search_fields = ['ad', 'barkod', 'aciklama']
    list_editable = ['fiyat', 'stok_adedi']
    readonly_fields = ['olusturma_tarihi', 'guncelleme_tarihi']
    fieldsets = (
        ('Ürün Bilgileri', {
            'fields': ('ad', 'kategori', 'barkod', 'birim', 'aciklama')
        }),
        ('Fiyat ve Stok', {
            'fields': ('fiyat', 'stok_adedi')
        }),
        ('Tarihler', {
            'fields': ('olusturma_tarihi', 'guncelleme_tarihi'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StokHareketi)
class StokHareketiAdmin(admin.ModelAdmin):
    list_display = ['urun', 'hareket_tipi', 'miktar', 'kullanici', 'olusturma_tarihi']
    list_filter = ['hareket_tipi', 'olusturma_tarihi']
    search_fields = ['urun__ad', 'aciklama']
    readonly_fields = ['olusturma_tarihi']
    fieldsets = (
        ('Hareket Bilgileri', {
            'fields': ('urun', 'hareket_tipi', 'miktar', 'kullanici')
        }),
        ('Diğer', {
            'fields': ('aciklama', 'olusturma_tarihi')
        }),
    )

