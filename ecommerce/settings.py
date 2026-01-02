from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# =====================================================================================
#                ENVIRONMENTAL VARIABLES & DATABASE CONFIGURATION
# =====================================================================================
import environ, os

# Initialize environment variables and set default casting (e.g., DEBUG as boolean)
env = environ.Env(DEBUG=(bool, False)) 

# Load .env file ONLY if it exists (useful for local development without Docker)
# In Docker, variables are injected directly, so the .env file is not required.
env_file = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_file):
    environ.Env.read_env(env_file)
    
# --- CORE SETTINGS ---
# Security Key and Debug mode are pulled from the environment for security
SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')

# --- THIRD-PARTY INTEGRATIONS ---

# Mercado Pago Credentials (Payment Gateway)
MERCADO_PAGO_PUBLIC_KEY = env('MERCADO_PAGO_PUBLIC_KEY')
MERCADO_PAGO_ACCESS_TOKEN = env('MERCADO_PAGO_ACCESS_TOKEN')

# Image hosting service (ImgBB) API Key
IMGBB_KEY = env('IMG_BB_KEY') 

# --- DATABASE CONFIGURATION ---
# PostgreSQL setup using environment variables for sensitive credentials.
# In a Docker environment, 'HOST' should match the database service name (e.g., 'db_client_1').
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),     # En Docker será 'db_client_1'
        'PORT': env('DB_PORT'),
    }
}


# ----------------------------------------------------------------------------------------- 
# EMAIL CONFIGURATION
# -----------------------------------------------------------------------------------------
# Default backend for sending emails via SMTP (Production)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
if DEBUG:
    # In development, emails are printed to the console instead of being sent
    # This prevents accidental spam and allows for easy testing
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# SMTP Server settings (Configured for Gmail)
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True  # Protocol for securing the connection

# Email credentials loaded from environment variables for security
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')

# Default email address for outgoing system notifications
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


# ----------------------------------------------------------------------------------------- 
# AUTHENTICATION & PASSWORD RECOVERY 
# -----------------------------------------------------------------------------------------
# The URL where users are redirected for login (used by @login_required decorator)
LOGIN_URL = '/auth/login/'

# Token validity duration for password reset links (86400 seconds = 24 hours)
# This improves security by ensuring reset links expire after a day
PASSWORD_RESET_TIMEOUT = 86400

# Django 'sites' framework ID. 
# Required by many third-party apps to generate absolute URLs in emails (like password reset links)
SITE_ID = 1


# -----------------------------------------------------------------------------------------
#             Application definition
# -----------------------------------------------------------------------------------------
INSTALLED_APPS = [
    # --- CORE DJANGO APPS ---
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # --- THIRD-PARTY LIBRARIES ---
    'rest_framework',
    'django.contrib.sites',  # Required for site-specific features (e.g., password reset via API)
    'compressor',           # Assets minification (JS/CSS)
    'drf_spectacular',      # OpenAPI 3.0 documentation (Swagger)
    
    # --- PROJECT BUSINESS LOGIC (Internal Apps) ---
    'core',           # Shared utilities and base classes
    'home',           # Marketing and landing pages
    'users',          # User authentication and management
    'profiles',       # User profiles and preferences
    'products',       # Catalog and product management
    'favorites',      # Wishlists and user bookmarks
    
    # --- E-COMMERCE ENGINE ---
    'cart',           # Shopping cart logic
    'orders',         # Order processing and management
    'payments',       # Payment gateway integration (e.g., Mercado Pago)
    
    # --- ANALYTICS AND BACKOFFICE ---
    # 'dashboard',       # General administration dashboard
    # 'dashboard_sales', # Specialized sales analytics
    # 'audit',           # Logging and system activity tracking
    
    'contact',         # Contact forms and support (email smtp)
]


# ----------------------------------------------------------------------------------------- 
# MIDDLEWARE CONFIGURATION
# -----------------------------------------------------------------------------------------
# Middleware classes process requests and responses globally
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # 'whitenoise.middleware.WhiteNoiseMiddleware', # Disabled: Nginx handles static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    
    # Custom Middleware: Must be placed after AuthenticationMiddleware to access 'request.user'
    'cart.middleware.CartMiddleware',
    
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ecommerce.urls'

# --- TEMPLATE ENGINE CONFIGURATION ---
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [], # Folders for global templates (if any)
        'APP_DIRS': True, # Look for 'templates/' folder inside each app
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                
                # Custom Context Processors: Inject data globally into all templates
                'products.context_processors.get_categories_n_subcats',
                'home.context_processors.get_ecommerce_data',
                'cart.context_processors.cart_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'ecommerce.wsgi.application'

# --- USER AUTHENTICATION MODEL ---
# Overriding the default User model with a custom implementation
AUTH_USER_MODEL = 'users.CustomUser'


# --- PASSWORD VALIDATION ---
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators
# Security rules for user passwords
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 4,  # Minimum length required for user passwords
        }
    },
]

# --- INTERNATIONALIZATION & LOCALIZATION ---
# https://docs.djangoproject.com/en/5.1/topics/i18n/
LANGUAGE_CODE = 'es' # Default language set to Spanish (def django = 'en-us')
TIME_ZONE = 'America/Argentina/Buenos_Aires' # Local time zone for Argentina (def django = 'UTC')
USE_I18N = True # Enable translation system
USE_TZ = True   # Enable time-zone aware datetimes


# --- STATIC AND MEDIA FILES ---
# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# Directories where Django looks for additional static files
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]

# Destination for collectstatic (where Nginx will serve files in production)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# URL and root directory for user-uploaded files (Product images, etc.)
MEDIA_URL = 'media/' 
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# --- MISCELLANEOUS ---
# Set the default type for auto-generated primary keys
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ----------------------------------------------------------------------------------------- 
# DJANGO COMPRESSOR CONFIGURATION 
# -----------------------------------------------------------------------------------------
# Defines how Django finds static files to be compressed
STATICFILES_FINDERS = [  
    'django.contrib.staticfiles.finders.FileSystemFinder',    # Look for files in global folders (STATICFILES_DIRS)
    'django.contrib.staticfiles.finders.AppDirectoriesFinder', # Look for files within each App's /static/ folder
    'compressor.finders.CompressorFinder',    # Required: allows Compressor to find {% compress %} tags
]   

# Filters to minify files (removes whitespace and comments to reduce file size)
COMPRESS_CSS_FILTERS = ["compressor.filters.cssmin.CSSMinFilter"]    # CSS minification filter
COMPRESS_JS_FILTERS = ["compressor.filters.jsmin.JSMinFilter"]      # JavaScript minification filter

# Defines where the final compressed files will be stored
# Setting this to STATIC_ROOT allows Nginx to easily serve them from the shared volume
COMPRESS_ROOT = STATIC_ROOT

# Enables or disables the compression engine
# Disabled during DEBUG (Development) to allow easier debugging of original source files
COMPRESS_ENABLED = False if DEBUG else True

# OFFLINE COMPRESSION (Crucial for Docker/Production environments)
# False (Dev): Compiles files "on the fly" when a user visits the page
# True (Prod): Django expects files to be pre-compiled (pre-rendered)
# This is why we run 'python manage.py compress --force' in the Dockerfile/Compose command
COMPRESS_OFFLINE = False if DEBUG else True


# ---------------------------------------------------------------------------------- 
# DJANGO REST FRAMEWORK CONFIGURATION 
# ----------------------------------------------------------------------------------
REST_FRAMEWORK = {
    # Renderers define how the API output is displayed
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        # Enables the user-friendly interactive HTML interface in the browser
        'rest_framework.renderers.BrowsableAPIRenderer',  
    ),
    
    # Parsers define how the API handles incoming data (request body)
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
    ),
    
    # --- RATE LIMITING (THROTTLING) CONFIGURATION ---
    # These classes determine who gets limited (Anonymous vs Authenticated users)
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        # ScopedRateThrottle allows custom limits for specific sensitive views
        'rest_framework.throttling.ScopedRateThrottle'
    ],
    
    # Specific rate limits for different types of interactions
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',       # General limit for unauthenticated users
        'user': '1000/day',        # Daily quota for logged-in users
        
        # Scoped limits: Highly restrictive to prevent brute force or abuse
        'auth_heavy': '5/minute',  # Strict limit for Login/Register endpoints
        'email_reset': '3/minute', # Prevents spamming password recovery emails
        'orders': '3/minute',      # Prevents duplicate or automated order creation
        'search': '25/minute',     # Protects the database from heavy search queries
        'favorites': '15/minute',  # Prevents bot manipulation of "favorite" stats
    },
    
    # --- API DOCUMENTATION (SWAGGER/OPENAPI) ---
    # Integration with drf-spectacular for automated OpenAPI 3.0 schema generation
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    
    # --- GLOBAL ERROR HANDLING ---
    # Points to a custom function to standardize 400, 404, and other error responses
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
}


# --- DRF SPECTACULAR (SWAGGER/OPENAPI) SETTINGS ---
# These settings control the automated API documentation generation
SPECTACULAR_SETTINGS = {
    'TITLE': 'Cat Games API',
    'DESCRIPTION': 'Complete API documentation for the E-commerce platform',
    'VERSION': '1.0.0',
    
    # Do not include the raw schema file in the UI page for a cleaner look
    'SERVE_INCLUDE_SCHEMA': False,  
    
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,        # Allows direct linking to specific API endpoints
        'persistAuthorization': True, # Keeps the Auth Token active even after page refresh
        'displayOperationId': True,  # Shows the internal function name for each endpoint
    },
    
    # Split request and response components in the documentation
    # This provides better support for complex tasks like File Uploads (Media)
    'COMPONENT_SPLIT_REQUEST': True,  
}

# ----------------------------------------------------------------------------------
# LOGGING CONFIGURATION 
# ----------------------------------------------------------------------------------
# Standardizes how the application outputs errors and information
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    
    # Formatters define the visual structure of the log message
    "formatters": {
        "simple": {
            # Format: Level - Timestamp - Module - Message
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },

    "handlers": {
        # Console handler outputs logs to the terminal/standard output
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },

    "root": {
        "handlers": ["console"],
        # Logging Level:
        # DEBUG: Shows everything (ideal for development)
        # WARNING: Shows only alerts and errors (ideal for production to save disk space)
        "level": "DEBUG" if DEBUG else "WARNING",
    },
}
# Optional: Use colored logs in Development (DEBUG=True) if colorlog is installed
"""  
if DEBUG:
    try:
        import colorlog
        LOGGING["formatters"]["colored"] = {
            "()": "colorlog.ColoredFormatter",
            "format": "%(log_color)s%(levelname)s [%(name)s] %(message)s",
            "log_colors": {
                "DEBUG": "cyan", "INFO": "green", "WARNING": "yellow", "ERROR": "red", "CRITICAL": "bold_red",
            },
        }
        LOGGING["handlers"]["console"]["formatter"] = "colored"
    except ImportError:
        pass # If colorlog is not installed, it falls back to the simple formatter
"""


# ---------------------------------------------------------------------------------- 
# REDIS CACHE CONFIGURATION 
# ----------------------------------------------------------------------------------
# In Development (DEBUG=True), we use local memory cache for simplicity.
# In Production, we use Redis for high-performance distributed caching.
if DEBUG:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }
else:
    # Using Redis as the primary cache backend for high performance
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://redis_cliente_1:6379/1",    # Using database index 1 in Redis
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            }
        }
    }
    
    
# --- SESSION MANAGEMENT ---
# Storing sessions in Redis instead of the database (Database-less sessions)
# This significantly improves performance and reduces DB load
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"


# --- NETWORK & SECURITY SETTINGS ---

# ALLOWED_HOSTS: Domains or IPs that can serve this Django app.
# Note: In production, '*' should be replaced with your specific domain.
ALLOWED_HOSTS = ['*']

# CSRF_TRUSTED_ORIGINS: Required for secure requests (POST) from specific domains.
# Must include the protocol (http/https) and the port.
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    'https://3a72490574f8.ngrok-free.app', # Temporary ngrok tunnel for testing
]

if DEBUG:
    # BASE_URL_PAGE: Used for generating absolute URLs (e.g., for Mercado Pago webhooks)
    BASE_URL_PAGE = "https://656321f2e712.ngrok-free.app"
    CSRF_TRUSTED_ORIGINS.append(BASE_URL_PAGE)
    
    # --- DEVELOPMENT TOOLS ---
    # Optional: Enable Django Debug Toolbar for performance profiling
    # INSTALLED_APPS += ['debug_toolbar']
    # MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    # INTERNAL_IPS = ['127.0.0.1', '::1']
    
# --- AJUSTE FINAL DE SEGURIDAD Y LOGS ---
else:
    # 1. ¿Quién puede entrar? (Evita ataques de Host Header)
    # ALLOWED_HOSTS = [env('DOMAIN_NAME', default='tudominio.com'), 'www.tudominio.com']

    # 2. Confianza en Nginx
    # Nginx le dirá a Django "esta conexión es segura (HTTPS)"
    # SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # 3. Forzar HTTPS
    # SECURE_SSL_REDIRECT = True # Redirige http:// a https://
    # SESSION_COOKIE_SECURE = True # Solo envía cookies por HTTPS
    # CSRF_COOKIE_SECURE = True # Protege contra ataques CSRF
    
    # 4. HSTS (Opcional pero recomendado)
    # SECURE_HSTS_SECONDS = 31536000 # 1 año
    # SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    # SECURE_HSTS_PRELOAD = True
    pass
