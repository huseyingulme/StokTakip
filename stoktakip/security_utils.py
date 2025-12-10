"""
Güvenlik ve input validation utility fonksiyonları.
CSRF koruması, input sanitization ve XSS koruması için helper'lar.
"""
import re
from typing import Any, Optional, Union
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.core.exceptions import ValidationError


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """
    String input'u sanitize eder ve güvenli hale getirir.
    
    Args:
        value: Temizlenecek string değer
        max_length: Maksimum uzunluk (None ise sınır yok)
    
    Returns:
        Temizlenmiş string
    
    Raises:
        ValidationError: Geçersiz input durumunda
    """
    if not isinstance(value, str):
        raise ValidationError("Input must be a string")
    
    # Başta ve sonda boşlukları temizle
    cleaned = value.strip()
    
    # Null byte karakterlerini kaldır
    cleaned = cleaned.replace('\x00', '')
    
    # Maksimum uzunluk kontrolü
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    
    return cleaned


def sanitize_integer(value: Any, min_value: Optional[int] = None, 
                     max_value: Optional[int] = None) -> int:
    """
    Integer input'u validate ve sanitize eder.
    
    Args:
        value: Dönüştürülecek değer
        min_value: Minimum değer
        max_value: Maksimum değer
    
    Returns:
        Validated integer
    
    Raises:
        ValidationError: Geçersiz input durumunda
    """
    try:
        int_value = int(value)
    except (ValueError, TypeError):
        raise ValidationError("Input must be a valid integer")
    
    if min_value is not None and int_value < min_value:
        raise ValidationError(f"Value must be at least {min_value}")
    
    if max_value is not None and int_value > max_value:
        raise ValidationError(f"Value must be at most {max_value}")
    
    return int_value


def sanitize_decimal(value: Any, min_value: Optional[float] = None,
                     max_value: Optional[float] = None) -> float:
    """
    Decimal/Float input'u validate ve sanitize eder.
    
    Args:
        value: Dönüştürülecek değer
        min_value: Minimum değer
        max_value: Maksimum değer
    
    Returns:
        Validated float
    
    Raises:
        ValidationError: Geçersiz input durumunda
    """
    try:
        float_value = float(value)
    except (ValueError, TypeError):
        raise ValidationError("Input must be a valid number")
    
    if min_value is not None and float_value < min_value:
        raise ValidationError(f"Value must be at least {min_value}")
    
    if max_value is not None and float_value > max_value:
        raise ValidationError(f"Value must be at most {max_value}")
    
    return float_value


def sanitize_sql_input(value: str) -> str:
    """
    SQL injection'a karşı input'u sanitize eder.
    Django ORM kullanıldığı için risk düşük ama ekstra güvenlik için.
    
    Args:
        value: Temizlenecek string
    
    Returns:
        SQL injection'a karşı temizlenmiş string
    """
    if not isinstance(value, str):
        return str(value)
    
    # Tehlikeli SQL karakterlerini escape et
    dangerous_chars = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_']
    cleaned = value
    
    for char in dangerous_chars:
        cleaned = cleaned.replace(char, '')
    
    return cleaned


def safe_html_render(html_content: str) -> str:
    """
    HTML içeriğini güvenli bir şekilde render eder (XSS koruması).
    
    Args:
        html_content: Render edilecek HTML içeriği
    
    Returns:
        Güvenli HTML string (mark_safe ile)
    """
    # Temel XSS koruması - script tag'lerini kaldır
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.IGNORECASE | re.DOTALL)
    
    # Event handler'ları kaldır (onclick, onerror, vb.)
    html_content = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', html_content, flags=re.IGNORECASE)
    
    # JavaScript: protocol'ünü kaldır
    html_content = re.sub(r'javascript:', '', html_content, flags=re.IGNORECASE)
    
    return mark_safe(html_content)


def validate_date_range(start_date: str, end_date: str) -> tuple[str, str]:
    """
    Tarih aralığını validate eder.
    
    Args:
        start_date: Başlangıç tarihi (YYYY-MM-DD formatında)
        end_date: Bitiş tarihi (YYYY-MM-DD formatında)
    
    Returns:
        (start_date, end_date) tuple
    
    Raises:
        ValidationError: Geçersiz tarih veya aralık durumunda
    """
    from datetime import datetime
    
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        raise ValidationError("Tarih formatı geçersiz. YYYY-MM-DD formatında olmalıdır.")
    
    if start > end:
        raise ValidationError("Başlangıç tarihi bitiş tarihinden sonra olamaz.")
    
    # Maksimum 1 yıllık aralık kontrolü
    from datetime import timedelta
    if (end - start).days > 365:
        raise ValidationError("Tarih aralığı en fazla 1 yıl olabilir.")
    
    return start_date, end_date


def validate_search_query(query: str, max_length: int = 100) -> str:
    """
    Arama sorgusunu validate eder.
    
    Args:
        query: Arama sorgusu
        max_length: Maksimum uzunluk
    
    Returns:
        Validated arama sorgusu
    
    Raises:
        ValidationError: Geçersiz sorgu durumunda
    """
    if not query:
        return ""
    
    cleaned = sanitize_string(query, max_length=max_length)
    
    # Sadece alfanumerik karakterler, boşluk ve bazı özel karakterlere izin ver
    if not re.match(r'^[a-zA-Z0-9\s\-_.,;:!?()]+$', cleaned):
        raise ValidationError("Arama sorgusu geçersiz karakterler içeriyor.")
    
    return cleaned

