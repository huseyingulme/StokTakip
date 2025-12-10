from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()  # .env yükle

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
# Production'da DEBUG=False olmalı, development için .env'de DEBUG=True yapılabilir
# Development için varsayılan olarak True (production'da mutlaka False yapılmalı!)
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# SECRET_KEY - Production'da mutlaka environment variable'dan alınmalı
# Development için fallback key kullanılabilir
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    # Development için geçici bir key (production'da kullanılmamalı!)
    SECRET_KEY = 'django-insecure-dev-key-only-for-development-do-not-use-in-production'
    # Production modunda uyarı ver (DEBUG=False ise)
    if not DEBUG:
        import warnings
        warnings.filterwarnings('once')  # Sadece bir kez göster
        

# ALLOWED_HOSTS - Production'da mutlaka doldurulmalı
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',') if os.getenv('ALLOWED_HOSTS') else []
if not ALLOWED_HOSTS:
    # Development için localhost ve 127.0.0.1 ekle
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']
    # Production modunda uyarı ver (DEBUG=False ise)
    if not DEBUG:
        import warnings
        warnings.filterwarnings('once')  # Sadece bir kez göster
        

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = '/raporlar/'  # Giriş sonrası dashboard'a yönlendir
LOGOUT_REDIRECT_URL = '/accounts/login/'  # Çıkış sonrası login sayfasına yönlendir


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    # local apps
    "accounts",
    "stok",
    "cari",
    "fatura",
    "raporlar",
    "masraf",
    "finans",
    "kullanici_yonetimi",
    "api",
]

# drf_spectacular (API documentation) - optional
try:
    import drf_spectacular  # pyright: ignore[reportMissingImports]
    INSTALLED_APPS.insert(INSTALLED_APPS.index("rest_framework") + 1, "drf_spectacular")
except ImportError:
    pass

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "accounts.middleware.RateLimitMiddleware",
    "accounts.middleware.SecurityHeadersMiddleware",
]

ROOT_URLCONF = "stoktakip.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "stoktakip.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "StokTakip"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", "sql"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "tr-tr"

TIME_ZONE = "Europe/Istanbul"

USE_I18N = True

USE_TZ = True


STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Security settings (production için)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# Session settings
SESSION_COOKIE_AGE = 86400  # 24 saat
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    },
}

# API Documentation (drf-spectacular) - optional
try:
    import drf_spectacular  # pyright: ignore[reportMissingImports]
    REST_FRAMEWORK['DEFAULT_SCHEMA_CLASS'] = 'drf_spectacular.openapi.AutoSchema'
    
    SPECTACULAR_SETTINGS = {
        'TITLE': 'Stok Takip API',
        'DESCRIPTION': 'Stok Takip Sistemi API Dokümantasyonu',
        'VERSION': '1.0.0',
        'SERVE_INCLUDE_SCHEMA': False,
        'COMPONENT_SPLIT_REQUEST': True,
        'SCHEMA_PATH_PREFIX': '/api/v1/',
    }
except ImportError:
    pass

# Email settings (Password reset için)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Development için console
# Production için aşağıdaki ayarları kullanın:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
# EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
# EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
# DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@stoktakip.com')

# Error pages (urls.py'de tanımlı)

# Cache Configuration (Redis)
# Redis bağlantısını test et, yoksa LocMemCache kullan
REDIS_AVAILABLE = False
try:
    import redis
    r = redis.Redis(host='127.0.0.1', port=6379, db=1, socket_connect_timeout=1, socket_timeout=1)
    r.ping()
    REDIS_AVAILABLE = True
except (ImportError, redis.ConnectionError, redis.TimeoutError, Exception):
    REDIS_AVAILABLE = False

if REDIS_AVAILABLE:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'SOCKET_CONNECT_TIMEOUT': 1,
                'SOCKET_TIMEOUT': 1,
                'IGNORE_EXCEPTIONS': True,  # Redis hatalarını yok say
            },
            'KEY_PREFIX': 'stoktakip',
            'TIMEOUT': 300,  # 5 dakika
        }
    }
    # Session Cache (Redis)
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'
else:
    # Redis yoksa local memory cache kullan
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
            'TIMEOUT': 300,
        }
    }
    # Session normal session backend kullan (Redis yoksa)
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'stoktakip.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'propagate': True,
        },
        'stoktakip': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
}

# Rate Limiting
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# Celery Configuration (Async tasks için)
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://127.0.0.1:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
