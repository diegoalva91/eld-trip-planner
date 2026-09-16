from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-secret-key")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = [x.strip() for x in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if x.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "trips",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = [
    x.strip()
    for x in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if x.strip()
]
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}

# ---------------------------------------------------------------------------
# OpenStreetMap / Nominatim / OSRM configuration
# ---------------------------------------------------------------------------
# Geocoding uses the public Nominatim service directly. Nominatim requires a
# custom application User-Agent and limits public clients to at most 1 request
# per second. Set NOMINATIM_CONTACT_EMAIL in .env when you have a contact email.
NOMINATIM_BASE_URL = os.getenv(
    "NOMINATIM_BASE_URL",
    "https://nominatim.openstreetmap.org",
).rstrip("/")
NOMINATIM_USER_AGENT = os.getenv(
    "NOMINATIM_USER_AGENT",
    "ELDTripPlanner/2.0",
).strip()
NOMINATIM_CONTACT_EMAIL = os.getenv("NOMINATIM_CONTACT_EMAIL", "").strip()
NOMINATIM_MIN_INTERVAL_SECONDS = max(
    float(os.getenv("NOMINATIM_MIN_INTERVAL_SECONDS", "1.1")),
    1.0,
)
NOMINATIM_CACHE_SECONDS = int(os.getenv("NOMINATIM_CACHE_SECONDS", str(60 * 60 * 24 * 30)))

# OSRM's public demo service is used only to calculate the driving route and
# turn-by-turn instructions from coordinates returned by Nominatim.
OSRM_BASE_URL = os.getenv(
    "OSRM_BASE_URL",
    "https://router.project-osrm.org/route/v1/driving",
).rstrip("/")
