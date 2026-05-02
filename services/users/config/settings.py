import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "apps",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"
DB_ENGINE = os.environ.get("DB_ENGINE", "postgresql").lower()

# if DB_ENGINE == "postgresql":
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("USERS_POSTGRES_DB", "users_db"),
        "USER": os.environ.get("USERS_POSTGRES_USER", "users_user"),
        "PASSWORD": os.environ.get("USERS_POSTGRES_PASSWORD", "users_pass"),
        "HOST": os.environ.get("USERS_POSTGRES_HOST", "db-users-pg"),
        "PORT": os.environ.get("USERS_POSTGRES_PORT", "5432"),
    }
}
# else:
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db.sqlite3",
#     }
# }

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

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    # (login) Configuración de autenticación JWT
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}

# (login) Configuración de JWT para tokens de acceso y refresh
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        hours=1
    ),  # (login) Token de acceso válido por 1 hora
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=7
    ),  # (login) Token de refresh válido por 7 días
    "ALGORITHM": "HS256",  # (login) Algoritmo de firma JWT
    "SIGNING_KEY": SECRET_KEY,  # (login) Clave para firmar tokens
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Users Service API",
    "DESCRIPTION": "API documentation for users microservice",
    "VERSION": "1.0.0",
    "SERVERS": [
        {
            "url": "/user/api/v1",
            "description": "Gateway base URL",
        }
    ],
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
        "core.schema.inject_gateway_servers",
    ],
    "SECURITY": [{"BearerAuth": []}],
    "COMPONENTS": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Agregar el token en el header Authorization: Bearer <token>",
            }
        }
    },
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
        "displayRequestDuration": True,
    },
}

AUTH_USER_MODEL = "apps.User"

# (reset) Configuración de email - Console backend para desarrollo
# (reset) Los correos se imprimen en la terminal/logs del contenedor
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"  # (reset)
DEFAULT_FROM_EMAIL = "noreply@plataforma.com"  # (reset)
