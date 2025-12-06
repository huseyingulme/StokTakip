from django import forms
from .models import Urun


class UrunForm(forms.ModelForm):
    class Meta:
        model = Urun
        fields = ['ad', 'barkod', 'fiyat', 'stok_adedi', 'birim', 'aciklama']
        widgets = {
            'ad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ürün adı giriniz'}),
            'barkod': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Barkod numarası'}),
            'fiyat': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'stok_adedi': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'birim': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Adet, Kg, Lt vb.'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ürün açıklaması'}),
        }
        labels = {
            'ad': 'Ürün Adı',
            'barkod': 'Barkod',
            'fiyat': 'Fiyat (₺)',
            'stok_adedi': 'Stok Adedi',
            'birim': 'Birim',
            'aciklama': 'Açıklama',
        }

