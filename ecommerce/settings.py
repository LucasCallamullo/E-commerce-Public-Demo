

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# =====================================================================================
#             EVERYTHING RELATED TO ENVIRONMENTAL VARIABLES n DB
# =====================================================================================
import environ, os
# Valor por defecto y casteo automático
env = environ.Env(DEBUG=(bool, False)) 

# Intentar leer el archivo .env SOLO si existe (útil para desarrollo local sin Docker)
# Si estás en Docker, el archivo no estará (por el .dockerignore), pero las variables sí.
env_file = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_file):
    environ.Env.read_env(env_file)
    
# ----- CONFIGURACIÓN -------
SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')

# Mercado Pago
MERCADO_PAGO_PUBLIC_KEY = env('MERCADO_PAGO_PUBLIC_KEY')
MERCADO_PAGO_ACCESS_TOKEN = env('MERCADO_PAGO_ACCESS_TOKEN')


# API img BB Keys
IMGBB_KEY = env('IMG_BB_KEY') 
# PYME_NAME = "Cat Cat Games"

# O si preferís mantener tu formato manual que ya funciona:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('postgres_DATABASE'),
        'USER': env('postgres_USER'),
        'PASSWORD': env('postgres_PASSWORD'),
        'HOST': env('postgres_HOST'), # En Docker será 'db_cliente_1'
        'PORT': env('postgres_PORT'),
    }
}


# configuiracion estandar email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
# configuracion basica email variables de entorno
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


# AGREGADO PARA VISTAS DE PASSWORD RESET
LOGIN_URL = '/auth/login/'  # o donde tengas el login
PASSWORD_RESET_TIMEOUT = 86400  # 24 horas de validez
    
# =====================================================================================
#             Application definition
# =====================================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    
    'whitenoise.runserver_nostatic',    # recomendado antes de staticfiles
    'django.contrib.staticfiles',
    
    # for deploy
    'rest_framework',
    'django.contrib.sites',      # Necesario para password reset
    
    # My apps
    'core',
    'home',
    'users',
    
    'products',
    'cart',
    
    'orders',
    'payments',
    
    'dashboard',
    'dashboard_sales',
    'profiles',
    'favorites',
    
    'contact',
    'compressor',    # to minify css and js
    'audit',
    
    'drf_spectacular',  # <-- swagger para drf, al final de todo recomendado
]

# Para el password reset, vistas personalizadas de drf
SITE_ID = 1  
 
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', 
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    
    # como depende de los user despues de authentication si o si
    'cart.middleware.CartMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
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
                'cart.context_processors.cart_context',
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

# Asegurate de que Whitenoise sepa dónde buscar
WHITENOISE_MANIFEST_STRICT = False

# Usar el almacenamiento simple de Whitenoise mientras debugueamos Docker
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'



# "compress" stuff
STATICFILES_FINDERS = [  
    'django.contrib.staticfiles.finders.FileSystemFinder',  
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',  
    'compressor.finders.CompressorFinder',  
]   
COMPRESS_CSS_FILTERS = ["compressor.filters.cssmin.CSSMinFilter"]    
COMPRESS_JS_FILTERS = ["compressor.filters.jsmin.JSMinFilter"]

COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True

if DEBUG:
    COMPRESS_ENABLED = False  # Desactiva la compresión pero mantiene el tag (default=True)
    COMPRESS_OFFLINE = False    # en produccion a True    


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# drf stuff config
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        
        # This allows you to view the API in HTML format (browser interface)
        'rest_framework.renderers.BrowsableAPIRenderer',  
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
    ),
    
    # configuracion nativa para rate limiting
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        # ESTA LÍNEA ES LA QUE HACE MAGIA CON EL SCOPE:
        'rest_framework.throttling.ScopedRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',
        'user': '1000/day',
        'auth_heavy': '5/minute', # Muy estricto para Login/Registro
        'email_reset': '3/minute', # Muy estricto para recuperar contraseña
        'orders': '3/minute',     # Muy estricto para crear nuevas ordenes
        'search': '25/minute',     # Muy estricto para busquedas de productos
        'favorites': '15/minute',    # estricto para que no jueguen con el endpoint de favs
    },
    
    # La nueva configuración para drf-spectacular    / swagger stuff:
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    
    # personaliza errores de forma simplificada sobre todo los 400 y 404
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
}



# Configuración opcional de drf-spectacular 
SPECTACULAR_SETTINGS = {
    'TITLE': 'Cat Games API',
    'DESCRIPTION': 'Documentación completa de la API de tu producto',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,  # No incluir schema en la página
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,  # Mantiene token en sesión
        'displayOperationId': True,
    },
    # Para autenticación con tokens (si usas TokenAuth)
    'COMPONENT_SPLIT_REQUEST': True,  # Mejor soporte para file upload
}

# todas cosas que ver con logging en local
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    
    # Formateador simple: Fecha - Nivel - Mensaje
    "formatters": {
        "simple": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple", # Usamos el formateador simple
        },
    },

    "root": {
        "handlers": ["console"],
        # NOTE Usamos el valor de DEBUG para decidir cuánto loguear
        # Si DEBUG es True (local) vemos todo. Si es False (producción) solo avisos/errores.
        "level": "DEBUG" if DEBUG else "WARNING",
    },
}

# cache por defecto de django solamente que ahora lo hago explicito mudar a redis en el futuro
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# ALLOWED_HOSTS: Solo dominios o IPs, SIN el puerto.
# ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '0.0.0.0']
ALLOWED_HOSTS = ['*']

# CSRF_TRUSTED_ORIGINS: AQUÍ SÍ va el protocolo (http) y el puerto.
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    'https://3a72490574f8.ngrok-free.app',
]




# --- AJUSTE FINAL DE SEGURIDAD Y LOGS ---
if not DEBUG:
    pass
    # Configuraciones específicas de producción (Hetzner)
    # ALLOWED_HOSTS = [env('DOMAIN_NAME', default='tudominio.com')]
    # En producción, forzar HTTPS si tenés SSL
    # SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    # SECURE_SSL_REDIRECT = True

else:
    ALLOWED_HOSTS = ['*']
    BASE_URL_PAGE = "https://656321f2e712.ngrok-free.app"
    CSRF_TRUSTED_ORIGINS.append(BASE_URL_PAGE)
    
    # para desarrollo asi evita enviar emails, los manda a consola
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    
    """ 
    # Eliminamos el bloque LOGGING de aquí para que no pida colorlog en Docker
    LOGGING = {
        "formatters": {
            "colored": {
                "()": "colorlog.ColoredFormatter",
                "format": "%(log_color)s%(levelname)s [%(name)s] %(message)s",
                "log_colors": {
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold_red",
                },
            },
        },

        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "colored",
            },
        },
    }
    
    # ELIMINAR ANTES DE SUBIR A PRODCIOON
    # INSTALLED_APPS += ['debug_toolbar']
    # MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    # INTERNAL_IPS = ['127.0.0.1', '::1']  # Solo accesible localmente
    """
    