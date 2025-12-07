from django.contrib import admin
from django.utils.html import format_html
from .models import Cari, CariHareketi, CariNotu, TahsilatMakbuzu, TediyeMakbuzu


@admin.register(Cari)
class CariAdmin(admin.ModelAdmin):
    list_display = ['ad_soyad', 'kategori', 'durum', 'telefon', 'email', 'bakiye_renkli', 'risk_limiti', 'son_islem_tarihi']
    list_filter = ['kategori', 'durum', 'sehir', 'olusturma_tarihi']
    search_fields = ['ad_soyad', 'vergi_no', 'tc_vkn', 'telefon', 'email']
    list_editable = ['durum', 'risk_limiti']
    readonly_fields = ['olusturma_tarihi', 'guncelleme_tarihi', 'bakiye', 'risk_asimi_var_mi', 'son_islem_tarihi']
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('ad_soyad', 'kategori', 'durum')
        }),
        ('Vergi Bilgileri', {
            'fields': ('vergi_dairesi', 'vergi_no', 'tc_vkn')
        }),
        ('İletişim Bilgileri', {
            'fields': ('telefon', 'email', 'adres', 'sehir', 'ilce')
        }),
        ('Mali Bilgiler', {
            'fields': ('risk_limiti', 'bakiye', 'risk_asimi_var_mi', 'son_islem_tarihi')
        }),
        ('Tarihler', {
            'fields': ('olusturma_tarihi', 'guncelleme_tarihi'),
            'classes': ('collapse',)
        }),
    )

    def bakiye_renkli(self, obj):
        bakiye = obj.bakiye
        if bakiye > 0:
            color = 'red'
            text = f'{bakiye:,.2f} ₺ (Borç)'
        elif bakiye < 0:
            color = 'green'
            text = f'{abs(bakiye):,.2f} ₺ (Alacak)'
        else:
            color = 'black'
            text = '0.00 ₺'
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, text)
    bakiye_renkli.short_description = 'Bakiye'


@admin.register(CariHareketi)
class CariHareketiAdmin(admin.ModelAdmin):
    list_display = ['cari', 'hareket_turu', 'tutar', 'belge_no', 'tarih', 'odeme_yontemi', 'olusturan']
    list_filter = ['hareket_turu', 'odeme_yontemi', 'tarih']
    search_fields = ['cari__ad_soyad', 'belge_no', 'aciklama']
    readonly_fields = ['olusturma_tarihi']
    date_hierarchy = 'tarih'
    fieldsets = (
        ('Hareket Bilgileri', {
            'fields': ('cari', 'hareket_turu', 'tutar', 'tarih', 'belge_no')
        }),
        ('Ödeme Bilgileri', {
            'fields': ('odeme_yontemi', 'aciklama')
        }),
        ('Sistem', {
            'fields': ('olusturan', 'olusturma_tarihi'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CariNotu)
class CariNotuAdmin(admin.ModelAdmin):
    list_display = ['cari', 'baslik', 'olusturan', 'olusturma_tarihi']
    list_filter = ['olusturma_tarihi']
    search_fields = ['cari__ad_soyad', 'baslik', 'icerik']
    readonly_fields = ['olusturma_tarihi', 'guncelleme_tarihi']
    fieldsets = (
        ('Not Bilgileri', {
            'fields': ('cari', 'baslik', 'icerik')
        }),
        ('Sistem', {
            'fields': ('olusturan', 'olusturma_tarihi', 'guncelleme_tarihi'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TahsilatMakbuzu)
class TahsilatMakbuzuAdmin(admin.ModelAdmin):
    list_display = ['makbuz_no', 'cari', 'tutar', 'odeme_yontemi', 'tarih', 'olusturan']
    list_filter = ['odeme_yontemi', 'tarih']
    search_fields = ['makbuz_no', 'cari__ad_soyad', 'dekont_no']
    readonly_fields = ['olusturma_tarihi']
    date_hierarchy = 'tarih'
    fieldsets = (
        ('Makbuz Bilgileri', {
            'fields': ('makbuz_no', 'cari', 'tutar', 'tarih', 'odeme_yontemi')
        }),
        ('Diğer', {
            'fields': ('aciklama', 'dekont_no', 'olusturan', 'olusturma_tarihi')
        }),
    )


@admin.register(TediyeMakbuzu)
class TediyeMakbuzuAdmin(admin.ModelAdmin):
    list_display = ['makbuz_no', 'cari', 'tutar', 'odeme_yontemi', 'tarih', 'olusturan']
    list_filter = ['odeme_yontemi', 'tarih']
    search_fields = ['makbuz_no', 'cari__ad_soyad', 'dekont_no']
    readonly_fields = ['olusturma_tarihi']
    date_hierarchy = 'tarih'
    fieldsets = (
        ('Makbuz Bilgileri', {
            'fields': ('makbuz_no', 'cari', 'tutar', 'tarih', 'odeme_yontemi')
        }),
        ('Diğer', {
            'fields': ('aciklama', 'dekont_no', 'olusturan', 'olusturma_tarihi')
        }),
    )
