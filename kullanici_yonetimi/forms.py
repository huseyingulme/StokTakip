from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class KullaniciForm(forms.ModelForm):
    password = forms.CharField(
        label='Şifre',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text='Şifre değiştirmek için yeni şifre girin. Boş bırakırsanız şifre değişmez.'
    )
    password_confirm = forms.CharField(
        label='Şifre (Tekrar)',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff', 'is_superuser']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'username': 'Kullanıcı Adı',
            'first_name': 'Ad',
            'last_name': 'Soyad',
            'email': 'E-posta',
            'is_active': 'Aktif',
            'is_staff': 'Personel',
            'is_superuser': 'Müdür (Süper Kullanıcı)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Düzenleme modunda şifre zorunlu değil
            self.fields['password'].required = False
            self.fields['password_confirm'].required = False
            self.fields['password'].help_text = 'Şifre değiştirmek için yeni şifre girin. Boş bırakırsanız şifre değişmez.'
        else:
            # Yeni kullanıcı için şifre zorunlu
            self.fields['password'].required = True
            self.fields['password_confirm'].required = True
            self.fields['password'].help_text = 'Şifre en az 8 karakter olmalıdır.'

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise ValidationError('Şifreler eşleşmiyor.')
        
        return password_confirm
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        # Yeni kullanıcı için şifre kontrolü
        if not self.instance.pk:
            if not password:
                self.add_error('password', 'Yeni kullanıcı için şifre zorunludur.')
            elif len(password) < 8:
                self.add_error('password', 'Şifre en az 8 karakter olmalıdır.')

        # Düzenleme modunda şifre değiştiriliyorsa kontrol et
        if self.instance.pk and password:
            if len(password) < 8:
                self.add_error('password', 'Şifre en az 8 karakter olmalıdır.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        
        if password:
            user.set_password(password)
        
        if commit:
            user.save()
        return user

