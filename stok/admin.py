from django.contrib import admin
from .models import Urun


@admin.register(Urun)
class UrunAdmin(admin.ModelAdmin):
    list_display = ['ad', 'barkod', 'fiyat', 'stok_adedi', 'birim', 'olusturma_tarihi']
    list_filter = ['birim', 'olusturma_tarihi']
    search_fields = ['ad', 'barkod', 'aciklama']
    list_editable = ['fiyat', 'stok_adedi']
    readonly_fields = ['olusturma_tarihi', 'guncelleme_tarihi']
    fieldsets = (
        ('Ürün Bilgileri', {
            'fields': ('ad', 'barkod', 'birim', 'aciklama')
        }),
        ('Fiyat ve Stok', {
            'fields': ('fiyat', 'stok_adedi')
        }),
        ('Tarihler', {
            'fields': ('olusturma_tarihi', 'guncelleme_tarihi'),
            'classes': ('collapse',)
        }),
    )

