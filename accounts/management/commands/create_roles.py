from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from stok.models import Urun, StokHareketi
from cari.models import Cari, CariHareketi
from fatura.models import Fatura


class Command(BaseCommand):
    help = 'Kullanıcı rollerini ve izinlerini oluşturur'

    def handle(self, *args, **options):
        admin_group, created = Group.objects.get_or_create(name='Admin')
        muhasebe_group, created = Group.objects.get_or_create(name='Muhasebe')
        satis_group, created = Group.objects.get_or_create(name='Satış')
        depo_group, created = Group.objects.get_or_create(name='Depo')
        rapor_group, created = Group.objects.get_or_create(name='Rapor')

        urun_ct = ContentType.objects.get_for_model(Urun)
        stok_hareket_ct = ContentType.objects.get_for_model(StokHareketi)
        cari_ct = ContentType.objects.get_for_model(Cari)
        cari_hareket_ct = ContentType.objects.get_for_model(CariHareketi)
        fatura_ct = ContentType.objects.get_for_model(Fatura)

        admin_permissions = Permission.objects.all()
        admin_group.permissions.set(admin_permissions)

        muhasebe_permissions = Permission.objects.filter(
            content_type__in=[cari_ct, cari_hareket_ct, fatura_ct]
        )
        muhasebe_group.permissions.set(muhasebe_permissions)

        satis_permissions = Permission.objects.filter(
            content_type__in=[cari_ct, fatura_ct]
        ).exclude(codename__contains='delete')
        satis_group.permissions.set(satis_permissions)

        depo_permissions = Permission.objects.filter(
            content_type__in=[urun_ct, stok_hareket_ct]
        )
        depo_group.permissions.set(depo_permissions)

        rapor_permissions = Permission.objects.filter(
            codename__contains='view'
        )
        rapor_group.permissions.set(rapor_permissions)

        self.stdout.write(self.style.SUCCESS('Roller başarıyla oluşturuldu!'))

