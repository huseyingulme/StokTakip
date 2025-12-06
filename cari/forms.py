from django import forms
from .models import Musteri


class MusteriForm(forms.ModelForm):
    class Meta:
        model = Musteri
        fields = ['ad_soyad', 'unvan', 'tc_vkn', 'telefon', 'email', 'adres', 'sehir', 'tip', 'bakiye']
        widgets = {
            'ad_soyad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ad Soyad'}),
            'unvan': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Şirket Ünvanı'}),
            'tc_vkn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'TC Kimlik No / Vergi No'}),
            'telefon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '05XX XXX XX XX'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ornek@email.com'}),
            'adres': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Adres bilgisi'}),
            'sehir': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Şehir'}),
            'tip': forms.Select(attrs={'class': 'form-control'}),
            'bakiye': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        labels = {
            'ad_soyad': 'Ad Soyad / Firma Adı',
            'unvan': 'Ünvan',
            'tc_vkn': 'TC / Vergi No',
            'telefon': 'Telefon',
            'email': 'E-posta',
            'adres': 'Adres',
            'sehir': 'Şehir',
            'tip': 'Tip',
            'bakiye': 'Bakiye (₺)',
        }

