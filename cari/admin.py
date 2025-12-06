from django.contrib import admin
from .models import Musteri


@admin.register(Musteri)
class MusteriAdmin(admin.ModelAdmin):
    list_display = ['ad_soyad', 'tip', 'telefon', 'email', 'sehir', 'bakiye', 'olusturma_tarihi']
    list_filter = ['tip', 'sehir', 'olusturma_tarihi']
    search_fields = ['ad_soyad', 'tc_vkn', 'telefon', 'email', 'unvan']
    list_editable = ['bakiye']
    readonly_fields = ['olusturma_tarihi', 'guncelleme_tarihi']
    fieldsets = (
        ('Kişi/Kurum Bilgileri', {
            'fields': ('ad_soyad', 'unvan', 'tc_vkn', 'tip')
        }),
        ('İletişim Bilgileri', {
            'fields': ('telefon', 'email', 'adres', 'sehir')
        }),
        ('Mali Bilgiler', {
            'fields': ('bakiye',)
        }),
        ('Tarihler', {
            'fields': ('olusturma_tarihi', 'guncelleme_tarihi'),
            'classes': ('collapse',)
        }),
    )

