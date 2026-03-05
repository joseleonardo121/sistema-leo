"""
Django settings for config project.
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# --- CONFIGURACIÓN DE SEGURIDAD ---
SECRET_KEY = 'django-insecure-lj=@ei(9t5rtmpt5wvjep=pl@zuxq8%#l-k4)_s)iybd&y4b&v'

# CAMBIAR A 'False' cuando subas a PythonAnywhere
DEBUG = True

# En PythonAnywhere pon ['tunombre.pythonanywhere.com']
ALLOWED_HOSTS = ['*']


# --- APLICACIONES INSTALADAS ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Tus aplicaciones
    'core',
    'ventas',
    'accounts',
    'web',
    'simple_history',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # Para tus templates generales
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'ventas.context_processors.caja_actual',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# --- BASE DE DATOS ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# --- VALIDACIÓN DE CONTRASEÑAS ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]


# --- INTERNACIONALIZACIÓN (Configurado para Arequipa, Perú) ---
LANGUAGE_CODE = 'es-pe'
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = True


# --- ARCHIVOS ESTÁTICOS (CSS, JS) ---
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'core' / 'static',
]
# Carpeta donde se recolectarán los estáticos en PythonAnywhere
STATIC_ROOT = BASE_DIR / 'staticfiles'


# --- ARCHIVOS MEDIA (Fotos de productos, Banners) ---
# Muy importante para que tu catálogo muestre las imágenes
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# --- CONFIGURACIÓN DE ACCESOS (LOGIN/LOGOUT) ---
# Estas rutas deben coincidir con tus URLs
LOGIN_URL = '/cuentas/login/'
LOGIN_REDIRECT_URL = '/gestion/ventas/'
LOGOUT_REDIRECT_URL = '/'


# --- OTROS ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'