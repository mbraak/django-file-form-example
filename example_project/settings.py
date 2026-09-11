"""
Django settings for the django-file-form example project.

Only the settings relevant to django-file-form are commented; the rest is the
standard Django scaffold.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Development-only key. Never use this in production.
SECRET_KEY = "django-insecure-example-key-XV6Uwvpnh5HKmZFxi9_XLz36p34GhCW8jfon"

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # django-file-form provides the TemporaryUploadedFile model, the tus upload
    # endpoints and the static assets (file_form.js / file_form.css).
    "django_file_form",
    # The example app.
    "uploads",
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

ROOT_URLCONF = "example_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "example_project.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"  # noqa: E501
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

# django-file-form stores uploads under MEDIA_ROOT, so MEDIA_ROOT is required.
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "media/"

# --- django-file-form settings -------------------------------------------
# Directory (relative to MEDIA_ROOT) for files that are uploaded via tus but
# not yet attached to a saved form. Default: "temp_uploads".
FILE_FORM_UPLOAD_DIR = "temp_uploads"
# Require an authenticated user for the upload endpoints. Default: False.
FILE_FORM_MUST_LOGIN = False
# The tus upload endpoint keeps upload progress in the Django cache.
FILE_FORM_CACHE = "default"
FILE_FORM_CACHE_TIMEOUT = 3600 * 24

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
