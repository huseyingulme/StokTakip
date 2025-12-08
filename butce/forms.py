from django import forms
from .models import ButceKategori, Butce


class ButceKategoriForm(forms.ModelForm):
    class Meta:
        model = ButceKategori
        fields = ['ad', 'aciklama']
        widgets = {
            'ad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kategori adı'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Açıklama'}),
        }
        labels = {
            'ad': 'Kategori Adı',
            'aciklama': 'Açıklama',
        }


class ButceForm(forms.ModelForm):
    class Meta:
        model = Butce
        fields = ['baslik', 'kategori', 'donem', 'baslangic_tarihi', 'bitis_tarihi', 'butce_tutari', 'aciklama']
        widgets = {
            'baslik': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bütçe başlığı'}),
            'kategori': forms.Select(attrs={'class': 'form-control'}),
            'donem': forms.Select(attrs={'class': 'form-control'}),
            'baslangic_tarihi': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'bitis_tarihi': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'butce_tutari': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Açıklama'}),
        }
        labels = {
            'baslik': 'Başlık',
            'kategori': 'Kategori',
            'donem': 'Dönem',
            'baslangic_tarihi': 'Başlangıç Tarihi',
            'bitis_tarihi': 'Bitiş Tarihi',
            'butce_tutari': 'Bütçe Tutarı (₺)',
            'aciklama': 'Açıklama',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        baslangic_tarihi = cleaned_data.get('baslangic_tarihi')
        bitis_tarihi = cleaned_data.get('bitis_tarihi')
        
        if baslangic_tarihi and bitis_tarihi:
            if bitis_tarihi < baslangic_tarihi:
                raise forms.ValidationError('Bitiş tarihi başlangıç tarihinden önce olamaz.')
        
        return cleaned_data

