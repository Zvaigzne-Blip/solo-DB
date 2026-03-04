"""
Django settings for SoloHub project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env from project root
load_dotenv(BASE_DIR / '.env')

# ─────────────────────────────────────────────────────────────────────────────
# Security
# ─────────────────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-@($!341+&)g2vrqx(bm4v_aldmknf@h8x8gge29qy!2h1i76ja'
)

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = [
    h.strip() for h in
    os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    if h.strip()
]
# Accept all *.run.app subdomains (Cloud Run auto-assigned URLs)
# Accept Firebase Hosting domains
if not DEBUG:
    ALLOWED_HOSTS += ['.run.app', '.web.app', '.firebaseapp.com']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'corsheaders',
    # Local
    'solohub',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # static files — must be 2nd
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# ─────────────────────────────────────────────────────────────────────────────
# Database — SQLite for local dev, PostgreSQL (Render / any provider) in prod
# Set DATABASE_URL in environment to switch:
#   DATABASE_URL=postgresql://user:pass@host:5432/dbname
# ─────────────────────────────────────────────────────────────────────────────
_db_url = os.environ.get('DATABASE_URL', '')

if _db_url.startswith('postgresql') or _db_url.startswith('postgres'):
    import urllib.parse as _up
    _r = _up.urlparse(_db_url)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': _r.path.lstrip('/'),
            'USER': _r.username,
            'PASSWORD': _r.password,
            'HOST': _r.hostname,
            'PORT': _r.port or 5432,
            'OPTIONS': {'sslmode': 'require'},
        }
    }
else:
    # Local development — SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = '/static/'
# Files are collected into  staticfiles/static/  so that Firebase Hosting
# (public: "staticfiles") can serve URL  /static/admin/css/base.css  by
# reading  staticfiles/static/admin/css/base.css  directly from its CDN.
# Without this sub-folder every static request falls through the "**" rewrite
# and hits Cloud Run instead of being cached at the edge.
STATIC_ROOT = BASE_DIR / 'staticfiles' / 'static'

# Django 6.0+ uses STORAGES dict instead of deprecated STATICFILES_STORAGE
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Security headers — enabled in production (DEBUG=False)
# ─────────────────────────────────────────────────────────────────────────────

# Fly.io injects FLY_APP_NAME; Render injects RENDER_EXTERNAL_HOSTNAME.
# Both terminate TLS at the edge — SECURE_SSL_REDIRECT must stay False
# (internal health checks hit plain HTTP).
_ON_FLY    = bool(os.environ.get('FLY_APP_NAME'))
_ON_RENDER = bool(os.environ.get('RENDER_EXTERNAL_HOSTNAME'))
_EDGE_HOST = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '')

if not DEBUG:
    if _ON_FLY:
        ALLOWED_HOSTS += ['.fly.dev']
    if _ON_RENDER and _EDGE_HOST:
        ALLOWED_HOSTS += [_EDGE_HOST, '.onrender.com']

    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    # Edge platforms handle HTTP→HTTPS; internal redirect breaks health checks.
    SECURE_SSL_REDIRECT = not (_ON_FLY or _ON_RENDER)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    # Django 4.0+ CSRF check — list every public hostname that sends POST
    # requests (Firebase Hosting URL, custom domain, Cloud Run direct URL).
    # Override via CSRF_TRUSTED_ORIGINS env var to add custom domains.
    _csrf_extra = [
        o.strip()
        for o in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')
        if o.strip()
    ]
    _render_origin = ([f'https://{_EDGE_HOST}'] if _EDGE_HOST else []) + ['https://*.onrender.com']
    CSRF_TRUSTED_ORIGINS = [
        'https://*.web.app',
        'https://*.firebaseapp.com',
        'https://*.run.app',
        'https://solohub-tgb6xr7dcq-ew.a.run.app',
        'https://*.fly.dev',
    ] + _render_origin + _csrf_extra

# ─────────────────────────────────────────────────────────────────────────────
# Default primary key field type
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─────────────────────────────────────────────────────────────────────────────
# CORS — accept all origins in dev; lock down in production via ALLOWED_ORIGINS
# ─────────────────────────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',') if o.strip()
]

# ─────────────────────────────────────────────────────────────────────────────
# Django REST Framework
# ─────────────────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

