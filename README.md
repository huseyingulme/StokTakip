# StokTakip - Stok ve Cari Takip Sistemi

Modern ve kapsamlı bir stok takip, cari hesap yönetimi ve fatura yönetim sistemi.

## 🚀 Özellikler

### 📦 Stok Yönetimi
- Ürün ve kategori yönetimi
- Stok giriş/çıkış işlemleri
- Minimum stok seviyesi takibi
- Barkod desteği
- Stok hareket geçmişi

### 💼 Cari Hesap Yönetimi
- Müşteri ve tedarikçi yönetimi
- Cari hareket takibi
- Tahsilat ve tediye makbuzları
- Risk limiti kontrolü
- Cari ekstre raporları
- Cari notları

### 📄 Fatura Yönetimi
- Alış ve satış faturaları
- Fatura kalem yönetimi
- KDV hesaplama
- Fatura durum takibi
- Otomatik stok güncelleme

### 💰 Finans Yönetimi
- Hesap kartları (Kasa, Banka, Kredi Kartı)
- Gelir/Gider/Transfer işlemleri
- Finans hareket takibi
- Bakiye yönetimi

### 📊 Bütçe Yönetimi
- Bütçe planlama
- Kategori bazlı bütçe takibi
- Harcama analizi
- Kalan bütçe hesaplama

### 📈 Raporlar
- Dashboard (Genel istatistikler)
- Kar/Maliyet raporları
- Satış raporları
- Alış raporları
- Tarih bazlı filtreleme

### 💸 Masraf Yönetimi
- Masraf kategorileri
- Masraf kayıtları
- Ödeme durumu takibi
- Masraf raporları

## 🛠️ Teknolojiler

- **Backend:** Django 6.0
- **Veritabanı:** PostgreSQL
- **Frontend:** Bootstrap 5, Bootstrap Icons
- **Python:** 3.13+

## 📋 Kurulum

### 1. Gereksinimler
```bash
pip install -r requirements.txt
```

### 2. Veritabanı Ayarları
`.env` dosyası oluşturun:
```env
DB_NAME=StokTakip
DB_USER=postgres
DB_PASSWORD=sql
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=your-secret-key-here
```

### 3. Veritabanı Migrations
```bash
python manage.py migrate
```

### 4. Süper Kullanıcı Oluşturma
```bash
python manage.py createsuperuser
```

### 5. Sunucuyu Başlatma
```bash
python manage.py runserver
```

## 📁 Proje Yapısı

```
StokTakip/
├── accounts/          # Kullanıcı yönetimi
├── stok/              # Stok yönetimi
├── cari/              # Cari hesap yönetimi
├── fatura/            # Fatura yönetimi
├── masraf/            # Masraf yönetimi
├── finans/            # Finans yönetimi
├── butce/             # Bütçe yönetimi
├── raporlar/          # Raporlar
├── templates/         # HTML şablonları
├── static/            # CSS, JS, resimler
└── stoktakip/         # Ana proje ayarları
```

## 🔐 Güvenlik

- Kullanıcı kimlik doğrulama sistemi
- CSRF koruması
- XSS koruması
- SQL injection koruması
- Session yönetimi
- Güvenli şifre validasyonu

## 📝 Kullanım

1. **Giriş Yapın:** `/accounts/login/` adresinden giriş yapın
2. **Dashboard:** Ana sayfada genel istatistikleri görüntüleyin
3. **Stok Yönetimi:** Ürün ekleyin, stok hareketleri yapın
4. **Cari Yönetimi:** Müşteri/tedarikçi ekleyin, hareketleri takip edin
5. **Fatura:** Alış/satış faturaları oluşturun
6. **Raporlar:** Detaylı raporları görüntüleyin

## 🎯 Özellikler

- ✅ Responsive tasarım (mobil uyumlu)
- ✅ Modern ve kullanıcı dostu arayüz
- ✅ Gelişmiş arama ve filtreleme
- ✅ Sayfalama (pagination)
- ✅ Hata yönetimi (404, 500 sayfaları)
- ✅ Mesaj sistemi (başarı/hata bildirimleri)
- ✅ Admin paneli entegrasyonu

## 📊 Veritabanı

PostgreSQL veritabanı kullanılmaktadır. Tüm modeller:
- Stok (Kategori, Ürün, StokHareketi)
- Cari (Cari, CariHareketi, CariNotu, TahsilatMakbuzu, TediyeMakbuzu)
- Fatura (Fatura, FaturaKalem)
- Masraf (MasrafKategori, Masraf)
- Finans (HesapKart, FinansHareketi)
- Bütçe (ButceKategori, Butce)

## 🔄 Güncellemeler

- ✅ Finans modülü CRUD işlemleri eklendi
- ✅ Bütçe modülü CRUD işlemleri eklendi
- ✅ Error handling sayfaları eklendi
- ✅ Güvenlik ayarları geliştirildi
- ✅ Forms validasyonu eklendi
- ✅ Admin kayıtları tamamlandı

## 📞 Destek

Herhangi bir sorun için issue açabilir veya proje yöneticisi ile iletişime geçebilirsiniz.

## 📄 Lisans

Bu proje özel kullanım içindir.

---

**Geliştirici Notları:**
- Tüm view'ler `@login_required` ile korunmaktadır
- Forms validasyonu eklenmiştir
- Error handling sayfaları mevcuttur
- Güvenlik ayarları production için hazırdır
