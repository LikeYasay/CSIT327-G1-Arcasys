import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-dev-key-only')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# FIXED: Add your exact Render URL here
ALLOWED_HOSTS = [
    'marketingarcasysdemo.onrender.com',
    'localhost',
    '127.0.0.1',
    '.onrender.com'
]

# FIXED: CRITICAL - Add your Render URL with https://
CSRF_TRUSTED_ORIGINS = [
    'https://marketingarcasysdemo.onrender.com',
    'http://localhost',
    'http://127.0.0.1'
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Modular apps
    'apps.shared',
    'apps.users',
    'apps.events',
    'apps.marketing',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / "templates",
            BASE_DIR / "apps/shared/templates",
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'

# Database Configuration for Render + Supabase
DATABASE_URL = os.environ.get('DATABASE_URL')
DATABASES = {
    "default": dj_database_url.config(
        default=DATABASE_URL or "sqlite:///db.sqlite3",
        conn_max_age=600,
        ssl_require=True
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Manila'
USE_I18N = True
USE_TZ = True

# Static files (WhiteNoise)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# FIXED: Use ONLY default Django authentication
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# Authentication Redirects
LOGIN_URL = 'users:login'
LOGIN_REDIRECT_URL = 'events:events'
LOGOUT_REDIRECT_URL = 'marketing:landing'

# Email Configuration - UPDATED FOR SENDGRID
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Try SendGrid first (works on Render)
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'  # This is ALWAYS 'apikey' for SendGrid
EMAIL_HOST_PASSWORD = os.environ.get('SENDGRID_API_KEY', '')  # Your SendGrid API key
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'arcasys.marketing.archive@gmail.com')

# Fallback to Gmail only if SendGrid API key is not available (for local testing)
if not os.environ.get('SENDGRID_API_KEY') and DEBUG:
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

# CRITICAL: Reduced timeout for Render environment
EMAIL_TIMEOUT = 10

# Use console backend in development if no email credentials are set
if DEBUG and not any([os.environ.get('SENDGRID_API_KEY'), os.environ.get('EMAIL_HOST_PASSWORD')]):
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Session Settings
SESSION_COOKIE_AGE = 600
SESSION_SAVE_EVERY_REQUEST = True

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# FIXED: Security Settings - Only enable HTTPS in production, not development
if not DEBUG:
    # Production settings (Render)
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
else:
    # Development settings (local)
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False