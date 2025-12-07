from django import forms
from .models import Kategori, Urun, StokHareketi


class KategoriForm(forms.ModelForm):
    class Meta:
        model = Kategori
        fields = ['ad', 'aciklama']
        widgets = {
            'ad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kategori adı giriniz'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Kategori açıklaması'}),
        }
        labels = {
            'ad': 'Kategori Adı',
            'aciklama': 'Açıklama',
        }


class UrunForm(forms.ModelForm):
    class Meta:
        model = Urun
        fields = ['ad', 'kategori', 'barkod', 'fiyat', 'stok_adedi', 'birim', 'aciklama']
        widgets = {
            'ad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ürün adı giriniz'}),
            'kategori': forms.Select(attrs={'class': 'form-control'}),
            'barkod': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Barkod numarası'}),
            'fiyat': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'stok_adedi': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'birim': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Adet, Kg, Lt vb.'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ürün açıklaması'}),
        }
        labels = {
            'ad': 'Ürün Adı',
            'kategori': 'Kategori',
            'barkod': 'Barkod',
            'fiyat': 'Birim Fiyatı (₺)',
            'stok_adedi': 'Stok Miktarı',
            'birim': 'Birim',
            'aciklama': 'Açıklama',
        }


class StokHareketiForm(forms.ModelForm):
    class Meta:
        model = StokHareketi
        fields = ['urun', 'hareket_tipi', 'miktar', 'aciklama']
        widgets = {
            'urun': forms.Select(attrs={'class': 'form-control'}),
            'hareket_tipi': forms.Select(attrs={'class': 'form-control'}),
            'miktar': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Açıklama'}),
        }
        labels = {
            'urun': 'Ürün',
            'hareket_tipi': 'İşlem Tipi',
            'miktar': 'Miktar',
            'aciklama': 'Açıklama',
        }

