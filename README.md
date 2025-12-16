# StokTakip - Stok ve Cari Takip Sistemi 

Kurumsal ölçekli stok ve ticari süreç yönetimi için geliştirilmiş bir **Django tabanlı stok takip ve ön muhasebe uygulaması**.

Bu proje ile;
- **Stok** hareketlerini (alış, satış, sayım, toplu işlem vb.) takip edebilir,
- **Cari** hesaplarınızı (müşteri / tedarikçi) yönetebilir,
- **Fatura** süreçlerinizi uçtan uca kaydedip raporlayabilir,
- **Finans** hareketlerinizi, kasa/banka hesaplarınızı izleyebilirsiniz,
- **Masraf** yönetimi yaparak giderlerinizi kategorize edebilirsiniz,
- **Kullanıcı yönetimi ve yetkilendirme** ile çok kullanıcılı, güvenli bir yapı kurabilirsiniz,
- Dashboard ve detaylı **raporlar** ile karar destek süreçlerinizi güçlendirebilirsiniz.

Uygulama; PostgreSQL veritabanı, Django REST Framework, opsiyonel Redis cache, SMTP e-posta ve isteğe bağlı API dokümantasyonu (drf-spectacular) ile modern bir Django mimarisi üzerine inşa edilmiştir.

---

## Özellikler

- **Stok Yönetimi (`stok` uygulaması)**
  - Ürün kartı oluşturma ve güncelleme
  - Minimum stok seviyesi takibi
  - Stok giriş / çıkış hareketleri (`stok_hareketleri`)
  - Stok sayım ve **toplu stok işlem** ekranları (`stok_sayim`, `toplu_stok_islem`)

- **Cari Yönetimi (`cari` uygulaması)**
  - Müşteri / tedarikçi kartları
  - Cari hareketler (borç / alacak)
  - Cari detay sayfaları ve **ekstre** dökümleri
  - Tahsilat ve tediye makbuzları

- **Fatura Yönetimi (`fatura` uygulaması)**
  - Alış / satış faturaları
  - Fatura kalemleri ve ürün bazlı takip
  - İskonto oranı / tutarı desteği
  - Fatura numarası, durum bilgisi gibi alanlarla ticari süreç takibi

- **Finans Yönetimi (`finans` uygulaması)**
  - Kasa / banka hesapları
  - Gelir / gider hareketleri
  - Hesap hareketleri üzerinden raporlama

- **Masraf Yönetimi (`masraf` uygulaması)**
  - Masraf kalemleri oluşturma
  - Masraf formları ve silme ekranları

- **Raporlama (`raporlar` uygulaması)**
  - **Dashboard**: Özet metrikler, satış / alış grafikleri
  - Satış raporu
  - Alış raporu
  - Kâr / maliyet raporları

- **Kullanıcı Yönetimi (`kullanici_yonetimi` uygulaması)**
  - Kullanıcı oluşturma / güncelleme / silme
  - Kullanıcı detay ve liste ekranları
  - Kullanıcı bazlı raporlama

- **Hesap ve Yetkilendirme (`accounts` uygulaması)**
  - Django auth ile entegre giriş / çıkış
  - Profil sayfası (`profile.html`)
  - Güvenli **şifre sıfırlama** akışı ("şifremi unuttum" sayfaları)
  - Gelişmiş **rate limiting** ve güvenlik başlıkları (özel middleware)
  - Kullanıcı işlem loglarını tutan audit log ekranı

- **API ve Entegrasyon (`api` uygulaması)**
  - Django REST Framework ile JSON API uçları
  - Oturum ve Token tabanlı kimlik doğrulama
  - Opsiyonel drf-spectacular entegrasyonu ile otomatik API dokümantasyonu

- **Altyapı & Güvenlik**
  - PostgreSQL veritabanı
  - Redis cache (varsa) veya LocMemCache fallback
  - Rate limiting (anon ve kullanıcı bazlı)
  - Güvenli şifre politikaları (Django password validators)
  - SMTP e-posta ile gerçek şifre sıfırlama / bildirim alt yapısı
  - Üretim ortamına özel `DEBUG`, `ALLOWED_HOSTS`, `SECRET_KEY` ve güvenlik başlıkları

---

## Mimari Genel Bakış

Proje, klasik **Django çok uygulamalı (multi-app) monolit** mimarisini kullanır:

- **Çekirdek Proje**: `stoktakip/`
  - `settings.py`: Ortam değişkenleriyle yönetilen konfigürasyon (DEBUG, DB, e-posta, cache, rate limit vb.)
  - `urls.py`: Tüm uygulamaların URL yönlendirmeleri
  - `template_helpers.py`: Şablonlarda kullanılan yardımcı fonksiyonlar
  - `error_handling.py`, `security_utils.py`, `cache_utils.py`: Hata, güvenlik ve cache ile ilgili yardımcılar

- **Alan Bazlı Uygulamalar**
  - `stok/`: Ürün, stok hareketleri, sayım, barkod/QR kod
  - `cari/`: Cari hesaplar ve hareketler
  - `fatura/`: Faturalar ve fatura kalemleri
  - `finans/`: Kasa/banka ve finansal hareketler
  - `masraf/`: Masraf kayıtları
  - `raporlar/`: Dashboard ve raporlama ekranları
  - `kullanici_yonetimi/`: Kullanıcı CRUD ve raporları
  - `accounts/`: Kimlik doğrulama, profil, güvenlik, e-posta servisleri
  - `api/`: REST API endpoint’leri

- **Sunum Katmanı**
  - Ortak `base.html` layout’u
  - Her modül için alt klasörlerde özelleşmiş şablonlar (ör. `templates/stok/`, `templates/cari/`)
  - Yeniden kullanılabilir `includes/` parçaları (`form_field`, `delete_confirm`, `card_wrapper` vb.)

---

## Kurulum

### 1. Gerekli Bağımlılıkları Yükleme

Öncelikle repoyu klonlayın ve sanal ortamınızı oluşturun:

```bash
# Projeyi klonla
git clone <repo-url>
cd StokTakip

# (Opsiyonel) Sanal ortam oluştur ve aktifleştir
python -m venv venv
venv\Scripts\activate  # Windows
# veya
source venv/bin/activate  # Linux / macOS

# Bağımlılıkları yükle
pip install -r requirements.txt
```

### 2. Ortam Değişkenleri (`.env`)

Proje, kritik ayarları `.env` dosyası üzerinden yönetir. Kök dizinde bir `.env` dosyası oluşturup aşağıdaki örneği ihtiyaçlarınıza göre doldurun:

```env
# Django
DEBUG=True
SECRET_KEY=django-super-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Veritabanı (PostgreSQL)
DB_NAME=StokTakip
DB_USER=postgres
DB_PASSWORD=sql
DB_HOST=localhost
DB_PORT=5432

# E-posta (Gmail SMTP örneği)
EMAIL_HOST_USER=you@gmail.com
EMAIL_HOST_PASSWORD=uygulama_sifresi
DEFAULT_FROM_EMAIL="Stok Takip <you@gmail.com>"

# Redis (isteğe bağlı)
REDIS_URL=redis://127.0.0.1:6379/1
```

- **DEBUG**: Geliştirme ortamında `True`, üretimde mutlaka `False` olmalıdır.
- **SECRET_KEY**: Üretim ortamında güçlü, benzersiz bir key kullanın ve kod tabanına koymayın.
- **ALLOWED_HOSTS**: Üretimde gerçek domain / IP’leri ekleyin.

### 3. Veritabanı Migrasyonları

```bash
python manage.py migrate
```

İlk süper kullanıcıyı oluşturun:

```bash
python manage.py createsuperuser
```

### 4. Statik Dosyalar

Geliştirme ortamında Django statik dosyaları kendisi servis eder. Üretim ortamı için:

```bash
python manage.py collectstatic
```

### 5. Sunucuyu Çalıştırma

```bash
python manage.py runserver
```

Ardından tarayıcınızdan aşağıdaki adrese gidin:

```text
http://127.0.0.1:8000/
```

Dashboard ve diğer modüllere `raporlar/`, `stok/`, `cari/` vb. URL’ler üzerinden erişebilirsiniz.

---

## Geliştirme Ortamı

- **Dil & Framework**: Python, Django, Django REST Framework
- **Veritabanı**: PostgreSQL
- **Cache**: Redis (varsa), aksi halde `LocMemCache`
- **API Dökümantasyonu**: `drf-spectacular` (kuruluysa otomatik entegre olur)
- **Önbellekleme & Rate Limiting**: Django cache + DRF throttle sınıfları

Geliştirme sırasında tipik akış:

1. İlgili uygulama içinde (`stok/`, `cari/` vb.) model / view / form değişikliklerini yapın.
2. Gerekirse yeni migrasyon oluşturun:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
3. Şablonları `templates/<uygulama_adı>/` altında güncelleyin.
4. Gerekirse yeni API endpoint’lerini `api/` uygulamasında tanımlayın.

---

## Güvenlik Notları

- Üretim ortamında:
  - **`DEBUG=False`** olmalı.
  - **`SECRET_KEY`** mutlaka `.env` içinde tanımlanmalı ve gizli tutulmalı.
  - **`ALLOWED_HOSTS`** gerçek domain / IP’ler ile doldurulmalı.
  - HTTPS kullanılıyorsa `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` gibi ayarlar devreye girer.
- Giriş denemeleri ve hassas istekler özel **RateLimit middleware** ile sınırlandırılır.
- Şifreler Django’nun yerleşik password validators seti ile güçlendirilmiştir.

---

## E-posta ve Şifre Sıfırlama Akışı

- Uygulama, varsayılan olarak **SMTP üzerinden e-posta** gönderecek şekilde yapılandırılmıştır.
- Şifre sıfırlama süreci;
  - `forgot_password.html` üzerinden e-posta alma,
  - Kullanıcıya token içeren link gönderme,
  - `password_reset_confirm.html` üzerinden yeni şifre belirleme,
  - Tamamlandığında `password_reset_complete.html` ekranına yönlendirme
  adımlarından oluşur.

Geliştirme aşamasında gerçek SMTP yerine isterseniz Django’nun **console backend**’ini kullanabilirsiniz (settings’te `EMAIL_BACKEND` değerini değiştirmek yeterlidir).

---

## Loglama ve İzleme

Proje, Django’nun logging altyapısını kullanarak;

- Geliştirme ortamında konsola basit loglar,
- Üretim ortamında dönen log dosyalarına (ör. `logs/stoktakip.log`) detaylı kayıt

alacak şekilde yapılandırılmıştır. Log dosyaları **rotating** handler ile sınırlı boyutta tutulur.

