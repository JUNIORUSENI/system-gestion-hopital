"""
Configuration pour l'environnement de développement
"""
from .base import *
from decouple import config

# Mode debug activé pour le développement
DEBUG = True

# Hôtes autorisés pour le développement
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

# Configuration de la base de données pour le développement
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Configuration du cache pour le développement (cache en mémoire)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Configuration email pour le développement (console backend)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Désactiver la sécurité des cookies pour le développement
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Configuration des outils de débogage
INSTALLED_APPS += [
    'debug_toolbar',
]

MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

INTERNAL_IPS = [
    '127.0.0.1',
]

# Logging détaillé pour le développement
LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['hospital']['level'] = 'DEBUG'