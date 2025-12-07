from django import forms
from .models import Cari, CariHareketi, CariNotu, TahsilatMakbuzu, TediyeMakbuzu


class CariForm(forms.ModelForm):
    class Meta:
        model = Cari
        fields = ['ad_soyad', 'vergi_dairesi', 'vergi_no', 'tc_vkn', 'telefon', 'email', 
                  'adres', 'sehir', 'ilce', 'kategori', 'durum', 'risk_limiti']
        widgets = {
            'ad_soyad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ad Soyad / Firma Adı'}),
            'vergi_dairesi': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vergi Dairesi'}),
            'vergi_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Vergi Numarası'}),
            'tc_vkn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'TCKN / VKN'}),
            'telefon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '05XX XXX XX XX'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ornek@email.com'}),
            'adres': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Adres bilgisi'}),
            'sehir': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Şehir'}),
            'ilce': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'İlçe'}),
            'kategori': forms.Select(attrs={'class': 'form-control'}),
            'durum': forms.Select(attrs={'class': 'form-control'}),
            'risk_limiti': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }
        labels = {
            'ad_soyad': 'Ad Soyad / Firma Adı',
            'vergi_dairesi': 'Vergi Dairesi',
            'vergi_no': 'Vergi Numarası',
            'tc_vkn': 'TCKN / VKN',
            'telefon': 'Telefon',
            'email': 'E-posta',
            'adres': 'Adres',
            'sehir': 'Şehir',
            'ilce': 'İlçe',
            'kategori': 'Kategori',
            'durum': 'Durum',
            'risk_limiti': 'Risk Limiti (₺)',
        }


class CariHareketiForm(forms.ModelForm):
    class Meta:
        model = CariHareketi
        fields = ['cari', 'hareket_turu', 'tutar', 'aciklama', 'belge_no', 'tarih', 'odeme_yontemi']
        widgets = {
            'cari': forms.Select(attrs={'class': 'form-control'}),
            'hareket_turu': forms.Select(attrs={'class': 'form-control'}),
            'tutar': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Açıklama'}),
            'belge_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Fatura No / Dekont No'}),
            'tarih': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'odeme_yontemi': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'cari': 'Cari',
            'hareket_turu': 'Hareket Türü',
            'tutar': 'Tutar (₺)',
            'aciklama': 'Açıklama',
            'belge_no': 'Belge Numarası',
            'tarih': 'Tarih',
            'odeme_yontemi': 'Ödeme Yöntemi',
        }


class CariNotuForm(forms.ModelForm):
    class Meta:
        model = CariNotu
        fields = ['baslik', 'icerik']
        widgets = {
            'baslik': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Not başlığı'}),
            'icerik': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Not içeriği'}),
        }
        labels = {
            'baslik': 'Başlık',
            'icerik': 'İçerik',
        }


class TahsilatMakbuzuForm(forms.ModelForm):
    class Meta:
        model = TahsilatMakbuzu
        fields = ['makbuz_no', 'cari', 'tutar', 'odeme_yontemi', 'tarih', 'aciklama', 'dekont_no']
        widgets = {
            'makbuz_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'TAH-2024-001'}),
            'cari': forms.Select(attrs={'class': 'form-control'}),
            'tutar': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'odeme_yontemi': forms.Select(attrs={'class': 'form-control'}),
            'tarih': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Açıklama'}),
            'dekont_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dekont numarası'}),
        }
        labels = {
            'makbuz_no': 'Makbuz No',
            'cari': 'Cari',
            'tutar': 'Tutar (₺)',
            'odeme_yontemi': 'Ödeme Yöntemi',
            'tarih': 'Tarih',
            'aciklama': 'Açıklama',
            'dekont_no': 'Dekont No',
        }


class TediyeMakbuzuForm(forms.ModelForm):
    class Meta:
        model = TediyeMakbuzu
        fields = ['makbuz_no', 'cari', 'tutar', 'odeme_yontemi', 'tarih', 'aciklama', 'dekont_no']
        widgets = {
            'makbuz_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'TED-2024-001'}),
            'cari': forms.Select(attrs={'class': 'form-control'}),
            'tutar': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'odeme_yontemi': forms.Select(attrs={'class': 'form-control'}),
            'tarih': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Açıklama'}),
            'dekont_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dekont numarası'}),
        }
        labels = {
            'makbuz_no': 'Makbuz No',
            'cari': 'Cari',
            'tutar': 'Tutar (₺)',
            'odeme_yontemi': 'Ödeme Yöntemi',
            'tarih': 'Tarih',
            'aciklama': 'Açıklama',
            'dekont_no': 'Dekont No',
        }
