

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# =====================================================================================
#             EVERYTHING RELATED TO ENVIRONMENTAL VARIABLES n DB
# =====================================================================================
import environ, os
env = environ.Env()    # Init the environment

# configuiracion estander email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True

try:
    # In local we use environ to bring keys from the .env file, in "Railway" this does not work
    # as such and we must use the "except" block to configure correctly with the environment variables
    # that are added in the "Railway" panel
    environ.Env.read_env()
    MERCADO_PAGO_PUBLIC_KEY = env('MERCADO_PAGO_PUBLIC_KEY')
    MERCADO_PAGO_ACCESS_TOKEN = env('MERCADO_PAGO_ACCESS_TOKEN')
    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY = env('SECRET_KEY')
    # SECURITY WARNING: don't run with debug turned on in production!
    DEBUG = env('DEBUG')
    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('postgres_DATABASE'),
            'USER': env('postgres_USER'),
            'PASSWORD': env('postgres_PASSWORD'),
            'HOST': env('postgres_HOST'),
            'PORT': env('postgres_PORT'),
        }
    }
    
    # configuracion basica email variables de entorno
    EMAIL_HOST_USER = env('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
    DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


except environ.ImproperlyConfigured:
    # This is for deploy on railway
    MERCADO_PAGO_PUBLIC_KEY = os.getenv('MERCADO_PAGO_PUBLIC_KEY', 'default_public_key')
    MERCADO_PAGO_ACCESS_TOKEN = os.getenv('MERCADO_PAGO_ACCESS_TOKEN', 'default_access_token')
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
    DEBUG = os.getenv('DEBUG', True)
    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'ecommerce_proofs',
            'USER': 'postgres',
            'PASSWORD': '1234',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }
    
    # configuracion basica email variables de entorno
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'email_not_found'),
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'pw_email_not_found'),
    DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
  
  
# =====================================================================================
#             Application definition
# =====================================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # for deploy
    'whitenoise.runserver_nostatic',
    'rest_framework',
    
    # My apps
    'home',
    'users',
    
    'cart',
    'products',
    'orders',
    'payments',
    
    # 'dashboard',
    'profiles',
    'favorites',
    
    'contact',
    'compressor', 
]
 
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', 
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'cart.middleware.CartMiddleware',    # como depende de los user despues de authentication si o si
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ecommerce.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                
                # This is my custom context_processors
                'products.context_processors.get_categories_n_subcats',
                'home.context_processors.get_ecommerce_data',
                'cart.context_processors.carrito_total',
            ],
        },
    },
]

WSGI_APPLICATION = 'ecommerce.wsgi.application'

# custom user stuff
AUTH_USER_MODEL = 'users.CustomUser' 

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 4,  # Longitud mínima de cuatro caracteres
        }
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/
# LANGUAGE_CODE = 'en-us'
# TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Argentina/Buenos_Aires'  # Cambiado a la zona horaria de Argentina
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# Ruta para archivos estaticos globales
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]

MEDIA_URL = 'media/' 
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Add for deploy to use "Whitenoise" and "Compress"
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# "compress" stuff
STATICFILES_FINDERS = [  
    'django.contrib.staticfiles.finders.FileSystemFinder',  
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',  
    'compressor.finders.CompressorFinder',  
]  
COMPRESS_ENABLED = False  # Desactiva la compresión pero mantiene el tag (default=True)
COMPRESS_OFFLINE = False    # en produccion a True     
COMPRESS_CSS_FILTERS = ["compressor.filters.cssmin.CSSMinFilter"]    
COMPRESS_JS_FILTERS = ["compressor.filters.jsmin.JSMinFilter"]


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# drf stuff
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        
        # This allows you to view the API in HTML format (browser interface)
        'rest_framework.renderers.BrowsableAPIRenderer',  
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
    ),
}

# this is for deployment API imgBB
IMGBB_KEY = '7923341a22d8128e89471ca8a60919a2'
PYME_NAME = "Cat Cat Games"

# this is for deployment and ngrok web hook
ALLOWED_HOSTS = ['127.0.0.1']

CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1',
]

BASE_URL_PAGE = "https://656321f2e712.ngrok-free.app"


if DEBUG:
    ALLOWED_HOSTS = ['*']
    CSRF_TRUSTED_ORIGINS.append(BASE_URL_PAGE)
    
    # ELIMINAR ANTES DE SUBIR A PRODCIOON
    # INSTALLED_APPS += ['debug_toolbar']
    # MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    # INTERNAL_IPS = ['127.0.0.1', '::1']  # Solo accesible localmente