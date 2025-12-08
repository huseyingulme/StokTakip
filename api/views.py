from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from stok.models import Urun, StokHareketi, Kategori
from cari.models import Cari, CariHareketi
from fatura.models import Fatura, FaturaKalem
from .serializers import (
    KategoriSerializer, UrunSerializer, StokHareketiSerializer,
    CariSerializer, CariHareketiSerializer, FaturaSerializer, FaturaKalemSerializer
)
from accounts.utils import log_action


class KategoriViewSet(viewsets.ModelViewSet):
    queryset = Kategori.objects.all()
    serializer_class = KategoriSerializer
    permission_classes = [permissions.IsAuthenticated]


class UrunViewSet(viewsets.ModelViewSet):
    queryset = Urun.objects.select_related('kategori').all()
    serializer_class = UrunSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Urun.objects.select_related('kategori').all()
        search = self.request.query_params.get('search', None)
        kategori = self.request.query_params.get('kategori', None)
        
        if search:
            queryset = queryset.filter(ad__icontains=search) | queryset.filter(barkod__icontains=search)
        if kategori:
            queryset = queryset.filter(kategori_id=kategori)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def hareketler(self, request, pk=None):
        urun = self.get_object()
        hareketler = StokHareketi.objects.filter(urun=urun).order_by('-tarih')
        serializer = StokHareketiSerializer(hareketler, many=True)
        return Response(serializer.data)


class StokHareketiViewSet(viewsets.ModelViewSet):
    queryset = StokHareketi.objects.select_related('urun', 'olusturan').all()
    serializer_class = StokHareketiSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        hareket = serializer.save(olusturan=self.request.user)
        log_action(self.request.user, 'create', hareket, f'Stok hareketi oluşturuldu: {hareket.urun.ad}')


class CariViewSet(viewsets.ModelViewSet):
    queryset = Cari.objects.filter(durum='aktif')
    serializer_class = CariSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Cari.objects.filter(durum='aktif')
        search = self.request.query_params.get('search', None)
        kategori = self.request.query_params.get('kategori', None)
        
        if search:
            queryset = queryset.filter(ad_soyad__icontains=search)
        if kategori:
            queryset = queryset.filter(kategori=kategori)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def hareketler(self, request, pk=None):
        cari = self.get_object()
        hareketler = cari.hareketler.all().order_by('-tarih')
        serializer = CariHareketiSerializer(hareketler, many=True)
        return Response(serializer.data)


class CariHareketiViewSet(viewsets.ModelViewSet):
    queryset = CariHareketi.objects.select_related('cari', 'olusturan').all()
    serializer_class = CariHareketiSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        hareket = serializer.save(olusturan=self.request.user)
        log_action(self.request.user, 'create', hareket, f'Cari hareketi oluşturuldu: {hareket.cari.ad_soyad}')


class FaturaViewSet(viewsets.ModelViewSet):
    queryset = Fatura.objects.select_related('cari', 'olusturan').prefetch_related('kalemler').all()
    serializer_class = FaturaSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Fatura.objects.select_related('cari', 'olusturan').prefetch_related('kalemler').all()
        tip = self.request.query_params.get('tip', None)
        durum = self.request.query_params.get('durum', None)
        
        if tip:
            queryset = queryset.filter(fatura_tipi=tip)
        if durum:
            queryset = queryset.filter(durum=durum)
        
        return queryset
    
    def perform_create(self, serializer):
        fatura = serializer.save(olusturan=self.request.user)
        log_action(self.request.user, 'create', fatura, f'Fatura oluşturuldu: {fatura.fatura_no}')

