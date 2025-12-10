from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from decimal import Decimal
from .models import Fatura, FaturaKalem
from cari.models import Cari
from stok.models import Urun


class FaturaForm(forms.ModelForm):
    class Meta:
        model = Fatura
        fields = ['cari', 'fatura_tarihi', 'fatura_tipi', 'durum', 'iskonto_orani']
        widgets = {
            'cari': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'fatura_tarihi': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fatura_tipi': forms.Select(attrs={'class': 'form-control'}),
            'durum': forms.Select(attrs={'class': 'form-control'}),
            'iskonto_orani': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100', 'value': '0', 'id': 'id_iskonto_orani'}),
        }
        labels = {
            'cari': 'Cari',
            'fatura_tarihi': 'Fatura Tarihi',
            'fatura_tipi': 'Fatura Tipi',
            'durum': 'Durum',
            'iskonto_orani': 'İskonto Oranı (%)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        bugun = timezone.now().date()
        
        if not self.instance.pk:
            self.fields['fatura_tarihi'].initial = bugun
        else:
            if self.instance.fatura_no:
                self.fields['fatura_no'] = forms.CharField(
                    required=False,
                    widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
                    label='Fatura No',
                    initial=self.instance.fatura_no
                )
        
        fatura_tipi = None
        if self.initial:
            fatura_tipi = self.initial.get('fatura_tipi')
        elif self.data:
            fatura_tipi = self.data.get('fatura_tipi')
        elif self.instance and self.instance.pk:
            fatura_tipi = self.instance.fatura_tipi
        
        if fatura_tipi == 'Satis':
            self.fields['cari'].queryset = Cari.objects.filter(durum='aktif', kategori__in=['musteri', 'her_ikisi'])
            self.fields['cari'].required = True
        elif fatura_tipi == 'Alis':
            self.fields['cari'].queryset = Cari.objects.filter(durum='aktif', kategori__in=['tedarikci', 'her_ikisi'])
            self.fields['cari'].required = True
        else:
            self.fields['cari'].queryset = Cari.objects.filter(durum='aktif')
            self.fields['cari'].required = True
    
    def clean(self):
        """Custom validation for FaturaForm."""
        cleaned_data = super().clean()
        errors = {}
        
        # İskonto oranı > 100 kontrolü
        iskonto_orani = cleaned_data.get('iskonto_orani')
        if iskonto_orani is not None:
            if iskonto_orani < 0:
                errors['iskonto_orani'] = 'İskonto oranı negatif olamaz.'
            elif iskonto_orani > 100:
                errors['iskonto_orani'] = 'İskonto oranı 100\'den büyük olamaz.'
        
        # Cari kategori kontrolü (form'da var ama clean'de de kontrol)
        cari = cleaned_data.get('cari')
        fatura_tipi = cleaned_data.get('fatura_tipi')
        if cari and fatura_tipi:
            if fatura_tipi == 'Satis' and cari.kategori not in ['musteri', 'her_ikisi']:
                errors['cari'] = 'Satış faturası için müşteri seçilmelidir.'
            elif fatura_tipi == 'Alis' and cari.kategori not in ['tedarikci', 'her_ikisi']:
                errors['cari'] = 'Alış faturası için tedarikçi seçilmelidir.'
        
        if errors:
            raise ValidationError(errors)
        
        return cleaned_data


class FaturaKalemForm(forms.ModelForm):
    kdv_dahil_fiyat = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'id': 'id_kdv_dahil_fiyat'}),
        label='KDV Dahil Fiyat (₺)'
    )
    
    class Meta:
        model = FaturaKalem
        fields = ['urun', 'urun_adi', 'miktar', 'birim_fiyat', 'kdv_orani']
        widgets = {
            'urun': forms.Select(attrs={'class': 'form-control urun-select'}),
            'urun_adi': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ürün adı', 'readonly': True}),
            'miktar': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'value': '1', 'id': 'id_miktar'}),
            'birim_fiyat': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'id': 'id_birim_fiyat'}),
            'kdv_orani': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100', 'value': '20', 'id': 'id_kdv_orani'}),
        }
        labels = {
            'urun': 'Ürün',
            'urun_adi': 'Ürün Adı',
            'miktar': 'Miktar',
            'birim_fiyat': 'KDV Hariç Birim Fiyat (₺)',
            'kdv_orani': 'KDV Oranı (%)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ürün queryset'ini düzgün şekilde ayarla
        self.fields['urun'].queryset = Urun.objects.all().order_by('ad')
        self.fields['urun'].required = False
        # Empty label ekle
        self.fields['urun'].empty_label = 'Seçiniz'
    
    def clean(self):
        """Custom validation for FaturaKalemForm."""
        cleaned_data = super().clean()
        errors = {}
        
        # Miktar kontrolü
        miktar = cleaned_data.get('miktar')
        if miktar is not None and miktar <= 0:
            errors['miktar'] = 'Miktar 0\'dan büyük olmalıdır.'
        
        # Birim fiyat kontrolü
        birim_fiyat = cleaned_data.get('birim_fiyat')
        if birim_fiyat is not None and birim_fiyat < 0:
            errors['birim_fiyat'] = 'Birim fiyat negatif olamaz.'
        
        # KDV oranı kontrolü
        kdv_orani = cleaned_data.get('kdv_orani')
        if kdv_orani is not None:
            if kdv_orani < 0 or kdv_orani > 100:
                errors['kdv_orani'] = 'KDV oranı 0 ile 100 arasında olmalıdır.'
        
        if errors:
            raise ValidationError(errors)
        
        return cleaned_data

