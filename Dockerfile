# Dockerfile pour l'application de gestion hospitalière

# Étape 1: Construction de l'image de base
FROM python:3.11-slim as base

# Définir les variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    gettext \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements/ requirements/
COPY requirements.txt requirements.txt

# Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements/production.txt

# Étape 2: Construction de l'application
FROM base as builder

# Copier le code de l'application
COPY . .

# Créer les répertoires nécessaires
RUN mkdir -p /app/logs /app/static /app/media

# Compiler les fichiers de traduction
RUN python manage.py compilemessages

# Collecter les fichiers statiques
RUN python manage.py collectstatic --noinput

# Étape 3: Image de production
FROM base as production

# Créer un utilisateur non root pour la sécurité
RUN groupadd -r django && useradd -r -g django django

# Copier les fichiers depuis l'étape de construction
COPY --from=builder --chown=django:django /app /app

# Créer les répertoires nécessaires avec les bonnes permissions
RUN mkdir -p /app/logs /app/static /app/media && \
    chown -R django:django /app

# Changer vers l'utilisateur django
USER django

# Exposer le port
EXPOSE 8000

# Variables d'environnement pour la production
ENV DJANGO_SETTINGS_MODULE=hospital_project.settings.production

# Commande pour exécuter l'application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", "--max-requests", "1000", "--max-requests-jitter", "50", "--access-logfile", "-", "--error-logfile", "-", "hospital_project.wsgi:application"]