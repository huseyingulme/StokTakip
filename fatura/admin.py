from django.contrib import admin
from .models import Fatura, FaturaKalem


class FaturaKalemInline(admin.TabularInline):
    model = FaturaKalem
    extra = 1
    fields = ('urun', 'urun_adi', 'miktar', 'birim_fiyat', 'kdv_orani', 'kdv_tutari', 'toplam_tutar', 'sira_no')


@admin.register(Fatura)
class FaturaAdmin(admin.ModelAdmin):
    list_display = ['fatura_no', 'cari', 'fatura_tarihi', 'genel_toplam', 'fatura_tipi', 'durum']
    list_filter = ['fatura_tipi', 'durum', 'fatura_tarihi']
    search_fields = ['fatura_no', 'cari__ad_soyad']
    list_editable = ['durum']
    readonly_fields = ['olusturma_tarihi', 'guncelleme_tarihi']
    inlines = [FaturaKalemInline]
    fieldsets = (
        ('Fatura Bilgileri', {
            'fields': ('fatura_no', 'fatura_tarihi', 'cari', 'fatura_tipi', 'durum')
        }),
        ('Tutar Bilgileri', {
            'fields': ('toplam_tutar', 'kdv_tutari', 'genel_toplam')
        }),
        ('Diğer', {
            'fields': ('aciklama',)
        }),
        ('Tarihler', {
            'fields': ('olusturma_tarihi', 'guncelleme_tarihi'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FaturaKalem)
class FaturaKalemAdmin(admin.ModelAdmin):
    list_display = ['fatura', 'urun_adi', 'miktar', 'birim_fiyat', 'toplam_tutar', 'sira_no']
    list_filter = ['fatura__fatura_tarihi']
    search_fields = ['urun_adi', 'fatura__fatura_no']
    readonly_fields = []

