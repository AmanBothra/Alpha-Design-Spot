import datetime
import logging
import os
from pathlib import Path
import sys
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.stdlib import StdlibIntegration
from sentry_sdk.integrations.excepthook import ExcepthookIntegration

import environ

# -------------------------------------------------------------------
env = environ.Env()
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, os.path.join(BASE_DIR, "app_modules"))
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))
SECRET_KEY = "django-insecure-n2@ca6*6y)uu%a$_afsnr382fz)ir0m8#$63u8343+_1f$uxvv"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ----------------------- Global Variables Need To be Set in .env ---------------------
DEBUG = env.bool("DEBUG", default=True)
DOMAIN = env.str("DOMAIN")
DOMAIN_IP = env.str("DOMAIN_IP")
ALLOWED_HOSTS = ["127.0.0.1", "api.alphawala.xyz", DOMAIN_IP, "localhost"]

AUTH_USER_MODEL = "account.User"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_HOST_URL"),
    }
}

# ------------------------------- APPS and MIDDLEWARE ------------------------------
DJANGO_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "rest_framework_simplejwt",
    # 'rest_framework_simplejwt.token_blacklist',
    "drf_yasg",
    "debug_toolbar",
    "django_celery_results",
    "django_celery_beat",
]

LOCAL_APPS = [
    "config",
    "app_modules.account",
    "app_modules.post",
    "app_modules.master",
    "app_modules.website",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------- Template Configuration -------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# -------------------------- Database Configuration --------------------------

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": "ads",
#         "USER": env("POSTGRES_USER"),
#         "PASSWORD": env("POSTGRES_PASSWORD"),
#         "HOST": env("DB_HOST"),
#         "PORT": 5432,
#         "TIME_ZONE": "Asia/Kolkata",
#     }
# }

DATABASES = {
    "default": {
        "ENGINE": "dj_db_conn_pool.backends.postgresql",  # Enables connection pooling
        "NAME": "ads",
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": 5432,
        "TIME_ZONE": "Asia/Kolkata",
        "OPTIONS": {
            "options": "-c statement_timeout=30000",  # Sets statement timeout to 30 seconds
            "client_encoding": "UTF8",
        },
        "CONN_MAX_AGE": 0,
        "POOL_OPTIONS": {
            "POOL_SIZE": 20,  # Increased from 10 for 7000 users
            "MAX_OVERFLOW": 10,  # Increased from 5 for peak load handling
            "RECYCLE": 1800,  # Reduced from 3600 to 30 minutes for fresher connections
            "POOL_TIMEOUT": 10,  # Reduced from 30 for faster error detection
            "POOL_PRE_PING": True,  # Enable connection health checks
        },
    }
}

# Retry settings
DATABASE_CONNECTION_RETRY_ATTEMPTS = 3
DATABASE_CONNECTION_RETRY_DELAY = 1  # Delay in seconds between retries

# ------------------------------- Password validation -------------------------
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
]

# ---------------------------- Internationalization --------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = env.str("TIME_ZONE", default="Asia/Kolkata")
USE_I18N = True
USE_L10N = True
USE_TZ = True

# ---------------------------- Static Media Settings ------------------------

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATICFILES_DIRS = (os.path.join(BASE_DIR, "staticfiles"),)

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# EMAIL
# ------------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")

# --------------------------- REST and CORS Configuration -----------------------
# Rest framework
REST_FRAMEWORK = {
    "DATE_INPUT_FORMATS": ["%d-%m-%Y", "%Y-%m-%d"],
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "lib.renderer.CustomRenderer",
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_PAGINATION_CLASS": "lib.paginator.CustomPagination",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": datetime.timedelta(days=365),
    "REFRESH_TOKEN_LIFETIME": datetime.timedelta(days=365),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
}

# ---------------------------- Celery Configuration ------------------------
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "django-db"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Kolkata"

CORS_ORIGIN_ALLOW_ALL = False
CORS_ORIGIN_WHITELIST = ["https://dashboard.alphawala.xyz", "http://localhost:3000"]
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "timezone",
]

INTERNAL_IPS = [
    "127.0.0.1",
]

JAZZMIN_SETTINGS = {
    "site_title": "Dashboard",
    "site_header": "Alpha Design Spot",
    "site_brand": "Alpha Design Spot",
    "site_logo": "images/logo.png",
    "login_logo": None,
    "login_logo_dark": None,
    "site_logo_classes": "img-circle",
    "site_icon": None,
    "welcome_sign": "Welcome to the Admin Dashboard",
    "copyright": "Alpha Design Spot",
    "search_model": ["auth.User", "auth.Group"],
    "user_avatar": None,
    #############
    # Side Menu #
    #############
    # Whether to display the side menu
    "show_sidebar": True,
    # Whether to aut expand the menu
    "navigation_expanded": False,
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
    },
    # Icons that are used when one is not manually specified
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    #################
    # Related Modal #
    #################
    # Use modals instead of popups
    "related_modal_active": False,
}

# swagger
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "basic": {"type": "basic"},
        "api_key": {"type": "apiKey", "in": "header", "name": "Authorization"},
    },
    "DOC_EXPANSION": "None",
    "FETCH_SCHEMA_WITH_QUERY": True,
    "LOGOUT_URL": "/admin/logout/",
    "LOGIN_URL": "/admin/login/",
    "DEFAULT_MODEL_RENDERING": "example",
    "DEFAULT_FIELD_INSPECTORS": [
        "drf_yasg.inspectors.CamelCaseJSONFilter",
        "drf_yasg.inspectors.InlineSerializerInspector",
        "drf_yasg.inspectors.RelatedFieldInspector",
        "drf_yasg.inspectors.ChoiceFieldInspector",
        "drf_yasg.inspectors.FileFieldInspector",
        "drf_yasg.inspectors.DictFieldInspector",
        "drf_yasg.inspectors.SimpleFieldInspector",
        "drf_yasg.inspectors.StringDefaultFieldInspector",
    ],
}

# settings.py

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {message}",
            "style": "{",
        },
        "json": {
            "format": '{{"level": "{levelname}", "time": "{asctime}", "name": "{name}", "module": "{module}", "message": "{message}"}}',
            "style": "{",
        },
        "security": {
            "format": "SECURITY {levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG" if DEBUG else "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/api_requests.log",
            "maxBytes": 50 * 1024 * 1024,  # 50MB
            "backupCount": 10,
            "formatter": "verbose",
        },
        "error_file": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/api_errors.log",
            "maxBytes": 50 * 1024 * 1024,  # 50MB
            "backupCount": 10,
            "formatter": "verbose",
        },
        "security_file": {
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/security.log",
            "maxBytes": 50 * 1024 * 1024,  # 50MB
            "backupCount": 10,
            "formatter": "security",
        },
        "auth_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/auth.log",
            "maxBytes": 20 * 1024 * 1024,  # 20MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "business_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/business.log",
            "maxBytes": 20 * 1024 * 1024,  # 20MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "celery_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/celery.log",
            "maxBytes": 20 * 1024 * 1024,  # 20MB
            "backupCount": 5,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"] if DEBUG else ["file"],
            "level": "INFO",
            "propagate": True,
        },
        "django.request": {
            "handlers": ["file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["security_file", "error_file"],
            "level": "WARNING",
            "propagate": False,
        },
        "api_errors": {
            "handlers": ["error_file", "console"] if DEBUG else ["error_file"],
            "level": "ERROR",
            "propagate": False,
        },
        "auth": {
            "handlers": ["auth_file", "console"] if DEBUG else ["auth_file"],
            "level": "INFO",
            "propagate": False,
        },
        "business": {
            "handlers": ["business_file", "console"] if DEBUG else ["business_file"],
            "level": "INFO",
            "propagate": False,
        },
        "security": {
            "handlers": ["security_file", "error_file"],
            "level": "WARNING",
            "propagate": False,
        },
        "celery": {
            "handlers": ["celery_file", "console"] if DEBUG else ["celery_file"],
            "level": "INFO",
            "propagate": False,
        },
        "celery.task": {
            "handlers": ["celery_file"],
            "level": "INFO",
            "propagate": False,
        },
        # Application specific loggers
        "app_modules.account": {
            "handlers": ["auth_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "app_modules.post": {
            "handlers": ["business_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "app_modules.master": {
            "handlers": ["business_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "app_modules.website": {
            "handlers": ["business_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"] if DEBUG else ["file"],
    },
}


# ---------------------------- Sentry Configuration ------------------------
def before_send(event, hint):
    """
    Custom event processing before sending to Sentry.
    Filter out sensitive data and add custom context.
    """
    # Filter out events from health check endpoints
    if event.get("request", {}).get("url", "").endswith("/health/"):
        return None

    # Filter out specific error types that are not actionable
    if "exception" in event:
        exc_info = event["exception"]["values"][0]
        if (
            exc_info.get("type") in ["ConnectionError", "TimeoutError"]
            and "redis" in str(exc_info.get("value", "")).lower()
        ):
            # Don't spam Sentry with Redis connection issues
            return None

    # Add custom tags for better error grouping
    event.setdefault("tags", {})
    event["tags"]["environment"] = env.str("ENVIRONMENT", "development")

    # Add user context if available
    if "request" in event and hasattr(event.get("request", {}), "user"):
        user = event["request"].user
        if user and hasattr(user, "id"):
            event.setdefault("user", {}).update(
                {
                    "id": user.id,
                    "email": getattr(user, "email", None),
                    "username": getattr(user, "username", None),
                }
            )

    return event


# Sentry Integrations Configuration
sentry_logging = LoggingIntegration(
    level=logging.INFO,  # Capture info and above as breadcrumbs
    event_level=logging.ERROR,  # Send errors as events
)

django_integration = DjangoIntegration(
    transaction_style="url",
    middleware_spans=True,
    signals_spans=True,
    cache_spans=True,
)

celery_integration = CeleryIntegration(
    monitor_beat_tasks=True,
    propagate_traces=True,
)

redis_integration = RedisIntegration()

stdlib_integration = StdlibIntegration()

excepthook_integration = ExcepthookIntegration(always_run=True)

# Environment-specific configuration
SENTRY_ENVIRONMENT = env.str("ENVIRONMENT", "development")
SENTRY_RELEASE = env.str("SENTRY_RELEASE", None)  # Set this in deployment

# Performance monitoring configuration
if DEBUG:
    # Development environment - higher sampling for testing
    traces_sample_rate = 1.0
    profiles_sample_rate = 1.0
elif SENTRY_ENVIRONMENT == "staging":
    # Staging environment - moderate sampling
    traces_sample_rate = 0.5
    profiles_sample_rate = 0.3
else:
    # Production environment - conservative sampling
    traces_sample_rate = 0.1
    profiles_sample_rate = 0.05

sentry_sdk.init(
    dsn="https://5c75dac3f54472df756b133e6854adc7@o4509779494305792.ingest.us.sentry.io/4509779511738368",
    # Integrations
    integrations=[
        django_integration,
        celery_integration,
        redis_integration,
        sentry_logging,
        stdlib_integration,
        excepthook_integration,
    ],
    # Environment and Release Tracking
    environment=SENTRY_ENVIRONMENT,
    release=SENTRY_RELEASE,
    # Performance Monitoring
    traces_sample_rate=traces_sample_rate,
    profiles_sample_rate=profiles_sample_rate,
    # Error Filtering and Processing
    before_send=before_send,
    # Additional Configuration
    debug=DEBUG,
    attach_stacktrace=True,
    send_default_pii=False,  # Don't send personally identifiable information
    # Performance options
    enable_tracing=True,
    max_breadcrumbs=50,
    # Custom fingerprinting for better error grouping
    default_integrations=False,  # We explicitly define integrations above
)
