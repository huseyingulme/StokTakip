# 🐍 PYTHON ÖĞRENİYORUM - STOK TAKİP PROJESİ İLE

## 📚 İÇİNDEKİLER

1. [Python Nedir?](#python-nedir)
2. [Python Temel Konuları](#python-temel-konuları)
3. [Django Framework Nedir?](#django-framework-nedir)
4. [Proje Yapısını Anlama](#proje-yapısını-anlama)
5. [Kod Örnekleri ve Açıklamaları](#kod-örnekleri-ve-açıklamaları)
6. [Proje Özellikleri Detaylı](#proje-özellikleri-detaylı)
7. [Adım Adım Öğrenme Rehberi](#adım-adım-öğrenme-rehberi)

---

## 🐍 PYTHON NEDİR?

Python, kolay öğrenilen, güçlü bir programlama dilidir. Web siteleri, veri analizi, yapay zeka ve daha birçok alanda kullanılır.

### Python'un Avantajları:
- ✅ Okunması kolay (İngilizce'ye benzer)
- ✅ Öğrenmesi kolay
- ✅ Çok yönlü (web, veri, AI, oyun)
- ✅ Büyük topluluk desteği
- ✅ Ücretsiz ve açık kaynak

### Python'da Basit Örnek:
```python
# Bu bir yorum satırıdır (açıklama)
print("Merhaba Dünya!")  # Ekrana yazdırır

# Değişken tanımlama
isim = "Ahmet"
yas = 25

# Matematik işlemleri
toplam = 10 + 20
print(toplam)  # 30 yazdırır
```

---

## 📖 PYTHON TEMEL KONULARI

### 1. DEĞİŞKENLER (Variables)

Değişken, veri saklamak için kullanılan bir kutudur.

```python
# String (Metin) - Tırnak içinde yazılır
isim = "Ahmet"
soyad = 'Yılmaz'  # Tek tırnak da olabilir

# Integer (Tam Sayı)
yas = 25
stok_adedi = 100

# Float (Ondalıklı Sayı)
fiyat = 99.99
kdv_orani = 18.5

# Boolean (True/False - Doğru/Yanlış)
stok_var_mi = True
pasif_mi = False

# List (Liste) - Birden fazla değer
urunler = ["Ürün 1", "Ürün 2", "Ürün 3"]
fiyatlar = [10.5, 20.0, 30.75]

# Dictionary (Sözlük) - Anahtar-Değer çiftleri
urun_bilgisi = {
    "ad": "Laptop",
    "fiyat": 5000,
    "stok": 10
}
```

**Projede Kullanım:**
```python
# fatura/views.py içinde
fatura_no = "SATIS-20241201-001"  # String
miktar = 5  # Integer
birim_fiyat = 100.50  # Float
durum = True  # Boolean
```

---

### 2. VERİ TİPLERİ (Data Types)

Python'da her değerin bir tipi vardır:

```python
# type() fonksiyonu ile tip öğrenilir
print(type("Merhaba"))  # <class 'str'> - String
print(type(25))         # <class 'int'> - Integer
print(type(99.99))      # <class 'float'> - Float
print(type(True))       # <class 'bool'> - Boolean
print(type([1, 2, 3]))  # <class 'list'> - List
print(type({"a": 1}))   # <class 'dict'> - Dictionary
```

**Projede Kullanım:**
```python
# stok/models.py içinde
ad = models.CharField(max_length=200)  # String tipi
fiyat = models.DecimalField(...)      # Decimal (ondalıklı sayı) tipi
miktar = models.IntegerField(...)     # Integer (tam sayı) tipi
```

---

### 3. OPERATÖRLER (Operators)

#### Aritmetik Operatörler:
```python
toplam = 10 + 5      # Toplama: 15
fark = 10 - 5        # Çıkarma: 5
carpim = 10 * 5      # Çarpma: 50
bolum = 10 / 5       # Bölme: 2.0
us = 2 ** 3          # Üs: 8 (2³)
mod = 10 % 3         # Mod (kalan): 1
```

#### Karşılaştırma Operatörleri:
```python
10 == 10   # Eşit mi? True
10 != 5    # Eşit değil mi? True
10 > 5     # Büyük mü? True
10 < 5     # Küçük mü? False
10 >= 10   # Büyük veya eşit mi? True
10 <= 5    # Küçük veya eşit mi? False
```

#### Mantıksal Operatörler:
```python
True and True   # VE: True
True and False  # VE: False
True or False   # VEYA: True
not True        # DEĞİL: False
```

**Projede Kullanım:**
```python
# fatura/views.py içinde
if miktar > 0:  # Eğer miktar 0'dan büyükse
    # İşlem yap
    pass

if durum == 'AcikHesap' and genel_toplam > 0:  # VE operatörü
    # Cari hareketi oluştur
    pass
```

---

### 4. KOŞULLU İFADELER (If-Else)

Programın akışını kontrol eder:

```python
# Basit if
yas = 18
if yas >= 18:
    print("Reşit")
else:
    print("Reşit değil")

# Çoklu koşul (elif)
not = 85
if not >= 90:
    print("A")
elif not >= 80:
    print("B")
elif not >= 70:
    print("C")
else:
    print("F")

# İç içe if
stok = 10
if stok > 0:
    if stok < 5:
        print("Stok azalıyor!")
    else:
        print("Stok yeterli")
else:
    print("Stok yok!")
```

**Projede Kullanım:**
```python
# fatura/views.py içinde
if fatura.durum == 'AcikHesap':
    # Açık hesap işlemleri
    if fatura.genel_toplam > 0:
        # Cari hareketi oluştur
        CariHareketi.objects.create(...)
elif fatura.durum == 'KasadanKapanacak':
    # Kasadan kapanacak işlemleri
    pass
```

---

### 5. DÖNGÜLER (Loops)

Aynı işlemi tekrar tekrar yapmak için:

#### For Döngüsü:
```python
# Liste üzerinde döngü
urunler = ["Ürün 1", "Ürün 2", "Ürün 3"]
for urun in urunler:
    print(urun)  # Her ürünü yazdırır

# Sayı aralığında döngü
for i in range(5):  # 0, 1, 2, 3, 4
    print(i)

for i in range(1, 6):  # 1, 2, 3, 4, 5
    print(i)

# Dictionary üzerinde döngü
urun = {"ad": "Laptop", "fiyat": 5000}
for anahtar, deger in urun.items():
    print(f"{anahtar}: {deger}")
```

#### While Döngüsü:
```python
sayac = 0
while sayac < 5:
    print(sayac)
    sayac += 1  # sayac = sayac + 1
```

**Projede Kullanım:**
```python
# fatura/views.py içinde - Kalemleri ekleme
for kalem_data in gecerli_kalemler:
    try:
        urun_id = int(kalem_data['urun_id'])
        urun = Urun.objects.get(pk=urun_id)
        # Kalem oluştur
        FaturaKalem.objects.create(...)
    except Exception as e:
        logger.error(f"Hata: {e}")
        continue  # Bir sonraki kaleme geç
```

---

### 6. FONKSİYONLAR (Functions)

Tekrar kullanılabilir kod blokları:

```python
# Basit fonksiyon
def merhaba():
    print("Merhaba!")

merhaba()  # Fonksiyonu çağır

# Parametreli fonksiyon
def topla(a, b):
    sonuc = a + b
    return sonuc

toplam = topla(10, 20)  # 30

# Varsayılan parametre
def carp(a, b=2):
    return a * b

carp(5)      # 10 (b varsayılan 2)
carp(5, 3)   # 15 (b=3)

# Çoklu değer döndürme
def hesapla(a, b):
    toplam = a + b
    fark = a - b
    return toplam, fark

t, f = hesapla(10, 5)  # t=15, f=5
```

**Projede Kullanım:**
```python
# stoktakip/security_utils.py içinde
def sanitize_string(value, max_length=None):
    """String input'u temizler"""
    if not isinstance(value, str):
        raise ValidationError("Input must be a string")
    
    cleaned = value.strip()  # Başta/sondaki boşlukları temizle
    
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length]  # Kısalt
    
    return cleaned

# Kullanım
temiz_metin = sanitize_string("  Merhaba  ", max_length=10)
```

---

### 7. CLASS (Sınıf) ve OBJECT (Nesne)

Sınıf, bir şablon; nesne, o şablondan oluşturulan örnektir:

```python
# Sınıf tanımlama
class Urun:
    # __init__: Nesne oluşturulduğunda çalışır
    def __init__(self, ad, fiyat):
        self.ad = ad
        self.fiyat = fiyat
        self.stok = 0
    
    # Metod (fonksiyon)
    def stok_ekle(self, miktar):
        self.stok += miktar
    
    def stok_azalt(self, miktar):
        if self.stok >= miktar:
            self.stok -= miktar
            return True
        return False

# Nesne oluşturma
laptop = Urun("Laptop", 5000)
laptop.stok_ekle(10)
print(laptop.stok)  # 10
```

**Projede Kullanım:**
```python
# stok/models.py içinde
class Urun(models.Model):
    ad = models.CharField(max_length=200)
    fiyat = models.DecimalField(max_digits=10, decimal_places=2)
    
    @property
    def mevcut_stok(self):
        """Property: Hesaplanan değer"""
        giris = StokHareketi.objects.filter(
            urun=self, islem_turu='giriş'
        ).aggregate(toplam=Sum('miktar'))['toplam'] or 0
        
        cikis = StokHareketi.objects.filter(
            urun=self, islem_turu='çıkış'
        ).aggregate(toplam=Sum('miktar'))['toplam'] or 0
        
        return giris - cikis

# Kullanım
urun = Urun.objects.get(pk=1)
print(urun.mevcut_stok)  # Property otomatik hesaplanır
```

---

### 8. MODÜLLER ve IMPORT

Kodları organize etmek için:

```python
# math modülünü import et
import math
print(math.sqrt(16))  # 4.0

# Belirli fonksiyonu import et
from math import sqrt
print(sqrt(16))  # 4.0

# Takma isim (alias) ile import
import math as m
print(m.sqrt(16))

# Birden fazla import
from django.shortcuts import render, redirect, get_object_or_404
```

**Projede Kullanım:**
```python
# fatura/views.py başında
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Fatura, FaturaKalem
from stok.models import Urun
```

---

### 9. HATA YÖNETİMİ (Exception Handling)

Hataları yakalayıp yönetmek için:

```python
# Try-Except
try:
    sayi = int("123")
    sonuc = 10 / sayi
    print(sonuc)
except ValueError:
    print("Geçersiz sayı!")
except ZeroDivisionError:
    print("Sıfıra bölünemez!")
except Exception as e:
    print(f"Beklenmeyen hata: {e}")

# Try-Except-Finally
try:
    dosya = open("dosya.txt", "r")
    icerik = dosya.read()
except FileNotFoundError:
    print("Dosya bulunamadı!")
finally:
    dosya.close()  # Her zaman çalışır
```

**Projede Kullanım:**
```python
# fatura/views.py içinde
try:
    urun_id = int(kalem_data['urun_id'])
    urun = Urun.objects.get(pk=urun_id)
except ValueError:
    logger.error("Geçersiz ürün ID")
    continue
except Urun.DoesNotExist:
    logger.error("Ürün bulunamadı")
    continue
except Exception as e:
    logger.error(f"Beklenmeyen hata: {e}")
    raise
```

---

### 10. LİSTE İŞLEMLERİ (List Operations)

```python
# Liste oluşturma
liste = [1, 2, 3, 4, 5]

# Eleman ekleme
liste.append(6)  # [1, 2, 3, 4, 5, 6]

# Eleman silme
liste.remove(3)  # [1, 2, 4, 5, 6]

# İndeks ile erişim
print(liste[0])   # İlk eleman: 1
print(liste[-1])  # Son eleman: 6

# Dilimleme (slicing)
print(liste[1:3])  # [2, 4] (1. ve 2. indeks)

# List comprehension (liste üretimi)
kareler = [x**2 for x in range(5)]  # [0, 1, 4, 9, 16]
ciftler = [x for x in range(10) if x % 2 == 0]  # [0, 2, 4, 6, 8]
```

**Projede Kullanım:**
```python
# fatura/views.py içinde
urun_ids = request.POST.getlist('urun_id[]')  # Liste al
miktarlar = request.POST.getlist('miktar[]')

# Liste üzerinde döngü
for i in range(len(urun_ids)):
    urun_id = urun_ids[i]
    miktar = miktarlar[i]
    # İşlem yap
```

---

### 11. DICTIONARY (Sözlük) İŞLEMLERİ

```python
# Dictionary oluşturma
kisi = {
    "ad": "Ahmet",
    "yas": 25,
    "sehir": "İstanbul"
}

# Değer erişim
print(kisi["ad"])      # "Ahmet"
print(kisi.get("ad"))  # "Ahmet" (güvenli erişim)

# Değer ekleme/güncelleme
kisi["email"] = "ahmet@example.com"
kisi["yas"] = 26

# Tüm anahtarlar
print(kisi.keys())    # dict_keys(['ad', 'yas', 'sehir', 'email'])

# Tüm değerler
print(kisi.values())  # dict_values(['Ahmet', 26, 'İstanbul', '...'])

# Tüm çiftler
print(kisi.items())   # dict_items([('ad', 'Ahmet'), ...])
```

**Projede Kullanım:**
```python
# fatura/views.py içinde
context = {
    'faturalar': faturalar,
    'search_query': search_query,
    'durum_filter': durum_filter,
    'table_html': table_html
}
return render(request, 'fatura/index.html', context)
```

---

### 12. STRING İŞLEMLERİ

```python
# String birleştirme
ad = "Ahmet"
soyad = "Yılmaz"
tam_ad = ad + " " + soyad  # "Ahmet Yılmaz"

# f-string (format string) - Modern yöntem
tam_ad = f"{ad} {soyad}"  # "Ahmet Yılmaz"
yas = 25
mesaj = f"{ad} {yas} yaşında"  # "Ahmet 25 yaşında"

# String metodları
metin = "  Merhaba Dünya  "
metin.strip()        # "Merhaba Dünya" (başta/sonda boşluk sil)
metin.upper()         # "  MERHABA DÜNYA  " (büyük harf)
metin.lower()         # "  merhaba dünya  " (küçük harf)
metin.replace("a", "A")  # "  MerhAbA DünyA  "

# String kontrol
"a" in metin         # True (içinde var mı?)
metin.startswith("M")  # False
metin.endswith("a")    # True
```

**Projede Kullanım:**
```python
# fatura/views.py içinde
fatura_no = f"SATIS-{yil}{ay:02d}{gun:02d}-{no:03d}"
# Örnek: "SATIS-20241201-001"

# stoktakip/security_utils.py içinde
cleaned = value.strip()  # Boşlukları temizle
cleaned = cleaned.replace('\x00', '')  # Null byte kaldır
```

---

## 🎯 DJANGO FRAMEWORK NEDİR?

Django, Python ile web uygulamaları geliştirmek için kullanılan bir framework'tür (çerçeve).

### Django'nun Avantajları:
- ✅ Hızlı geliştirme
- ✅ Güvenlik (SQL injection, XSS koruması)
- ✅ Admin paneli (otomatik)
- ✅ ORM (Veritabanı işlemleri kolay)
- ✅ URL routing
- ✅ Template sistemi

### Django Yapısı:
```
Django Projesi
├── Models (Veritabanı tabloları)
├── Views (İş mantığı)
├── Templates (HTML sayfaları)
├── URLs (URL yönlendirme)
└── Settings (Ayarlar)
```

---

## 📁 PROJE YAPISINI ANLAMA

### 1. MODELS (Modeller) - Veritabanı Tabloları

Model, veritabanındaki bir tabloyu temsil eder:

```python
# stok/models.py
from django.db import models

class Urun(models.Model):
    # CharField: Metin alanı (max uzunluk belirtilir)
    ad = models.CharField(max_length=200, verbose_name="Ürün Adı")
    
    # DecimalField: Ondalıklı sayı (toplam basamak, ondalık basamak)
    fiyat = models.DecimalField(
        max_digits=10,      # Toplam 10 basamak
        decimal_places=2,   # 2 ondalık basamak
        verbose_name="Satış Fiyatı"
    )
    
    # IntegerField: Tam sayı
    min_stok_adedi = models.IntegerField(default=0)
    
    # ForeignKey: Başka bir tabloya bağlantı
    kategori = models.ForeignKey(
        Kategori,           # Bağlanacak model
        on_delete=models.SET_NULL,  # Silinirse NULL yap
        null=True,          # Boş olabilir
        blank=True          # Form'da boş bırakılabilir
    )
    
    # DateTimeField: Tarih ve saat
    olusturma_tarihi = models.DateTimeField(
        auto_now_add=True   # Oluşturulduğunda otomatik doldur
    )
```

**Açıklama:**
- `models.Model`: Django model sınıfından türetilir
- `verbose_name`: Admin panelinde görünen isim
- `max_length`: Maksimum karakter sayısı
- `default`: Varsayılan değer
- `null=True`: Veritabanında NULL olabilir
- `blank=True`: Form'da boş bırakılabilir
- `on_delete`: İlişkili kayıt silinince ne olacak?

---

### 2. VIEWS (Görünümler) - İş Mantığı

View, kullanıcı isteğine cevap veren fonksiyonlardır:

```python
# fatura/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required  # Decorator: Sadece giriş yapmış kullanıcılar
def fatura_listesi(request):
    """
    Fatura listesini gösterir
    
    request: Kullanıcının isteği (GET parametreleri, POST verileri)
    """
    # Veritabanından faturaları al
    faturalar = Fatura.objects.all()
    
    # Arama yapılmışsa filtrele
    arama = request.GET.get('search', '')  # GET parametresini al
    if arama:
        faturalar = faturalar.filter(fatura_no__icontains=arama)
    
    # HTML sayfasını render et (göster)
    context = {
        'faturalar': faturalar,
        'arama': arama
    }
    return render(request, 'fatura/index.html', context)
```

**Açıklama:**
- `request`: Kullanıcının isteği (GET, POST, kullanıcı bilgisi)
- `request.GET`: URL'deki parametreler (?search=test)
- `request.POST`: Form gönderilen veriler
- `render()`: HTML sayfasını gösterir
- `redirect()`: Başka bir sayfaya yönlendirir

---

### 3. URLS (URL Yönlendirme)

URL, hangi view'ın çalışacağını belirler:

```python
# fatura/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # path('URL', view_fonksiyonu, name='isim')
    path('', views.index, name='index'),
    # '' = /fatura/ (boş URL)
    
    path('ekle/', views.fatura_ekle, name='ekle'),
    # 'ekle/' = /fatura/ekle/
    
    path('<int:pk>/', views.fatura_detay, name='detay'),
    # '<int:pk>/' = /fatura/1/ (pk=1)
    # int:pk = URL'deki sayıyı pk değişkenine al
]
```

**Açıklama:**
- `path()`: URL pattern tanımlar
- `name`: URL'ye isim verir (reverse için)
- `<int:pk>`: URL'deki sayıyı `pk` değişkenine alır

---

### 4. TEMPLATES (Şablonlar) - HTML Sayfaları

Template, HTML sayfalarıdır (Django template dili ile):

```html
<!-- templates/fatura/index.html -->
{% extends "base.html" %}  <!-- base.html'i genişlet -->

{% block content %}  <!-- content bloğunu doldur -->
<h1>Fatura Listesi</h1>

<!-- Arama formu -->
<form method="get">
    <input type="text" name="search" value="{{ search_query }}">
    <button type="submit">Ara</button>
</form>

<!-- Fatura listesi -->
<table>
    {% for fatura in faturalar %}
    <tr>
        <td>{{ fatura.fatura_no }}</td>
        <td>{{ fatura.fatura_tarihi }}</td>
        <td>{{ fatura.genel_toplam }} ₺</td>
    </tr>
    {% endfor %}
</table>
{% endblock %}
```

**Django Template Etiketleri:**
- `{% extends %}`: Başka template'i genişletir
- `{% block %}`: İçerik bloğu tanımlar
- `{% for %}`: Döngü
- `{% if %}`: Koşul
- `{{ variable }}`: Değişken değerini gösterir

---

### 5. FORMS (Formlar)

Form, kullanıcıdan veri almak için:

```python
# fatura/forms.py
from django import forms
from .models import Fatura

class FaturaForm(forms.ModelForm):
    class Meta:
        model = Fatura
        fields = ['cari', 'fatura_tarihi', 'fatura_tipi', 'durum']
        # Model'den otomatik form oluşturur
    
    # Özel validasyon
    def clean_fatura_tarihi(self):
        tarih = self.cleaned_data['fatura_tarihi']
        if tarih > timezone.now().date():
            raise forms.ValidationError("Gelecek tarih seçilemez!")
        return tarih
```

**Kullanım:**
```python
# View'da
if request.method == 'POST':
    form = FaturaForm(request.POST)
    if form.is_valid():
        fatura = form.save()  # Kaydet
        return redirect('fatura:detay', pk=fatura.pk)
else:
    form = FaturaForm()  # Boş form göster
```

---

## 🎨 DECORATOR (Süsleyici) NEDİR?

Decorator, bir fonksiyonu "süsleyen" özel bir yapıdır. Fonksiyonun üzerine eklenir ve ek özellikler katar.

### Basit Decorator Örneği:

```python
# Decorator tanımlama
def zaman_olc(func):
    """Fonksiyonun çalışma süresini ölçer"""
    def wrapper(*args, **kwargs):
        import time
        baslangic = time.time()
        sonuc = func(*args, **kwargs)
        bitis = time.time()
        print(f"{func.__name__} {bitis - baslangic:.2f} saniye sürdü")
        return sonuc
    return wrapper

# Decorator kullanımı
@zaman_olc
def yavas_fonksiyon():
    import time
    time.sleep(2)  # 2 saniye bekle
    return "Tamamlandı"

yavas_fonksiyon()  # "yavas_fonksiyon 2.00 saniye sürdü" yazdırır
```

### Projede Kullanılan Decorator'lar:

#### 1. `@login_required`
**Ne yapar?** Sadece giriş yapmış kullanıcılar erişebilir.

```python
from django.contrib.auth.decorators import login_required

@login_required
def gizli_sayfa(request):
    return render(request, 'gizli.html')

# Eğer kullanıcı giriş yapmamışsa, login sayfasına yönlendirir
```

#### 2. `@handle_view_errors`
**Ne yapar?** Hataları yakalar, loglar ve kullanıcıya mesaj gösterir.

```python
@handle_view_errors(
    error_message="Fatura oluşturulamadı",
    redirect_url="fatura:index"
)
def fatura_ekle(request):
    # Eğer hata olursa:
    # 1. Hata loglanır
    # 2. Kullanıcıya "Fatura oluşturulamadı" mesajı gösterilir
    # 3. fatura:index sayfasına yönlendirilir
    pass
```

**Nasıl Çalışır?**
```python
def handle_view_errors(error_message="Hata oluştu", redirect_url=None):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            try:
                return view_func(request, *args, **kwargs)  # Normal çalıştır
            except Exception as e:
                # Hata yakalandı
                logger.error(f"Hata: {e}")  # Logla
                messages.error(request, error_message)  # Mesaj göster
                if redirect_url:
                    return redirect(redirect_url)  # Yönlendir
        return wrapper
    return decorator
```

#### 3. `@cache_view_result`
**Ne yapar?** View sonucunu cache'ler (hızlandırır).

```python
@cache_view_result(timeout=300, key_prefix='fatura_index')
def index(request):
    # İlk çağrıda normal çalışır
    # Sonraki çağrılarda cache'den döner (5 dakika)
    pass
```

**Nasıl Çalışır?**
```python
def cache_view_result(timeout=300):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            cache_key = f"{view_func.__name__}_{request.user.id}"
            
            # Cache'den oku
            cached = cache.get(cache_key)
            if cached:
                return cached  # Cache'den dön
            
            # Yoksa çalıştır ve cache'e kaydet
            result = view_func(request, *args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator
```

#### 4. `@database_transaction`
**Ne yapar?** Veritabanı işlemlerini güvenli yapar.

```python
@database_transaction
def fatura_ekle(request):
    with transaction.atomic():  # Tüm işlemler birlikte
        fatura = Fatura.objects.create(...)
        FaturaKalem.objects.create(...)
        # Eğer hata olursa, hiçbiri kaydedilmez (rollback)
```

---

## 🔍 PROJE ÖZELLİKLERİ DETAYLI

### 1. STOK YÖNETİMİ

#### Ürün Ekleme:
```python
# stok/views.py
def urun_ekle(request):
    if request.method == 'POST':
        # Form gönderildi
        form = UrunForm(request.POST, request.FILES)
        if form.is_valid():
            urun = form.save()  # Kaydet
            messages.success(request, 'Ürün eklendi!')
            return redirect('stok:index')
    else:
        # Form göster
        form = UrunForm()
    
    return render(request, 'stok/urun_form.html', {'form': form})
```

**Adım Adım:**
1. Kullanıcı formu doldurur
2. `POST` isteği gönderilir
3. Form validate edilir
4. Geçerliyse kaydedilir
5. Başarı mesajı gösterilir
6. Liste sayfasına yönlendirilir

#### Stok Hesaplama:
```python
# stok/models.py
class Urun(models.Model):
    @property
    def mevcut_stok(self):
        """Property: Her çağrıldığında hesaplanır"""
        # Giriş toplamı
        giris = StokHareketi.objects.filter(
            urun=self,
            islem_turu='giriş'
        ).aggregate(toplam=Sum('miktar'))['toplam'] or 0
        
        # Çıkış toplamı
        cikis = StokHareketi.objects.filter(
            urun=self,
            islem_turu='çıkış'
        ).aggregate(toplam=Sum('miktar'))['toplam'] or 0
        
        return giris - cikis  # Mevcut stok
```

**Açıklama:**
- `@property`: Metod gibi çağrılır ama değişken gibi kullanılır
- `filter()`: Veritabanında filtreleme yapar
- `aggregate()`: Toplam, ortalama gibi hesaplamalar
- `Sum()`: Toplam alır

---

### 2. FATURA YÖNETİMİ

#### Fatura Oluşturma:
```python
# fatura/views.py
@database_transaction
@login_required
def fatura_ekle(request):
    if request.method == 'POST':
        # Fatura formu
        fatura_form = FaturaForm(request.POST)
        if fatura_form.is_valid():
            with transaction.atomic():  # Tüm işlemler birlikte
                # Fatura oluştur
                fatura = fatura_form.save(commit=False)
                fatura.olusturan = request.user
                fatura.save()
                
                # Kalemleri ekle
                urun_ids = request.POST.getlist('urun_id[]')
                miktarlar = request.POST.getlist('miktar[]')
                
                for i in range(len(urun_ids)):
                    urun = Urun.objects.get(pk=urun_ids[i])
                    miktar = int(miktarlar[i])
                    
                    # Kalem oluştur
                    FaturaKalem.objects.create(
                        fatura=fatura,
                        urun=urun,
                        miktar=miktar,
                        birim_fiyat=urun.fiyat
                    )
                
                # Toplamları hesapla
                fatura.hesapla_toplamlar()
                
                return redirect('fatura:detay', pk=fatura.pk)
```

**Adım Adım:**
1. Form validate edilir
2. Fatura oluşturulur
3. Her ürün için kalem eklenir
4. Toplamlar hesaplanır
5. Detay sayfasına yönlendirilir

**Transaction (İşlem) Nedir?**
- Tüm işlemler birlikte yapılır
- Eğer birinde hata olursa, hiçbiri kaydedilmez
- Veri tutarlılığını sağlar

#### Fatura Numarası Oluşturma:
```python
# fatura/models.py
def olustur_fatura_no(self):
    prefix = 'SATIS' if self.fatura_tipi == 'Satis' else 'ALIS'
    yil = self.fatura_tarihi.year
    ay = self.fatura_tarihi.month
    gun = self.fatura_tarihi.day
    
    tarih_str = f"{yil}{ay:02d}{gun:02d}"  # 20241201
    arama_pattern = f"{prefix}-{tarih_str}-"  # SATIS-20241201-
    
    # Aynı günkü son faturayı bul
    son_fatura = Fatura.objects.filter(
        fatura_no__startswith=arama_pattern
    ).aggregate(Max('fatura_no'))
    
    if son_fatura['fatura_no__max']:
        son_no = int(son_fatura['fatura_no__max'].split('-')[-1])
        yeni_no = son_no + 1
    else:
        yeni_no = 1
    
    return f"{prefix}-{tarih_str}-{yeni_no:03d}"  # SATIS-20241201-001
```

**Açıklama:**
- `f"{ay:02d}"`: 2 haneli sayı (01, 02, ..., 12)
- `f"{yeni_no:03d}"`: 3 haneli sayı (001, 002, ..., 999)
- `startswith()`: Başlangıç kontrolü
- `split('-')`: Tire ile ayır

---

### 3. CARİ HESAP YÖNETİMİ

#### Bakiye Hesaplama:
```python
# cari/models.py
class Cari(models.Model):
    @property
    def bakiye(self):
        """Cari hesap bakiyesi"""
        # Borç toplamı (bize borçlu)
        borc_toplam = CariHareketi.objects.filter(
            cari=self,
            hareket_turu__in=['satis_faturasi', 'odeme']
        ).aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0.00')
        
        # Alacak toplamı (biz ona borçluyuz)
        alacak_toplam = CariHareketi.objects.filter(
            cari=self,
            hareket_turu__in=['alis_faturasi', 'tahsilat']
        ).aggregate(toplam=Sum('tutar'))['toplam'] or Decimal('0.00')
        
        # Bakiye = Alacak - Borç
        # Pozitif: Biz ona borçluyuz
        # Negatif: O bize borçlu
        return alacak_toplam - borc_toplam
```

**Mantık:**
- Satış faturası → Müşteri bize borçlu (BORÇ)
- Alış faturası → Biz tedarikçiye borçluyuz (ALACAK)
- Tahsilat → Müşteriden para aldık (ALACAK azalır)
- Ödeme → Tedarikçiye para ödedik (BORÇ azalır)

---

### 4. API ENDPOINT'LERİ

#### REST API Nedir?
REST (Representational State Transfer), web servisleri için bir standarttır.

**HTTP Metodları:**
- `GET`: Veri okuma (liste, detay)
- `POST`: Yeni kayıt oluşturma
- `PUT`: Tüm kaydı güncelleme
- `PATCH`: Kısmi güncelleme
- `DELETE`: Kayıt silme

#### API Örneği:
```python
# api/views.py
from rest_framework import viewsets
from .serializers import UrunSerializer

class UrunViewSet(viewsets.ModelViewSet):
    queryset = Urun.objects.all()
    serializer_class = UrunSerializer
    permission_classes = [IsAdminOrDepo]
    
    def get_queryset(self):
        queryset = Urun.objects.all()
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(ad__icontains=search)
        return queryset
```

**Kullanım:**
```bash
# Liste
GET /api/v1/urunler/

# Arama
GET /api/v1/urunler/?search=laptop

# Detay
GET /api/v1/urunler/1/

# Yeni kayıt
POST /api/v1/urunler/
{
    "ad": "Laptop",
    "fiyat": 5000
}

# Güncelle
PUT /api/v1/urunler/1/
{
    "ad": "Güncellenmiş Laptop",
    "fiyat": 4500
}

# Sil
DELETE /api/v1/urunler/1/
```

---

### 5. GÜVENLİK ve VALİDASYON

#### Input Sanitization (Girdi Temizleme):
```python
# stoktakip/security_utils.py
def sanitize_string(value, max_length=None):
    """String input'u temizler"""
    if not isinstance(value, str):
        raise ValidationError("Input must be a string")
    
    # Başta ve sonda boşlukları temizle
    cleaned = value.strip()
    
    # Null byte karakterlerini kaldır (zararlı)
    cleaned = cleaned.replace('\x00', '')
    
    # Maksimum uzunluk kontrolü
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    
    return cleaned
```

**Neden Önemli?**
- SQL Injection: Kötü niyetli SQL kodu enjekte etme
- XSS (Cross-Site Scripting): Zararlı JavaScript kodu
- Buffer Overflow: Veri taşması

#### Validasyon Örneği:
```python
# cari/models.py
def clean(self):
    """Model-level validation"""
    errors = {}
    
    # Risk limiti kontrolü
    if self.risk_limiti < 0:
        errors['risk_limiti'] = 'Risk limiti negatif olamaz.'
    
    # TC/VKN format kontrolü
    if self.tc_vkn:
        tc_vkn_clean = self.tc_vkn.replace('-', '').replace(' ', '')
        if not (len(tc_vkn_clean) == 11 or len(tc_vkn_clean) == 10):
            errors['tc_vkn'] = 'TC/VKN 11 (TC) veya 10 (VKN) karakter olmalıdır.'
    
    if errors:
        raise ValidationError(errors)
```

---

### 6. CACHE (Önbellek) SİSTEMİ

#### Cache Nedir?
Sık kullanılan verileri hafızada tutarak hızlandırma.

**Örnek:**
```python
# Cache olmadan (her seferinde veritabanından çeker)
def dashboard(request):
    faturalar = Fatura.objects.all()  # Veritabanı sorgusu
    return render(request, 'dashboard.html', {'faturalar': faturalar})

# Cache ile (ilk seferinde veritabanından, sonra cache'den)
@cache_view_result(timeout=300)
def dashboard(request):
    faturalar = Fatura.objects.all()
    return render(request, 'dashboard.html', {'faturalar': faturalar})
```

**Nasıl Çalışır?**
1. İlk çağrı: Veritabanından çeker, cache'e kaydeder
2. Sonraki çağrılar (5 dakika): Cache'den döner (hızlı!)
3. 5 dakika sonra: Cache silinir, tekrar veritabanından çeker

---

## 📚 ADIM ADIM ÖĞRENME REHBERİ

### 1. ADIM: Python Temelleri
- ✅ Değişkenler ve veri tipleri
- ✅ Operatörler
- ✅ Koşullu ifadeler (if-else)
- ✅ Döngüler (for, while)
- ✅ Fonksiyonlar

### 2. ADIM: Python İleri Seviye
- ✅ Class ve Object
- ✅ Modüller ve Import
- ✅ Hata yönetimi (try-except)
- ✅ Liste ve Dictionary işlemleri

### 3. ADIM: Django Temelleri
- ✅ Django nedir?
- ✅ Model, View, Template kavramları
- ✅ URL routing
- ✅ Form işlemleri

### 4. ADIM: Projeyi Anlama
- ✅ Proje yapısını incele
- ✅ Modelleri oku
- ✅ View'ları incele
- ✅ Template'leri incele

### 5. ADIM: Kod Okuma
- ✅ Basit view'lardan başla
- ✅ Decorator'ları anla
- ✅ API endpoint'lerini incele
- ✅ Hata yönetimini öğren

### 6. ADIM: Kod Yazma
- ✅ Basit view yaz
- ✅ Form oluştur
- ✅ Model ekle
- ✅ Test et

---

## 💡 ÖNEMLİ KAVRAMLAR

### 1. ORM (Object-Relational Mapping)
Veritabanı işlemlerini Python objeleri ile yapma:

```python
# SQL yerine Python kodu
# SQL: SELECT * FROM stok_urun WHERE ad LIKE '%laptop%';
urunler = Urun.objects.filter(ad__icontains='laptop')

# SQL: INSERT INTO stok_urun (ad, fiyat) VALUES ('Laptop', 5000);
urun = Urun.objects.create(ad='Laptop', fiyat=5000)

# SQL: UPDATE stok_urun SET fiyat=4500 WHERE id=1;
urun = Urun.objects.get(pk=1)
urun.fiyat = 4500
urun.save()

# SQL: DELETE FROM stok_urun WHERE id=1;
urun.delete()
```

### 2. QuerySet
Veritabanı sorgusu sonucu:

```python
# Tüm ürünler
urunler = Urun.objects.all()

# Filtreleme
urunler = Urun.objects.filter(fiyat__gte=100)  # Fiyat >= 100

# Sıralama
urunler = Urun.objects.all().order_by('ad')  # Ada göre sırala

# İlk kayıt
urun = Urun.objects.first()

# Belirli kayıt
urun = Urun.objects.get(pk=1)  # ID=1 olan ürün
```

### 3. ForeignKey (Yabancı Anahtar)
İki tablo arasında ilişki:

```python
# Urun, Kategori'ye bağlı
class Urun(models.Model):
    kategori = models.ForeignKey(Kategori, on_delete=models.CASCADE)

# Kullanım
urun = Urun.objects.get(pk=1)
print(urun.kategori.ad)  # Kategori adını yazdır

kategori = Kategori.objects.get(pk=1)
print(kategori.urun_set.all())  # Bu kategoriye ait tüm ürünler
```

### 4. Property (Özellik)
Hesaplanan değer:

```python
class Urun(models.Model):
    @property
    def mevcut_stok(self):
        # Her çağrıldığında hesaplanır
        return giris - cikis

# Kullanım (değişken gibi)
urun = Urun.objects.get(pk=1)
print(urun.mevcut_stok)  # Property otomatik hesaplanır
```

---

## 🎓 ÖĞRENME İPUÇLARI

1. **Küçük Adımlarla Başla**: Önce basit kodları oku, sonra karmaşık olanlara geç
2. **Kod Yaz, Test Et**: Öğrendiğin her şeyi uygula
3. **Hata Yap, Öğren**: Hatalardan öğrenmek en iyi yöntem
4. **Dokümantasyon Oku**: Django ve Python dokümantasyonunu oku
5. **Projeyi İncele**: Mevcut kodu okuyarak öğren
6. **Soru Sor**: Anlamadığın yerleri sor

---

## 📖 SONUÇ

Bu dokümantasyon ile:
- ✅ Python temellerini öğrendin
- ✅ Django framework'ü anladın
- ✅ Proje yapısını kavradın
- ✅ Kod örneklerini gördün
- ✅ Önemli kavramları öğrendin

**Sıradaki Adımlar:**
1. Python temellerini pratik yap
2. Django tutorial'ını tamamla
3. Projeyi adım adım incele
4. Basit özellikler ekle
5. Kendi projelerini yap

**Başarılar! 🚀**

---

**Son Güncelleme:** 2024
**Versiyon:** 1.0.0 - Eğitim Versiyonu

