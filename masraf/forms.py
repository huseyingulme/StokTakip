from django import forms
from .models import MasrafKategori, Masraf


class MasrafKategoriForm(forms.ModelForm):
    class Meta:
        model = MasrafKategori
        fields = ['ad', 'aciklama']
        widgets = {
            'ad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kategori adı'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Açıklama'}),
        }
        labels = {
            'ad': 'Kategori Adı',
            'aciklama': 'Açıklama',
        }


class MasrafForm(forms.ModelForm):
    class Meta:
        model = Masraf
        fields = ['masraf_no', 'kategori', 'aciklama', 'tutar', 'tarih', 'odeme_yontemi', 'durum', 'belge_no']
        widgets = {
            'masraf_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'MAS-2024-001'}),
            'kategori': forms.Select(attrs={'class': 'form-control'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Masraf açıklaması'}),
            'tutar': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'tarih': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'odeme_yontemi': forms.Select(attrs={'class': 'form-control'}),
            'durum': forms.Select(attrs={'class': 'form-control'}),
            'belge_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Belge numarası'}),
        }
        labels = {
            'masraf_no': 'Masraf No',
            'kategori': 'Kategori',
            'aciklama': 'Açıklama',
            'tutar': 'Tutar (₺)',
            'tarih': 'Tarih',
            'odeme_yontemi': 'Ödeme Yöntemi',
            'durum': 'Durum',
            'belge_no': 'Belge No',
        }

