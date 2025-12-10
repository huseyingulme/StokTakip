from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
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
    
    def clean(self):
        """Custom validation for MasrafForm."""
        cleaned_data = super().clean()
        errors = {}
        
        # Tutar kontrolü
        tutar = cleaned_data.get('tutar')
        if tutar is not None and tutar < 0:
            errors['tutar'] = 'Tutar negatif olamaz.'
        
        # Tarih gelecek tarih kontrolü
        tarih = cleaned_data.get('tarih')
        if tarih and tarih > timezone.now().date():
            errors['tarih'] = 'Gelecek tarih seçilemez.'
        
        if errors:
            raise ValidationError(errors)
        
        return cleaned_data

