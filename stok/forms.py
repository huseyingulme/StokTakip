from django import forms
from django.core.exceptions import ValidationError
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
        fields = ['ad', 'kategori', 'barkod', 'birim', 'alis_fiyati', 'fiyat']
        widgets = {
            'ad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ürün adı giriniz'}),
            'kategori': forms.Select(attrs={'class': 'form-control'}),
            'barkod': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Barkod numarası'}),
            'birim': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Adet, Kg, Lt vb.'}),
            'alis_fiyati': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'fiyat': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
        }
        labels = {
            'ad': 'Ürün Adı',
            'kategori': 'Kategori',
            'barkod': 'Barkod',
            'birim': 'Birim',
            'alis_fiyati': 'Alış Fiyatı (₺)',
            'fiyat': 'Satış Fiyatı (₺)',
        }
    
    def clean(self):
        """Custom validation for UrunForm."""
        cleaned_data = super().clean()
        errors = {}
        
        # Alış fiyatı kontrolü
        alis_fiyati = cleaned_data.get('alis_fiyati')
        if alis_fiyati is not None and alis_fiyati < 0:
            errors['alis_fiyati'] = 'Alış fiyatı negatif olamaz.'
        
        # Satış fiyatı kontrolü
        fiyat = cleaned_data.get('fiyat')
        if fiyat is not None and fiyat < 0:
            errors['fiyat'] = 'Satış fiyatı negatif olamaz.'
        
        # Barkod unique kontrolü
        barkod = cleaned_data.get('barkod')
        if barkod:
            existing = Urun.objects.filter(barkod=barkod)
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                errors['barkod'] = 'Bu barkod numarası zaten kullanılıyor.'
        
        if errors:
            raise ValidationError(errors)
        
        return cleaned_data


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

