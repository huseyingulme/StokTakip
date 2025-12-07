from django.contrib import admin
from .models import ButceKategori, Butce


@admin.register(ButceKategori)
class ButceKategoriAdmin(admin.ModelAdmin):
    list_display = ['ad', 'olusturma_tarihi']
    search_fields = ['ad', 'aciklama']
    readonly_fields = ['olusturma_tarihi']


@admin.register(Butce)
class ButceAdmin(admin.ModelAdmin):
    list_display = ['baslik', 'kategori', 'donem', 'baslangic_tarihi', 'bitis_tarihi', 'butce_tutari', 'kalan_butce', 'olusturan']
    list_filter = ['kategori', 'donem', 'baslangic_tarihi']
    search_fields = ['baslik', 'aciklama']
    readonly_fields = ['olusturma_tarihi', 'guncelleme_tarihi', 'kalan_butce']
    date_hierarchy = 'baslangic_tarihi'
    fieldsets = (
        ('Bütçe Bilgileri', {
            'fields': ('baslik', 'kategori', 'donem', 'baslangic_tarihi', 'bitis_tarihi', 'butce_tutari')
        }),
        ('Diğer', {
            'fields': ('aciklama', 'kalan_butce', 'olusturan', 'olusturma_tarihi', 'guncelleme_tarihi')
        }),
    )
