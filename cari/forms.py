from django import forms
from django.core.exceptions import ValidationError
import re
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
    
    def clean(self):
        """Custom validation for CariForm."""
        cleaned_data = super().clean()
        errors = {}
        
        # TC/VKN format validation
        tc_vkn = cleaned_data.get('tc_vkn')
        if tc_vkn:
            tc_vkn_clean = tc_vkn.replace('-', '').replace(' ', '')
            if not (len(tc_vkn_clean) == 11 or len(tc_vkn_clean) == 10):
                errors['tc_vkn'] = 'TC/VKN 11 (TC) veya 10 (VKN) karakter olmalıdır.'
            elif not tc_vkn_clean.isdigit():
                errors['tc_vkn'] = 'TC/VKN sadece rakam içermelidir.'
        
        # Vergi no format validation
        vergi_no = cleaned_data.get('vergi_no')
        if vergi_no:
            vergi_no_clean = vergi_no.replace('-', '').replace(' ', '')
            if not vergi_no_clean.isdigit():
                errors['vergi_no'] = 'Vergi numarası sadece rakam içermelidir.'
        
        # Telefon format validation (Türkiye telefon formatı)
        telefon = cleaned_data.get('telefon')
        if telefon:
            telefon_clean = telefon.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if not telefon_clean.startswith('0') or len(telefon_clean) != 11:
                errors['telefon'] = 'Geçerli bir Türkiye telefon numarası giriniz (05XX XXX XX XX).'
            elif not telefon_clean.isdigit():
                errors['telefon'] = 'Telefon numarası sadece rakam içermelidir.'
        
        # Risk limiti kontrolü
        risk_limiti = cleaned_data.get('risk_limiti')
        if risk_limiti is not None and risk_limiti < 0:
            errors['risk_limiti'] = 'Risk limiti negatif olamaz.'
        
        if errors:
            raise ValidationError(errors)
        
        return cleaned_data


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
