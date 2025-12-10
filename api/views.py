from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied
from stok.models import Urun, StokHareketi, Kategori
from cari.models import Cari, CariHareketi
from fatura.models import Fatura, FaturaKalem
from .serializers import (
    KategoriSerializer, UrunSerializer, StokHareketiSerializer,
    CariSerializer, CariHareketiSerializer, FaturaSerializer, FaturaKalemSerializer
)
from accounts.utils import log_action
from stoktakip.error_handling import handle_api_errors
from stoktakip.security_utils import sanitize_string, sanitize_integer, validate_search_query
from .permissions import (
    IsAdminOrDepo, IsAdminOrMuhasebe, IsAdminOrSatis, IsAdminOnly
)
import logging

logger = logging.getLogger(__name__)


class KategoriViewSet(viewsets.ModelViewSet):
    queryset = Kategori.objects.all()
    serializer_class = KategoriSerializer
    permission_classes = [IsAdminOrDepo]
    
    @handle_api_errors
    def list(self, request, *args, **kwargs):
        """List all categories with input validation."""
        return super().list(request, *args, **kwargs)
    
    @handle_api_errors
    def create(self, request, *args, **kwargs):
        """Create a new category with input validation."""
        return super().create(request, *args, **kwargs)
    
    @handle_api_errors
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a category with input validation."""
        return super().retrieve(request, *args, **kwargs)
    
    @handle_api_errors
    def update(self, request, *args, **kwargs):
        """Update a category with input validation."""
        return super().update(request, *args, **kwargs)
    
    @handle_api_errors
    def destroy(self, request, *args, **kwargs):
        """Delete a category with input validation."""
        return super().destroy(request, *args, **kwargs)


class UrunViewSet(viewsets.ModelViewSet):
    queryset = Urun.objects.select_related('kategori').all()
    serializer_class = UrunSerializer
    permission_classes = [IsAdminOrDepo]
    
    def get_queryset(self):
        queryset = Urun.objects.select_related('kategori').all()
        search = self.request.query_params.get('search', None)
        kategori = self.request.query_params.get('kategori', None)
        
        # Input validation
        if search:
            try:
                search = validate_search_query(search)
                queryset = queryset.filter(ad__icontains=search) | queryset.filter(barkod__icontains=search)
            except Exception as e:
                logger.warning(f"Invalid search query: {str(e)}")
        
        if kategori:
            try:
                kategori = sanitize_integer(kategori, min_value=1)
                queryset = queryset.filter(kategori_id=kategori)
            except Exception as e:
                logger.warning(f"Invalid kategori ID: {str(e)}")
        
        return queryset
    
    @handle_api_errors
    def list(self, request, *args, **kwargs):
        """List all products with input validation."""
        return super().list(request, *args, **kwargs)
    
    @handle_api_errors
    def create(self, request, *args, **kwargs):
        """Create a new product with input validation."""
        return super().create(request, *args, **kwargs)
    
    @handle_api_errors
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a product with input validation."""
        return super().retrieve(request, *args, **kwargs)
    
    @handle_api_errors
    def update(self, request, *args, **kwargs):
        """Update a product with input validation."""
        return super().update(request, *args, **kwargs)
    
    @handle_api_errors
    def destroy(self, request, *args, **kwargs):
        """Delete a product with input validation."""
        return super().destroy(request, *args, **kwargs)
    
    @handle_api_errors
    @action(detail=True, methods=['get'])
    def hareketler(self, request, pk=None):
        """Get stock movements for a product with input validation."""
        urun = self.get_object()
        hareketler = StokHareketi.objects.filter(urun=urun).order_by('-tarih')
        serializer = StokHareketiSerializer(hareketler, many=True)
        return Response(serializer.data)


class StokHareketiViewSet(viewsets.ModelViewSet):
    queryset = StokHareketi.objects.select_related('urun', 'olusturan').all()
    serializer_class = StokHareketiSerializer
    permission_classes = [IsAdminOrDepo]
    
    @handle_api_errors
    def list(self, request, *args, **kwargs):
        """List all stock movements with input validation."""
        return super().list(request, *args, **kwargs)
    
    @handle_api_errors
    def create(self, request, *args, **kwargs):
        """Create a new stock movement with input validation."""
        return super().create(request, *args, **kwargs)
    
    @handle_api_errors
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a stock movement with input validation."""
        return super().retrieve(request, *args, **kwargs)
    
    @handle_api_errors
    def update(self, request, *args, **kwargs):
        """Update a stock movement with input validation."""
        return super().update(request, *args, **kwargs)
    
    @handle_api_errors
    def destroy(self, request, *args, **kwargs):
        """Delete a stock movement with input validation."""
        return super().destroy(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        hareket = serializer.save(olusturan=self.request.user)
        log_action(self.request.user, 'create', hareket, f'Stok hareketi oluşturuldu: {hareket.urun.ad}')


class CariViewSet(viewsets.ModelViewSet):
    queryset = Cari.objects.filter(durum='aktif')
    serializer_class = CariSerializer
    permission_classes = [IsAdminOrSatis]
    
    def get_queryset(self):
        queryset = Cari.objects.filter(durum='aktif')
        search = self.request.query_params.get('search', None)
        kategori = self.request.query_params.get('kategori', None)
        
        # Input validation
        if search:
            try:
                search = validate_search_query(search)
                queryset = queryset.filter(ad_soyad__icontains=search)
            except Exception as e:
                logger.warning(f"Invalid search query: {str(e)}")
        
        if kategori:
            try:
                kategori = sanitize_string(kategori)
                queryset = queryset.filter(kategori=kategori)
            except Exception as e:
                logger.warning(f"Invalid kategori: {str(e)}")
        
        return queryset
    
    @handle_api_errors
    def list(self, request, *args, **kwargs):
        """List all customers/suppliers with input validation."""
        return super().list(request, *args, **kwargs)
    
    @handle_api_errors
    def create(self, request, *args, **kwargs):
        """Create a new customer/supplier with input validation."""
        return super().create(request, *args, **kwargs)
    
    @handle_api_errors
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a customer/supplier with input validation."""
        return super().retrieve(request, *args, **kwargs)
    
    @handle_api_errors
    def update(self, request, *args, **kwargs):
        """Update a customer/supplier with input validation."""
        return super().update(request, *args, **kwargs)
    
    @handle_api_errors
    def destroy(self, request, *args, **kwargs):
        """Delete a customer/supplier with input validation."""
        return super().destroy(request, *args, **kwargs)
    
    @handle_api_errors
    @action(detail=True, methods=['get'])
    def hareketler(self, request, pk=None):
        """Get movements for a customer/supplier with input validation."""
        cari = self.get_object()
        hareketler = cari.hareketler.all().order_by('-tarih')
        serializer = CariHareketiSerializer(hareketler, many=True)
        return Response(serializer.data)


class CariHareketiViewSet(viewsets.ModelViewSet):
    queryset = CariHareketi.objects.select_related('cari', 'olusturan').all()
    serializer_class = CariHareketiSerializer
    permission_classes = [IsAdminOrMuhasebe]
    
    @handle_api_errors
    def list(self, request, *args, **kwargs):
        """List all customer movements with input validation."""
        return super().list(request, *args, **kwargs)
    
    @handle_api_errors
    def create(self, request, *args, **kwargs):
        """Create a new customer movement with input validation."""
        return super().create(request, *args, **kwargs)
    
    @handle_api_errors
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a customer movement with input validation."""
        return super().retrieve(request, *args, **kwargs)
    
    @handle_api_errors
    def update(self, request, *args, **kwargs):
        """Update a customer movement with input validation."""
        return super().update(request, *args, **kwargs)
    
    @handle_api_errors
    def destroy(self, request, *args, **kwargs):
        """Delete a customer movement with input validation."""
        return super().destroy(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        hareket = serializer.save(olusturan=self.request.user)
        log_action(self.request.user, 'create', hareket, f'Cari hareketi oluşturuldu: {hareket.cari.ad_soyad}')


class FaturaViewSet(viewsets.ModelViewSet):
    queryset = Fatura.objects.select_related('cari', 'olusturan').prefetch_related('kalemler').all()
    serializer_class = FaturaSerializer
    permission_classes = [IsAdminOrSatis]
    
    def get_permissions(self):
        """
        DELETE işlemi için sadece muhasebe/admin izni gerekli
        """
        if self.action == 'destroy':
            return [IsAdminOrMuhasebe()]
        return [IsAdminOrSatis()]
    
    def get_queryset(self):
        queryset = Fatura.objects.select_related('cari', 'olusturan').prefetch_related('kalemler').all()
        tip = self.request.query_params.get('tip', None)
        durum = self.request.query_params.get('durum', None)
        
        # Input validation
        if tip:
            try:
                tip = sanitize_string(tip)
                if tip in ['Satis', 'Alis']:
                    queryset = queryset.filter(fatura_tipi=tip)
            except Exception as e:
                logger.warning(f"Invalid tip: {str(e)}")
        
        if durum:
            try:
                durum = sanitize_string(durum)
                if durum in ['Beklemede', 'Odendi', 'Iptal']:
                    queryset = queryset.filter(durum=durum)
            except Exception as e:
                logger.warning(f"Invalid durum: {str(e)}")
        
        return queryset
    
    @handle_api_errors
    def list(self, request, *args, **kwargs):
        """List all invoices with input validation."""
        return super().list(request, *args, **kwargs)
    
    @handle_api_errors
    def create(self, request, *args, **kwargs):
        """Create a new invoice with input validation."""
        return super().create(request, *args, **kwargs)
    
    @handle_api_errors
    def retrieve(self, request, *args, **kwargs):
        """Retrieve an invoice with input validation."""
        return super().retrieve(request, *args, **kwargs)
    
    @handle_api_errors
    def update(self, request, *args, **kwargs):
        """Update an invoice with input validation."""
        return super().update(request, *args, **kwargs)
    
    @handle_api_errors
    def destroy(self, request, *args, **kwargs):
        """Delete an invoice with input validation."""
        return super().destroy(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        fatura = serializer.save(olusturan=self.request.user)
        log_action(self.request.user, 'create', fatura, f'Fatura oluşturuldu: {fatura.fatura_no}')

