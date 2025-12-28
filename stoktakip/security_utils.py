import re
from typing import Any, Optional
from django.core.exceptions import ValidationError


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """
    String input'u sanitize eder ve güvenli hale getirir.
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
    try:
        float_value = float(value)
    except (ValueError, TypeError):
        raise ValidationError("Input must be a valid number")
    
    if min_value is not None and float_value < min_value:
        raise ValidationError(f"Value must be at least {min_value}")
    
    if max_value is not None and float_value > max_value:
        raise ValidationError(f"Value must be at most {max_value}")
    
    return float_value


def validate_date_range(start_date: str, end_date: str) -> tuple[str, str]:

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

    if not query:
        return ""
    
    cleaned = sanitize_string(query, max_length=max_length)
    
    # Sadece alfanumerik karakterler, boşluk ve bazı özel karakterlere izin ver
    if not re.match(r'^[a-zA-Z0-9\s\-_.,;:!?()]+$', cleaned):
        raise ValidationError("Arama sorgusu geçersiz karakterler içeriyor.")
    
    return cleaned

