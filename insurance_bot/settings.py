from pathlib import Path
from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

SITE_ID = 1
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, ".env"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-djq+!-g)4^3j*v53)q34x(p%uay0r8v*rml9d-oz+ia(f)=1dg")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = ['.vercel.app', 'localhost','127.0.0.1']
LOGIN_URL = 'login'
# Application definition
INSTALLED_APPS = [
    'home',
    'chatbot',
    'insurance', 
    'django.contrib.admin',
    'django.contrib.humanize',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'allauth',
    'claims',
    'accounts',
    'pwa',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'allauth.account.middleware.AccountMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
]
PWA_APP_NAME = 'BeemaSakhi'
PWA_APP_DESCRIPTION = "insurance made easy."
PWA_APP_THEME_COLOR = '#0A0302'
PWA_APP_ICONS = [{'src': '/static/images/icon.png', 'sizes': '160x160'}]
# Tell Django where your custom service worker will live
PWA_SERVICE_WORKER_PATH = os.path.join(BASE_DIR, 'static/js', 'serviceworker.js')

# Add this at the bottom of the file
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
# Redirects
LOGIN_REDIRECT_URL = 'dashboard'  # <--- Essential for the flow to start
LOGOUT_REDIRECT_URL = 'login'

# Allauth Config
SOCIALACCOUNT_AUTO_SIGNUP = True  # Automatically creates user without asking for username
SOCIALACCOUNT_LOGIN_ON_GET = True # Skips the "Are you sure?" confirmation screen
ROOT_URLCONF = 'insurance_bot.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # ✅ allows global template directory if you use one
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

WSGI_APPLICATION = 'insurance_bot.wsgi.application'

# Database
DATABASES = {
    'default': dj_database_url.config(
        # Replace this with your variable name if different
        default=os.environ.get('DATABASE_URL'), 
        conn_max_age=600
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ✅ Internationalization (fixed typo: USE_I18N)
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'  # set to India timezone (you can adjust)
USE_I18N = True
USE_TZ = True

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# URL to use when referring to static files (where they will be served from)
STATIC_URL = 'static/'

# Where your static files live during development (e.g., inside your 'static' folder)
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'), 
]

# Where Django collects all static files for production (WhiteNoise serves from here)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Enable WhiteNoise's file compression and caching
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ✅ Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

ACCOUNT_USERNAME_REQUIRED = False      # Don't ask for username during signup
ACCOUNT_AUTHENTICATION_METHOD = 'email' # Users log in with email
ACCOUNT_EMAIL_REQUIRED = True          # Email is mandatory
ACCOUNT_UNIQUE_EMAIL = True            # Ensure emails are unique
ACCOUNT_EMAIL_VERIFICATION = 'none'    # Skip email verification for simplicity (can change to 'mandatory' later)
# ------------------------------------------------
ACCOUNT_LOGOUT_ON_GET = True
SOCIALACCOUNT_LOGIN_ON_GET = True
# Ensure this is still True
SOCIALACCOUNT_AUTO_SIGNUP = True
