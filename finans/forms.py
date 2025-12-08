from django import forms
from .models import HesapKart, FinansHareketi


class HesapKartForm(forms.ModelForm):
    class Meta:
        model = HesapKart
        fields = ['ad', 'hesap_tipi', 'hesap_no', 'bakiye', 'aciklama', 'durum']
        widgets = {
            'ad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Hesap adı'}),
            'hesap_tipi': forms.Select(attrs={'class': 'form-control'}),
            'hesap_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Hesap numarası'}),
            'bakiye': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Açıklama'}),
            'durum': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'ad': 'Hesap Adı',
            'hesap_tipi': 'Hesap Tipi',
            'hesap_no': 'Hesap No',
            'bakiye': 'Başlangıç Bakiyesi (₺)',
            'aciklama': 'Açıklama',
            'durum': 'Aktif',
        }


class FinansHareketiForm(forms.ModelForm):
    class Meta:
        model = FinansHareketi
        fields = ['hareket_no', 'hesap', 'hedef_hesap', 'hareket_tipi', 'tutar', 'aciklama', 'tarih', 'belge_no']
        widgets = {
            'hareket_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'FIN-2024-001'}),
            'hesap': forms.Select(attrs={'class': 'form-control'}),
            'hedef_hesap': forms.Select(attrs={'class': 'form-control'}),
            'hareket_tipi': forms.Select(attrs={'class': 'form-control'}),
            'tutar': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Açıklama'}),
            'tarih': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'belge_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Belge numarası'}),
        }
        labels = {
            'hareket_no': 'Hareket No',
            'hesap': 'Hesap',
            'hedef_hesap': 'Hedef Hesap (Transfer için)',
            'hareket_tipi': 'Hareket Tipi',
            'tutar': 'Tutar (₺)',
            'aciklama': 'Açıklama',
            'tarih': 'Tarih',
            'belge_no': 'Belge No',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['hesap'].queryset = HesapKart.objects.filter(durum=True)
        self.fields['hedef_hesap'].queryset = HesapKart.objects.filter(durum=True)
        self.fields['hedef_hesap'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        hareket_tipi = cleaned_data.get('hareket_tipi')
        hedef_hesap = cleaned_data.get('hedef_hesap')
        hesap = cleaned_data.get('hesap')
        
        if hareket_tipi == 'transfer' and not hedef_hesap:
            raise forms.ValidationError('Transfer işlemi için hedef hesap seçilmelidir.')
        
        if hareket_tipi == 'transfer' and hesap == hedef_hesap:
            raise forms.ValidationError('Kaynak ve hedef hesap aynı olamaz.')
        
        return cleaned_data

