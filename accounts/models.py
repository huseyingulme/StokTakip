from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    telefon = models.CharField(max_length=20, blank=True, null=True)
    adres = models.TextField(blank=True, null=True)
    pozisyon = models.CharField(max_length=100, blank=True, null=True)
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'accounts_userprofile'

    def __str__(self):
        return f"{self.user.username} - Profile"


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Oluşturma'),
        ('update', 'Güncelleme'),
        ('delete', 'Silme'),
        ('view', 'Görüntüleme'),
        ('export', 'Dışa Aktarma'),
        ('login', 'Giriş'),
        ('logout', 'Çıkış'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    model_name = models.CharField(max_length=100)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        db_table = 'accounts_auditlog'
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.user} - {self.get_action_display()} - {self.model_name} - {self.timestamp}"

