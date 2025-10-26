"""
Configuration pour l'environnement de test
"""
from .base import *

# Mode debug désactivé pour les tests
DEBUG = False

# Hôtes autorisés pour les tests
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

# Configuration de la base de données pour les tests (en mémoire)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Configuration du cache pour les tests (cache en mémoire)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Configuration email pour les tests (backend de test)
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Désactiver la sécurité des cookies pour les tests
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Configuration des mots de passe pour les tests (moins restrictive)
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 4,
        }
    },
]

# Logging minimal pour les tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

# Media files pour les tests
MEDIA_ROOT = '/tmp/hospital_test_media/'