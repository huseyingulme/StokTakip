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
        fields = ['ad', 'kategori', 'barkod', 'birim', 'fiyat']
        widgets = {
            'ad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ürün adı giriniz'}),
            'kategori': forms.Select(attrs={'class': 'form-control'}),
            'barkod': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Barkod numarası'}),
            'birim': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Adet, Kg, Lt vb.'}),
            'fiyat': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }
        labels = {
            'ad': 'Ürün Adı',
            'kategori': 'Kategori',
            'barkod': 'Barkod',
            'birim': 'Birim',
            'fiyat': 'Satış Fiyatı (₺)',
        }


class StokHareketiForm(forms.ModelForm):
    class Meta:
        model = StokHareketi
        fields = ['urun', 'islem_turu', 'miktar', 'aciklama']
        widgets = {
            'urun': forms.Select(attrs={'class': 'form-control'}),
            'islem_turu': forms.Select(attrs={'class': 'form-control'}),
            'miktar': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Açıklama'}),
        }
        labels = {
            'urun': 'Ürün',
            'islem_turu': 'İşlem Türü',
            'miktar': 'Miktar',
            'aciklama': 'Açıklama',
        }

