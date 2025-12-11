# STOK TAKİP PROJESİ - DETAYLI ANALİZ DOKÜMANTASYONU

## 📋 İÇİNDEKİLER
1. [Proje Genel Bakış](#proje-genel-bakış)
2. [Proje Yapısı](#proje-yapısı)
3. [Django Uygulamaları (Apps)](#django-uygulamaları-apps)
4. [API Endpoint'leri](#api-endpointleri)
5. [Decorator'lar ve Wrapped Fonksiyonlar](#decoratorlar-ve-wrapped-fonksiyonlar)
6. [Modeller (Models)](#modeller-models)
7. [Güvenlik ve Validasyon](#güvenlik-ve-validasyon)
8. [Cache ve Performans](#cache-ve-performans)
9. [Dosya Yapısı Detayları](#dosya-yapısı-detayları)

---

## 🎯 PROJE GENEL BAKIŞ

**Stok Takip Sistemi** - Django tabanlı bir stok yönetim, fatura, cari hesap ve raporlama sistemidir.

### Teknolojiler:
- **Backend**: Django 6.0
- **Veritabanı**: PostgreSQL
- **API**: Django REST Framework (DRF)
- **Cache**: Redis (opsiyonel, yoksa LocMemCache)
- **Frontend**: Django Templates + Bootstrap
- **Ek Paketler**: 
  - reportlab (PDF oluşturma)
  - openpyxl (Excel export)
  - Pillow (Resim işleme)
  - qrcode (QR kod oluşturma)
  - python-barcode (Barkod oluşturma)

### Ana Özellikler:
1. **Stok Yönetimi**: Ürün, kategori, stok hareketleri
2. **Fatura Yönetimi**: Alış/Satış faturaları, fatura kalemleri
3. **Cari Hesap**: Müşteri/Tedarikçi yönetimi, cari hareketleri
4. **Raporlama**: Dashboard, kar/maliyet, alış/satış raporları
5. **Masraf Yönetimi**: Masraf kategorileri ve masraflar
6. **Finans**: Finansal işlemler
7. **Kullanıcı Yönetimi**: Rol tabanlı yetkilendirme
8. **API**: RESTful API endpoints

---

## 📁 PROJE YAPISI

```
StokTakip/
├── accounts/              # Kullanıcı hesapları ve yetkilendirme
├── api/                   # REST API endpoints
├── cari/                  # Cari hesap yönetimi
├── fatura/                # Fatura yönetimi
├── finans/                 # Finansal işlemler
├── kullanici_yonetimi/    # Kullanıcı yönetimi
├── masraf/                # Masraf yönetimi
├── raporlar/              # Raporlama
├── stok/                  # Stok yönetimi
├── stoktakip/             # Ana proje ayarları
├── templates/             # HTML şablonları
├── static/                # CSS, JS, resimler
├── media/                 # Yüklenen dosyalar
└── logs/                  # Log dosyaları
```

---

## 🗂️ DJANGO UYGULAMALARI (APPS)

### 1. **accounts** - Kullanıcı Hesapları ve Yetkilendirme

**Dosyalar:**
- `models.py`: AuditLog modeli (kullanıcı işlem logları)
- `views.py`: Kayıt, profil, şifre değiştirme, audit log görüntüleme
- `decorators.py`: Rol tabanlı decorator'lar
- `middleware.py`: Rate limiting ve güvenlik header'ları
- `utils.py`: log_action(), get_client_ip() fonksiyonları
- `urls.py`: Account URL routing

**Önemli Fonksiyonlar:**
- `log_action()`: Kullanıcı işlemlerini loglar
- `get_client_ip()`: İstemci IP adresini alır

**Decorator'lar:**
- `@admin_required`: Sadece Admin
- `@muhasebe_required`: Admin veya Muhasebe
- `@satis_required`: Admin veya Satış
- `@depo_required`: Admin veya Depo
- `@role_required(*role_names)`: Özel rol kontrolü

**Middleware:**
- `RateLimitMiddleware`: API ve login için rate limiting (60 istek/dakika)
- `SecurityHeadersMiddleware`: Güvenlik header'ları ekler

---

### 2. **stok** - Stok Yönetimi

**Dosyalar:**
- `models.py`: Kategori, Urun, StokHareketi modelleri
- `views.py`: Ürün CRUD, stok hareketleri, toplu işlemler
- `views_barcode.py`: Barkod/QR kod görüntüleme ve tarama
- `forms.py`: Ürün ve stok hareketi formları
- `utils.py`: Stok yardımcı fonksiyonları
- `urls.py`: Stok URL routing

**Modeller:**
- `Kategori`: Ürün kategorileri
- `Urun`: Ürün bilgileri (ad, barkod, fiyat, stok)
- `StokHareketi`: Stok giriş/çıkış hareketleri

**View'lar:**
- `index()`: Ürün listesi
- `urun_ekle()`: Yeni ürün ekleme
- `urun_duzenle()`: Ürün düzenleme
- `urun_sil()`: Ürün silme
- `stok_duzenle()`: Stok miktarı düzenleme
- `stok_hareketleri()`: Ürün hareket geçmişi
- `toplu_stok_islem()`: Toplu stok işlemleri
- `stok_sayim()`: Stok sayımı
- `urun_import()`: Excel'den ürün import

**API Endpoint'leri:**
- `/api/v1/kategoriler/` - Kategori CRUD
- `/api/v1/urunler/` - Ürün CRUD
- `/api/v1/stok-hareketleri/` - Stok hareketi CRUD

---

### 3. **fatura** - Fatura Yönetimi

**Dosyalar:**
- `models.py`: Fatura, FaturaKalem modelleri
- `views.py`: Fatura CRUD, kalem yönetimi
- `forms.py`: Fatura ve fatura kalem formları
- `urls.py`: Fatura URL routing

**Modeller:**
- `Fatura`: Fatura bilgileri (no, tarih, cari, toplamlar, durum)
- `FaturaKalem`: Fatura kalemleri (ürün, miktar, fiyat, KDV)

**View'lar:**
- `index()`: Fatura listesi (filtreleme, arama, sayfalama)
- `fatura_ekle()`: Yeni fatura oluşturma
- `fatura_detay()`: Fatura detay görüntüleme
- `fatura_duzenle()`: Fatura düzenleme
- `fatura_sil()`: Fatura silme
- `fatura_kopyala()`: Fatura kopyalama
- `kalem_ekle()`: Fatura kalemi ekleme
- `kalem_duzenle()`: Fatura kalemi düzenleme
- `kalem_sil()`: Fatura kalemi silme
- `urun_bilgi_api()`: Ürün bilgisi API (JSON)

**Özellikler:**
- Otomatik fatura numarası oluşturma (SATIS-YYYYMMDD-001 formatı)
- KDV hesaplama
- İskonto desteği
- Cari hareketi otomatik oluşturma (Açık Hesap durumunda)
- Stok hareketi otomatik oluşturma

**API Endpoint'leri:**
- `/api/v1/faturalar/` - Fatura CRUD
- `/fatura/api/urun/<urun_id>/` - Ürün bilgisi (JSON)

---

### 4. **cari** - Cari Hesap Yönetimi

**Dosyalar:**
- `models.py`: Cari, CariHareketi, CariNotu, TahsilatMakbuzu, TediyeMakbuzu
- `views.py`: Cari CRUD, hareket yönetimi, ekstre, yaşlandırma
- `forms.py`: Cari ve hareket formları
- `urls.py`: Cari URL routing

**Modeller:**
- `Cari`: Müşteri/Tedarikçi bilgileri
- `CariHareketi`: Cari hesap hareketleri
- `CariNotu`: Cari notları
- `TahsilatMakbuzu`: Tahsilat makbuzları
- `TediyeMakbuzu`: Tediye (ödeme) makbuzları

**View'lar:**
- `index()`: Cari listesi
- `cari_ekle()`: Yeni cari ekleme
- `cari_detay()`: Cari detay
- `cari_duzenle()`: Cari düzenleme
- `cari_sil()`: Cari silme
- `cari_ekstre()`: Cari ekstre görüntüleme
- `cari_ekstre_pdf()`: Cari ekstre PDF export
- `cari_yaslandirma()`: Cari yaşlandırma raporu
- `hareket_listesi()`: Tüm cari hareketleri
- `hareket_ekle()`: Cari hareketi ekleme
- `not_ekle()`: Cari notu ekleme
- `tahsilat_makbuzu_ekle()`: Tahsilat makbuzu oluşturma
- `tediye_makbuzu_ekle()`: Tediye makbuzu oluşturma

**Özellikler:**
- Otomatik bakiye hesaplama
- Risk limiti kontrolü
- Yaşlandırma raporu
- PDF ekstre export

**API Endpoint'leri:**
- `/api/v1/cariler/` - Cari CRUD
- `/api/v1/cari-hareketleri/` - Cari hareketi CRUD

---

### 5. **raporlar** - Raporlama

**Dosyalar:**
- `views.py`: Dashboard ve raporlar
- `utils.py`: Excel export yardımcı fonksiyonları
- `urls.py`: Rapor URL routing

**View'lar:**
- `dashboard()`: Ana dashboard (istatistikler, grafikler)
- `kar_maliyet_raporu()`: Kar/maliyet raporu
- `alis_raporu()`: Alış faturası raporu
- `alis_raporu_excel()`: Alış raporu Excel export
- `satis_raporu()`: Satış faturası raporu
- `satis_raporu_excel()`: Satış raporu Excel export

**Özellikler:**
- Dashboard istatistikleri (toplam satış, alış, kar, stok durumu)
- Tarih aralığı filtreleme
- Excel export desteği

---

### 6. **masraf** - Masraf Yönetimi

**Dosyalar:**
- `models.py`: MasrafKategori, Masraf modelleri
- `views.py`: Masraf CRUD
- `forms.py`: Masraf formları
- `urls.py`: Masraf URL routing

**Modeller:**
- `MasrafKategori`: Masraf kategorileri
- `Masraf`: Masraf kayıtları

---

### 7. **finans** - Finansal İşlemler

**Dosyalar:**
- `models.py`: Finans modelleri
- `views.py`: Finans view'ları
- `forms.py`: Finans formları
- `urls.py`: Finans URL routing

---

### 8. **kullanici_yonetimi** - Kullanıcı Yönetimi

**Dosyalar:**
- `views.py`: Kullanıcı CRUD, rol yönetimi
- `forms.py`: Kullanıcı formları
- `urls.py`: Kullanıcı yönetimi URL routing

---

### 9. **api** - REST API

**Dosyalar:**
- `views.py`: DRF ViewSet'ler
- `serializers.py`: DRF Serializer'lar
- `permissions.py`: API permission sınıfları
- `urls.py`: API URL routing

**ViewSet'ler:**
- `KategoriViewSet`: Kategori CRUD
- `UrunViewSet`: Ürün CRUD + hareketler endpoint
- `StokHareketiViewSet`: Stok hareketi CRUD
- `CariViewSet`: Cari CRUD + hareketler endpoint
- `CariHareketiViewSet`: Cari hareketi CRUD
- `FaturaViewSet`: Fatura CRUD

**Permission Sınıfları:**
- `IsAdminOrDepo`: Admin veya Depo
- `IsAdminOrMuhasebe`: Admin veya Muhasebe
- `IsAdminOrSatis`: Admin veya Satış
- `IsAdminOnly`: Sadece Admin

---

## 🔌 API ENDPOINT'LERİ

### Base URL: `/api/v1/`

### 1. **Kategoriler** (`/api/v1/kategoriler/`)
- `GET /api/v1/kategoriler/` - Liste
- `POST /api/v1/kategoriler/` - Yeni kategori
- `GET /api/v1/kategoriler/{id}/` - Detay
- `PUT /api/v1/kategoriler/{id}/` - Güncelle
- `PATCH /api/v1/kategoriler/{id}/` - Kısmi güncelle
- `DELETE /api/v1/kategoriler/{id}/` - Sil

**Yetki**: Admin veya Depo

---

### 2. **Ürünler** (`/api/v1/urunler/`)
- `GET /api/v1/urunler/` - Liste (search, kategori filtreleme)
- `POST /api/v1/urunler/` - Yeni ürün
- `GET /api/v1/urunler/{id}/` - Detay
- `PUT /api/v1/urunler/{id}/` - Güncelle
- `PATCH /api/v1/urunler/{id}/` - Kısmi güncelle
- `DELETE /api/v1/urunler/{id}/` - Sil
- `GET /api/v1/urunler/{id}/hareketler/` - Ürün hareketleri

**Query Parametreleri:**
- `search`: Ürün adı veya barkod arama
- `kategori`: Kategori ID filtreleme

**Yetki**: Admin veya Depo

---

### 3. **Stok Hareketleri** (`/api/v1/stok-hareketleri/`)
- `GET /api/v1/stok-hareketleri/` - Liste
- `POST /api/v1/stok-hareketleri/` - Yeni hareket
- `GET /api/v1/stok-hareketleri/{id}/` - Detay
- `PUT /api/v1/stok-hareketleri/{id}/` - Güncelle
- `PATCH /api/v1/stok-hareketleri/{id}/` - Kısmi güncelle
- `DELETE /api/v1/stok-hareketleri/{id}/` - Sil

**Yetki**: Admin veya Depo

---

### 4. **Cariler** (`/api/v1/cariler/`)
- `GET /api/v1/cariler/` - Liste (search, kategori filtreleme)
- `POST /api/v1/cariler/` - Yeni cari
- `GET /api/v1/cariler/{id}/` - Detay
- `PUT /api/v1/cariler/{id}/` - Güncelle
- `PATCH /api/v1/cariler/{id}/` - Kısmi güncelle
- `DELETE /api/v1/cariler/{id}/` - Sil
- `GET /api/v1/cariler/{id}/hareketler/` - Cari hareketleri

**Query Parametreleri:**
- `search`: Cari adı arama
- `kategori`: Kategori filtreleme (musteri, tedarikci, her_ikisi)

**Yetki**: Admin veya Satış

---

### 5. **Cari Hareketleri** (`/api/v1/cari-hareketleri/`)
- `GET /api/v1/cari-hareketleri/` - Liste
- `POST /api/v1/cari-hareketleri/` - Yeni hareket
- `GET /api/v1/cari-hareketleri/{id}/` - Detay
- `PUT /api/v1/cari-hareketleri/{id}/` - Güncelle
- `PATCH /api/v1/cari-hareketleri/{id}/` - Kısmi güncelle
- `DELETE /api/v1/cari-hareketleri/{id}/` - Sil

**Yetki**: Admin veya Muhasebe

---

### 6. **Faturalar** (`/api/v1/faturalar/`)
- `GET /api/v1/faturalar/` - Liste (tip, durum filtreleme)
- `POST /api/v1/faturalar/` - Yeni fatura
- `GET /api/v1/faturalar/{id}/` - Detay (kalemler dahil)
- `PUT /api/v1/faturalar/{id}/` - Güncelle
- `PATCH /api/v1/faturalar/{id}/` - Kısmi güncelle
- `DELETE /api/v1/faturalar/{id}/` - Sil

**Query Parametreleri:**
- `tip`: Fatura tipi (Satis, Alis)
- `durum`: Fatura durumu (AcikHesap, KasadanKapanacak)

**Yetki**: 
- CRUD: Admin veya Satış
- DELETE: Admin veya Muhasebe

---

### API Dokümantasyon:
- Swagger UI: `/api/docs/` (drf-spectacular yüklüyse)
- ReDoc: `/api/redoc/` (drf-spectacular yüklüyse)
- Schema: `/api/schema/` (drf-spectacular yüklüyse)

---

## 🎨 DECORATOR'LAR VE WRAPPED FONKSİYONLAR

### 1. **Error Handling Decorator'ları** (`stoktakip/error_handling.py`)

#### `@handle_view_errors`
**Konum**: `stoktakip/error_handling.py:18`

**Kod:**
```python
def handle_view_errors(
    error_message: str = "Bir hata oluştu. Lütfen tekrar deneyin.",
    redirect_url: Optional[str] = None,
    log_error: bool = True
):
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
            try:
                return view_func(request, *args, **kwargs)
            except ValidationError as e:
                messages.error(request, str(e))
                if log_error:
                    logger.warning(f"Validation error in {view_func.__name__}: {str(e)}")
                if redirect_url:
                    return redirect(redirect_url)
                return view_func(request, *args, **kwargs)
            except PermissionDenied as e:
                # Permission denied handling
                ...
            except Exception as e:
                # Genel exception handling
                logger.error(f"Error in {view_func.__name__}: {str(e)}", exc_info=True)
                messages.error(request, error_message)
                if redirect_url:
                    return redirect(redirect_url)
                return render(request, '500.html', error_context, status=500)
        return wrapper
    return decorator
```

**Kullanım:**
```python
@handle_view_errors(error_message="Fatura oluşturulamadı", redirect_url="fatura:index")
def fatura_ekle(request):
    ...
```

**Özellikler:**
- Exception'ları yakalar ve loglar
- Kullanıcıya hata mesajı gösterir
- ValidationError, PermissionDenied ve genel Exception'ları ayrı işler
- Audit log'a kaydeder

---

#### `@handle_api_errors`
**Konum**: `stoktakip/error_handling.py:121`

**Kod:**
```python
def handle_api_errors(
    error_message: str = "API request failed",
    status_code: int = 500
):
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return view_func(*args, **kwargs)
            except ValidationError as e:
                logger.warning(f"API validation error in {view_func.__name__}: {str(e)}")
                return Response({'detail': str(e)}, status=400)
            except PermissionDenied:
                return Response({'detail': 'Yetkiniz yok'}, status=403)
            except Exception as e:
                logger.error(f"API error in {view_func.__name__}: {str(e)}", exc_info=True)
                return Response({'detail': error_message}, status=status_code)
        return wrapper
    return decorator
```

**Kullanım:**
```python
@handle_api_errors(error_message="Ürün bilgisi alınamadı", status_code=400)
def urun_bilgi_api(request, urun_id):
    ...
```

**Özellikler:**
- API endpoint'leri için error handling
- DRF Response veya JsonResponse döner
- HTTP status code kontrolü

---

#### `@database_transaction`
**Konum**: `stoktakip/error_handling.py:174`

**Kod:**
```python
def database_transaction(view_func: Callable) -> Callable:
    @wraps(view_func)
    def wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Database transaction error in {view_func.__name__}: {str(e)}", exc_info=True)
            raise  # Exception'ı yukarı fırlat
    return wrapper
```

**Kullanım:**
```python
@database_transaction
@login_required
def fatura_ekle(request):
    with transaction.atomic():
        ...
```

**Özellikler:**
- Database transaction hatalarını loglar
- View içinde `transaction.atomic()` kullanılmalı

---

#### `@safe_render`
**Konum**: `stoktakip/error_handling.py:198`

**Kod:**
```python
def safe_render(view_func: Callable) -> Callable:
    @wraps(view_func)
    def wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Template rendering error in {view_func.__name__}: {str(e)}", exc_info=True)
            messages.error(request, "Sayfa yüklenirken bir hata oluştu.")
            return redirect('raporlar:dashboard')
    return wrapper
```

**Kullanım:**
```python
@safe_render
def my_view(request):
    return render(request, 'template.html', context)
```

**Özellikler:**
- Template rendering hatalarını yakalar
- Dashboard'a yönlendirir

---

### 2. **Cache Decorator'ları** (`stoktakip/cache_utils.py`)

#### `@cache_view_result`
**Konum**: `stoktakip/cache_utils.py:13`

**Kod:**
```python
def cache_view_result(timeout: int = 300, key_prefix: Optional[str] = None):
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
            prefix = key_prefix or view_func.__name__
            cache_key = f"{prefix}_{request.user.id if request.user.is_authenticated else 'anon'}"
            
            if request.GET:
                query_string = '_'.join(f"{k}_{v}" for k, v in sorted(request.GET.items()))
                cache_key += f"_{query_string}"
            
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            result = view_func(request, *args, **kwargs)
            
            # HttpResponse objelerini cache'leme
            if isinstance(result, HttpResponse):
                return result
            
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator
```

**Kullanım:**
```python
@cache_view_result(timeout=300, key_prefix='fatura_index')
@login_required
def index(request):
    ...
```

**Özellikler:**
- View sonuçlarını cache'ler
- Kullanıcı bazlı cache key
- Query parametrelerini cache key'e ekler
- Default timeout: 5 dakika (300 saniye)

---

#### `@cache_query_result`
**Konum**: `stoktakip/cache_utils.py:62`

**Kod:**
```python
def cache_query_result(timeout: int = 300):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache_key = f"{func.__name__}_{str(args)}_{str(sorted(kwargs.items()))}"
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator
```

**Kullanım:**
```python
@cache_query_result(timeout=600)
def get_dashboard_stats():
    return {...}
```

**Özellikler:**
- Fonksiyon sonuçlarını cache'ler
- Argüman bazlı cache key

---

### 3. **Role-Based Decorator'lar** (`accounts/decorators.py`)

#### `@role_required`
**Konum**: `accounts/decorators.py:6`

**Kod:**
```python
def role_required(*role_names):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            
            user_groups = request.user.groups.values_list('name', flat=True)
            if not any(role in user_groups for role in role_names):
                raise PermissionDenied(f"Bu işlem için {role_text} yetkisi gereklidir.")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```

**Kullanım:**
```python
@role_required('Admin', 'Muhasebe')
def my_view(request):
    ...
```

**Özellikler:**
- Birden fazla rol kontrolü
- PermissionDenied exception fırlatır

---

#### `@admin_required`, `@muhasebe_required`, `@satis_required`, `@depo_required`
**Konum**: `accounts/decorators.py:28-41`

**Kod:**
```python
def admin_required(view_func):
    return role_required('Admin')(view_func)

def muhasebe_required(view_func):
    return role_required('Admin', 'Muhasebe')(view_func)

def satis_required(view_func):
    return role_required('Admin', 'Satış')(view_func)

def depo_required(view_func):
    return role_required('Admin', 'Depo')(view_func)
```

**Kullanım:**
```python
@admin_required
def admin_only_view(request):
    ...
```

---

## 🗄️ MODELLER (MODELS)

### Stok Modelleri (`stok/models.py`)

#### `Kategori`
- `ad`: Kategori adı
- `aciklama`: Açıklama
- `olusturma_tarihi`: Oluşturma tarihi

#### `Urun`
- `kategori`: ForeignKey(Kategori)
- `ad`: Ürün adı
- `barkod`: Barkod (unique)
- `birim`: Birim (Adet, Kg, vb.)
- `alis_fiyati`: Alış fiyatı
- `fiyat`: Satış fiyatı
- `min_stok_adedi`: Minimum stok (her zaman 0)
- `resim`: Ürün resmi
- `qr_kod`: QR kod resmi
- `mevcut_stok`: Property (giriş - çıkış)

#### `StokHareketi`
- `urun`: ForeignKey(Urun)
- `islem_turu`: giriş/çıkış
- `miktar`: Miktar
- `aciklama`: Açıklama
- `tarih`: İşlem tarihi
- `olusturan`: ForeignKey(User)

---

### Fatura Modelleri (`fatura/models.py`)

#### `Fatura`
- `fatura_no`: Fatura numarası (unique, otomatik oluşturulur)
- `cari`: ForeignKey(Cari)
- `fatura_tarihi`: Fatura tarihi
- `fatura_tipi`: Satis/Alis
- `durum`: AcikHesap/KasadanKapanacak
- `toplam_tutar`: KDV hariç toplam
- `kdv_tutari`: KDV tutarı
- `genel_toplam`: Genel toplam
- `iskonto_orani`: İskonto oranı (%)
- `iskonto_tutari`: İskonto tutarı
- `aciklama`: Açıklama
- `olusturan`: ForeignKey(User)

**Metodlar:**
- `olustur_fatura_no()`: Otomatik fatura no oluşturur (SATIS-YYYYMMDD-001)
- `hesapla_toplamlar()`: Toplamları yeniden hesaplar
- `save()`: Cari hareketi ve stok hareketi oluşturur

#### `FaturaKalem`
- `fatura`: ForeignKey(Fatura)
- `urun`: ForeignKey(Urun)
- `urun_adi`: Ürün adı (snapshot)
- `miktar`: Miktar
- `birim_fiyat`: Birim fiyat
- `kdv_orani`: KDV oranı (%)
- `kdv_tutari`: KDV tutarı
- `toplam_tutar`: Toplam tutar (KDV hariç)
- `sira_no`: Sıra numarası

**Metodlar:**
- `save()`: KDV ve toplam tutarı hesaplar, fatura toplamlarını günceller

---

### Cari Modelleri (`cari/models.py`)

#### `Cari`
- `ad_soyad`: Ad Soyad / Firma Adı
- `vergi_dairesi`: Vergi dairesi
- `vergi_no`: Vergi numarası
- `tc_vkn`: TC/VKN
- `telefon`: Telefon
- `email`: E-posta
- `adres`: Adres
- `sehir`: Şehir
- `ilce`: İlçe
- `kategori`: musteri/tedarikci/her_ikisi
- `durum`: aktif/pasif
- `risk_limiti`: Risk limiti

**Property'ler:**
- `bakiye`: Otomatik hesaplanan bakiye
- `risk_asimi_var_mi`: Risk limiti aşımı kontrolü
- `son_islem_tarihi`: Son işlem tarihi

#### `CariHareketi`
- `cari`: ForeignKey(Cari)
- `hareket_turu`: satis_faturasi/alis_faturasi/tahsilat/odeme/iade
- `tutar`: Tutar
- `aciklama`: Açıklama
- `belge_no`: Belge numarası
- `tarih`: Tarih
- `odeme_yontemi`: nakit/havale/kredi_karti/cek/senet
- `olusturan`: ForeignKey(User)

#### `CariNotu`
- `cari`: ForeignKey(Cari)
- `baslik`: Başlık
- `icerik`: İçerik
- `olusturan`: ForeignKey(User)

#### `TahsilatMakbuzu`
- `makbuz_no`: Makbuz numarası (unique)
- `cari`: ForeignKey(Cari)
- `tutar`: Tutar
- `odeme_yontemi`: Ödeme yöntemi
- `tarih`: Tarih
- `aciklama`: Açıklama
- `dekont_no`: Dekont numarası
- `olusturan`: ForeignKey(User)

**Özellikler:**
- `save()`: Otomatik olarak CariHareketi oluşturur (tahsilat)

#### `TediyeMakbuzu`
- `makbuz_no`: Makbuz numarası (unique)
- `cari`: ForeignKey(Cari)
- `tutar`: Tutar
- `odeme_yontemi`: Ödeme yöntemi
- `tarih`: Tarih
- `aciklama`: Açıklama
- `dekont_no`: Dekont numarası
- `olusturan`: ForeignKey(User)

**Özellikler:**
- `save()`: Otomatik olarak CariHareketi oluşturur (odeme)

---

## 🔒 GÜVENLİK VE VALİDASYON

### Security Utils (`stoktakip/security_utils.py`)

#### `sanitize_string(value, max_length=None)`
- String input'u temizler
- Null byte karakterlerini kaldırır
- Maksimum uzunluk kontrolü

#### `sanitize_integer(value, min_value=None, max_value=None)`
- Integer input'u validate eder
- Min/max değer kontrolü

#### `sanitize_decimal(value, min_value=None, max_value=None)`
- Decimal/Float input'u validate eder
- Min/max değer kontrolü

#### `validate_date_range(start_date, end_date)`
- Tarih aralığını validate eder
- Maksimum 1 yıllık aralık kontrolü

#### `validate_search_query(query, max_length=100)`
- Arama sorgusunu validate eder
- Sadece alfanumerik karakterler, boşluk ve bazı özel karakterlere izin verir

#### `sanitize_sql_input(value)`
- SQL injection'a karşı input'u temizler
- Tehlikeli SQL karakterlerini kaldırır

#### `safe_html_render(html_content)`
- HTML içeriğini güvenli bir şekilde render eder
- XSS koruması (script tag'lerini kaldırır)

---

## ⚡ CACHE VE PERFORMANS

### Cache Yapılandırması (`stoktakip/settings.py`)

**Redis Kullanımı:**
- Redis varsa: `django_redis.cache.RedisCache`
- Redis yoksa: `django.core.cache.backends.locmem.LocMemCache`
- Session cache: Redis varsa cache backend, yoksa database

**Cache Ayarları:**
- Timeout: 300 saniye (5 dakika)
- Key prefix: `stoktakip`
- Session engine: Redis varsa cache, yoksa database

### Cache Helper Fonksiyonları (`stoktakip/cache_utils.py`)

#### `invalidate_cache(pattern)`
- Belirli bir pattern'e uyan cache key'lerini siler
- Redis için pattern matching, LocMemCache için tüm cache'i temizler

#### `get_or_set_cache(key, callable_func, timeout=300)`
- Cache'den oku, yoksa fonksiyonu çalıştır ve cache'e yaz

---

## 📂 DOSYA YAPISI DETAYLARI

### Ana Proje (`stoktakip/`)

#### `settings.py`
- Django ayarları
- Database: PostgreSQL
- Cache: Redis (opsiyonel)
- Logging: Console + File
- Security: Production için SSL, secure cookies
- REST Framework: Token authentication, throttling

#### `urls.py`
- Ana URL routing
- App URL'lerini include eder
- API documentation (drf-spectacular/drf-yasg)

#### `error_handling.py`
- Error handling decorator'ları
- View ve API error handling

#### `cache_utils.py`
- Cache decorator'ları ve helper fonksiyonları

#### `security_utils.py`
- Input validation ve sanitization fonksiyonları

#### `template_helpers.py`
- Template helper fonksiyonları (HTML generation)
- Pagination, table, badge, filter form HTML oluşturma

#### `views.py`
- Home view
- Custom logout
- Error handlers (404, 500)

---

### Templates (`templates/`)

**Yapı:**
- `base.html`: Ana template
- `403.html`, `404.html`, `500.html`: Hata sayfaları
- `accounts/`: Kullanıcı hesapları şablonları
- `stok/`: Stok şablonları
- `fatura/`: Fatura şablonları
- `cari/`: Cari şablonları
- `raporlar/`: Rapor şablonları
- `masraf/`: Masraf şablonları
- `finans/`: Finans şablonları
- `kullanici_yonetimi/`: Kullanıcı yönetimi şablonları
- `includes/`: Include edilen parçalar

---

### Static Files (`static/`)

**Yapı:**
- `css/`: CSS dosyaları (site.css, toast.css)
- `js/`: JavaScript dosyaları (keyboard-shortcuts.js, toast.js)
- `img/`: Resim dosyaları

---

### Media Files (`media/`)

**Yapı:**
- `urunler/`: Ürün resimleri
- `qr_kodlar/`: QR kod resimleri

---

## 🔧 TEMİZLENEN KODLAR

### fatura/views.py
**Kaldırılan Import'lar:**
- `from reportlab.lib import colors`
- `from reportlab.lib.pagesizes import A4`
- `from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether`
- `from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT`
- `from io import BytesIO`
- `from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle`
- `from reportlab.lib.units import inch`
- `from openpyxl import Workbook`
- `from openpyxl.styles import Font, Alignment, PatternFill`
- `from django.http import HttpResponse` (sadece JsonResponse kullanılıyor)

**Sebep:** PDF ve Excel export fonksiyonları kaldırılmış (satır 999'da yorum var: "PDF ve önizleme view'ları kaldırıldı")

---

## 📝 ÖNEMLİ NOTLAR

1. **Fatura Numarası:** Otomatik oluşturulur (SATIS-YYYYMMDD-001 formatı)
2. **Stok Hesaplama:** `mevcut_stok` property ile dinamik hesaplanır (giriş - çıkış)
3. **Cari Bakiye:** Property ile dinamik hesaplanır (alacak - borç)
4. **Transaction Yönetimi:** Kritik işlemler `transaction.atomic()` içinde yapılır
5. **Cache:** View'lar cache'lenir (5 dakika timeout)
6. **Logging:** Tüm önemli işlemler loglanır (AuditLog + file logging)
7. **Güvenlik:** Input validation, XSS koruması, SQL injection koruması
8. **Rate Limiting:** API ve login için rate limiting (60 istek/dakika)
9. **Error Handling:** Tüm view'lar error handling decorator'ları ile korunur
10. **Role-Based Access:** Grup bazlı yetkilendirme (Admin, Muhasebe, Satış, Depo)

---

## 🚀 KULLANIM ÖRNEKLERİ

### View Örneği (Decorator'larla):
```python
@cache_view_result(timeout=300, key_prefix='fatura_index')
@handle_view_errors(error_message="Fatura listesi yüklenirken bir hata oluştu.")
@login_required
def index(request):
    # View kodu
    ...
```

### API ViewSet Örneği:
```python
class UrunViewSet(viewsets.ModelViewSet):
    queryset = Urun.objects.select_related('kategori').all()
    serializer_class = UrunSerializer
    permission_classes = [IsAdminOrDepo]
    
    @handle_api_errors
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
```

### Model Örneği (Otomatik Hesaplama):
```python
class Fatura(models.Model):
    def hesapla_toplamlar(self):
        kalemler = self.kalemler.all()
        toplam_tutar = kalemler.aggregate(toplam=Sum('toplam_tutar'))['toplam'] or Decimal('0.00')
        # ...
```

---

## 📊 VERİTABANI İLİŞKİLERİ

```
User
├── AuditLog (olusturan)
├── StokHareketi (olusturan)
├── CariHareketi (olusturan)
├── Fatura (olusturan)
└── ...

Cari
├── Fatura (cari)
├── CariHareketi (cari)
├── CariNotu (cari)
├── TahsilatMakbuzu (cari)
└── TediyeMakbuzu (cari)

Urun
├── FaturaKalem (urun)
└── StokHareketi (urun)

Fatura
└── FaturaKalem (fatura)

Kategori
└── Urun (kategori)
```

---

## ✅ SONUÇ

Bu proje, Django best practices kullanılarak geliştirilmiş, güvenli, ölçeklenebilir bir stok takip sistemidir. Decorator pattern, cache mekanizması, error handling, input validation ve role-based access control gibi modern yazılım geliştirme teknikleri kullanılmıştır.

**Temizlenen Kodlar:**
- ✅ `fatura/views.py`: Kullanılmayan reportlab ve openpyxl import'ları kaldırıldı

**Proje Durumu:**
- ✅ Tüm modeller tanımlı ve çalışıyor
- ✅ API endpoint'leri hazır
- ✅ Decorator'lar ve wrapped fonksiyonlar dokümante edildi
- ✅ Güvenlik ve validasyon mekanizmaları aktif
- ✅ Cache ve performans optimizasyonları yapılmış

---

**Son Güncelleme:** 2024
**Versiyon:** 1.0.0

