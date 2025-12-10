from rest_framework import serializers
from stok.models import Urun, StokHareketi, Kategori
from cari.models import Cari, CariHareketi
from fatura.models import Fatura, FaturaKalem


class KategoriSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kategori
        fields = ['id', 'ad', 'aciklama', 'olusturma_tarihi']


class UrunSerializer(serializers.ModelSerializer):
    kategori_adi = serializers.CharField(source='kategori.ad', read_only=True)
    mevcut_stok = serializers.ReadOnlyField()
    
    class Meta:
        model = Urun
        fields = ['id', 'kategori', 'kategori_adi', 'ad', 'barkod', 'birim', 'fiyat', 
                  'mevcut_stok', 'olusturma_tarihi']
        read_only_fields = ['min_stok_adedi']  # Her zaman 0


class StokHareketiSerializer(serializers.ModelSerializer):
    urun_adi = serializers.CharField(source='urun.ad', read_only=True)
    kullanici = serializers.CharField(source='olusturan.username', read_only=True)
    
    class Meta:
        model = StokHareketi
        fields = ['id', 'urun', 'urun_adi', 'islem_turu', 'miktar', 'aciklama', 
                  'tarih', 'kullanici']


class CariSerializer(serializers.ModelSerializer):
    bakiye = serializers.ReadOnlyField()
    
    class Meta:
        model = Cari
        fields = ['id', 'ad_soyad', 'vergi_dairesi', 'vergi_no', 'tc_vkn', 'telefon', 
                  'email', 'adres', 'sehir', 'ilce', 'kategori', 'durum', 'risk_limiti', 
                  'bakiye', 'olusturma_tarihi']


class CariHareketiSerializer(serializers.ModelSerializer):
    cari_adi = serializers.CharField(source='cari.ad_soyad', read_only=True)
    
    class Meta:
        model = CariHareketi
        fields = ['id', 'cari', 'cari_adi', 'hareket_turu', 'tutar', 'aciklama', 
                  'belge_no', 'tarih', 'odeme_yontemi']


class FaturaKalemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaturaKalem
        fields = ['id', 'urun', 'urun_adi', 'miktar', 'birim_fiyat', 'kdv_orani', 
                  'kdv_tutari', 'toplam_tutar', 'sira_no']


class FaturaSerializer(serializers.ModelSerializer):
    cari_adi = serializers.CharField(source='cari.ad_soyad', read_only=True)
    kalemler = FaturaKalemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Fatura
        fields = ['id', 'fatura_no', 'cari', 'cari_adi', 'fatura_tarihi', 
                  'toplam_tutar', 'kdv_tutari', 'genel_toplam', 'fatura_tipi', 'durum', 
                  'aciklama', 'kalemler', 'olusturma_tarihi']

