from django import forms
from .models import Fatura, FaturaKalem
from cari.models import Cari
from stok.models import Urun


class FaturaForm(forms.ModelForm):
    class Meta:
        model = Fatura
        fields = ['fatura_no', 'cari', 'fatura_tarihi', 'vade_tarihi', 'fatura_tipi', 'durum', 'aciklama']
        widgets = {
            'fatura_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'FAT-2024-001'}),
            'cari': forms.Select(attrs={'class': 'form-control'}),
            'fatura_tarihi': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'vade_tarihi': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fatura_tipi': forms.Select(attrs={'class': 'form-control'}),
            'durum': forms.Select(attrs={'class': 'form-control'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'fatura_no': 'Fatura No',
            'cari': 'Cari',
            'fatura_tarihi': 'Fatura Tarihi',
            'vade_tarihi': 'Vade Tarihi',
            'fatura_tipi': 'Fatura Tipi',
            'durum': 'Durum',
            'aciklama': 'Açıklama',
        }


class FaturaKalemForm(forms.ModelForm):
    class Meta:
        model = FaturaKalem
        fields = ['urun', 'urun_adi', 'miktar', 'birim_fiyat', 'kdv_orani']
        widgets = {
            'urun': forms.Select(attrs={'class': 'form-control'}),
            'urun_adi': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ürün adı'}),
            'miktar': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'birim_fiyat': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'kdv_orani': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'}),
        }
        labels = {
            'urun': 'Ürün',
            'urun_adi': 'Ürün Adı',
            'miktar': 'Miktar',
            'birim_fiyat': 'Birim Fiyat (₺)',
            'kdv_orani': 'KDV Oranı (%)',
        }

