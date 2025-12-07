from django.contrib import admin
from .models import MasrafKategori, Masraf


@admin.register(MasrafKategori)
class MasrafKategoriAdmin(admin.ModelAdmin):
    list_display = ['ad', 'olusturma_tarihi']
    search_fields = ['ad', 'aciklama']
    readonly_fields = ['olusturma_tarihi']


@admin.register(Masraf)
class MasrafAdmin(admin.ModelAdmin):
    list_display = ['masraf_no', 'kategori', 'aciklama', 'tutar', 'tarih', 'odeme_yontemi', 'durum', 'olusturan']
    list_filter = ['kategori', 'odeme_yontemi', 'durum', 'tarih']
    search_fields = ['masraf_no', 'aciklama', 'belge_no']
    list_editable = ['durum']
    readonly_fields = ['olusturma_tarihi', 'guncelleme_tarihi']
    date_hierarchy = 'tarih'
    fieldsets = (
        ('Masraf Bilgileri', {
            'fields': ('masraf_no', 'kategori', 'aciklama', 'tutar', 'tarih')
        }),
        ('Ödeme Bilgileri', {
            'fields': ('odeme_yontemi', 'durum', 'belge_no')
        }),
        ('Sistem', {
            'fields': ('olusturan', 'olusturma_tarihi', 'guncelleme_tarihi'),
            'classes': ('collapse',)
        }),
    )
