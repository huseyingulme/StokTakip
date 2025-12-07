# 🔐 Kullanıcı Giriş Sistemi

StokTakip projesinde kullanıcı giriş ve kayıt sistemi başarıyla yapılandırılmıştır.

## ✅ Özellikler

- ✅ Kullanıcı Girişi (Login)
- ✅ Kullanıcı Kaydı (Register)
- ✅ Kullanıcı Çıkışı (Logout)
- ✅ Güvenli form işlemleri
- ✅ Modern ve kullanıcı dostu arayüz
- ✅ Hata mesajları ve validasyon

## 📍 Erişim URL'leri

- **Giriş Sayfası:** http://127.0.0.1:8000/accounts/login/
- **Kayıt Sayfası:** http://127.0.0.1:8000/accounts/register/
- **Çıkış:** http://127.0.0.1:8000/accounts/logout/

## 🚀 Kullanım

### 1. İlk Admin Kullanıcısı Oluşturma

Terminal'de şu komutu çalıştırın:

```bash
python manage.py createsuperuser
```

Sistem şunları soracak:
- **Username:** (Kullanıcı adı girin, örn: admin)
- **Email address:** (E-posta girin - isteğe bağlı)
- **Password:** (Güvenli bir şifre girin)
- **Password (again):** (Şifreyi tekrar girin)

**Örnek:**
```
Username: admin
Email address: admin@example.com
Password: ********
Password (again): ********
```

### 2. Normal Kullanıcı Kaydı

Tarayıcıda:
1. http://127.0.0.1:8000/accounts/register/ adresine gidin
2. Kullanıcı adı girin
3. Şifre girin (en az 8 karakter)
4. Şifreyi tekrar girin
5. "Kayıt Ol" butonuna tıklayın

### 3. Giriş Yapma

Tarayıcıda:
1. http://127.0.0.1:8000/accounts/login/ adresine gidin
2. Kullanıcı adı ve şifre girin
3. "Giriş Yap" butonuna tıklayın

## 🔒 Güvenlik Ayarları

Proje ayarları (`stoktakip/settings.py`):

```python
LOGIN_URL = 'login'                    # Giriş sayfası URL'i
LOGIN_REDIRECT_URL = '/'               # Giriş sonrası yönlendirme
LOGOUT_REDIRECT_URL = '/'              # Çıkış sonrası yönlendirme
```

## 📝 Kullanıcı Yönetimi

### Django Admin Paneli

Admin kullanıcıları için:
- URL: http://127.0.0.1:8000/admin/
- Admin paneline sadece superuser olan kullanıcılar erişebilir

### Normal Kullanıcılar

- Normal kullanıcılar kayıt olabilir
- Sisteme giriş yapabilir
- Stok, cari, fatura modüllerini kullanabilir
- Admin paneline erişemezler

## 🎨 Arayüz Özellikleri

- Modern Bootstrap 5 tasarımı
- Responsive (mobil uyumlu)
- Gradient arka plan
- İkon desteği (Bootstrap Icons)
- Hata mesajları ve validasyon
- Kullanıcı dostu formlar

## ⚙️ Teknik Detaylar

### Kullanılan Django Özellikleri

- `django.contrib.auth.views.LoginView` - Giriş görünümü
- `django.contrib.auth.views.LogoutView` - Çıkış görünümü
- `django.contrib.auth.forms.UserCreationForm` - Kayıt formu
- Django'nun varsayılan User modeli

### Dosya Yapısı

```
templates/
├── registration/
│   ├── login.html      # Giriş sayfası
│   └── register.html   # Kayıt sayfası
accounts/
├── views.py            # Register view
└── urls.py             # URL yapılandırması
stoktakip/
└── urls.py             # Ana URL yapılandırması
```

## 🐛 Sorun Giderme

### "Kullanıcı adı veya şifre hatalı" Hatası

- Kullanıcı adını ve şifreyi kontrol edin
- Büyük/küçük harf duyarlılığına dikkat edin
- Kullanıcının mevcut olduğundan emin olun

### Kayıt Olurken Hata Alıyorsanız

- Şifrenin en az 8 karakter olduğundan emin olun
- Şifre tekrarının eşleştiğini kontrol edin
- Kullanıcı adının benzersiz olduğunu kontrol edin

### Admin Paneline Giriş Yapamıyorsanız

- Kullanıcının superuser olduğundan emin olun
- Yeni superuser oluşturmak için: `python manage.py createsuperuser`

## ✅ Test Etme

1. Projeyi çalıştırın:
   ```bash
   python manage.py runserver
   ```

2. Giriş sayfasını test edin:
   - http://127.0.0.1:8000/accounts/login/

3. Kayıt sayfasını test edin:
   - http://127.0.0.1:8000/accounts/register/

4. Admin paneline giriş yapın:
   - http://127.0.0.1:8000/admin/

---

**Durum:** 🎉 Kullanıcı giriş sistemi tamamen hazır ve çalışır durumda!

