from django import forms
from cari.models import Cari
from django.contrib.auth.models import User

class MusteriProfilForm(forms.ModelForm):
    email = forms.EmailField(label="E-posta Adresi", required=True)
    telefon = forms.CharField(label="Telefon", max_length=20, required=False)

    class Meta:
        model = Cari
        fields = ['telefon']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['email'].initial = self.user.email
            self.fields['email'].widget.attrs.update({'class': 'form-control'})
            self.fields['telefon'].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        cari = super().save(commit=False)
        if commit:
            cari.save()
            if self.user:
                self.user.email = self.cleaned_data['email']
                self.user.save()
        return cari
