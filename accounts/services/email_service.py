import logging
from functools import wraps
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from smtplib import SMTPException

# Logger yapılandırması
logger = logging.getLogger(__name__)

def handle_email_errors(func):
    """
    E-posta gönderim hatalarını yakalayan, loglayan ve 
    sistemin çökmesini engelleyen wrapper.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # to_email bilgisini yakalamaya çalış (hata logunda göstermek için)
        to_email = kwargs.get('to_email') or (args[1] if len(args) > 1 else "Bilinmiyor")
        subject = kwargs.get('subject') or (args[0] if len(args) > 0 else "Konu Yok")

        try:
            logger.info(f"E-posta gönderiliyor: {to_email} | Konu: {subject}")
            return func(*args, **kwargs)
        
        except SMTPException as e:
            # SMTP seviyesindeki hatalar (Bağlantı sorunu, kimlik doğrulama vb.)
            logger.error(f"SMTP Hatası ({to_email}): {str(e)}", exc_info=True)
            return False
            
        except Exception as e:
            # Diğer beklenmedik hatalar
            logger.error(f"E-posta Gönderiminde Beklenmedik Hata ({to_email}): {str(e)}", exc_info=True)
            return False
            
    return wrapper


class EmailService:
    """
    E-posta gönderimlerini merkezi bir noktadan yöneten servis.
    """

    @staticmethod
    @handle_email_errors
    def send_email(subject: str, to_email: str, html_content: str, text_content: str | None = None) -> bool:
        """
        HTML destekli e-posta gönderir. 
        Wrapper sayesinde hata anında sistem çökmez, False döner.
        """
        
        # Plain text gövde yoksa varsayılan mesajı ayarla
        if not text_content:
            text_content = "Bu e-posta HTML içeriğe sahiptir. Lütfen uygun bir istemci ile görüntüleyin."

        # E-posta nesnesini oluştur
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )

        # HTML içeriğini ekle
        email.attach_alternative(html_content, "text/html")

        # Gönderimi başlat
        # fail_silently=False diyoruz çünkü hatayı zaten @handle_email_errors yakalıyor
        result = email.send(fail_silently=False)
        
        return True if result else False