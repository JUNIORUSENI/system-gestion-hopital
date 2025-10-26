# 🚀 GUIDE COMPLET DE DÉPLOIEMENT - RDC Hospital Management

**Système de Gestion Hospitalière pour la RDC**

---

## 📋 TABLE DES MATIÈRES

1. [Développement Local](#-développement-local)
2. [Production avec Docker](#-production-avec-docker)
3. [Base de Données Externe (Prisma Postgres)](#-base-de-données-externe)
4. [Configuration Nginx](#-configuration-nginx)
5. [SSL/HTTPS](#-ssl

https)
6. [Dépannage](#-dépannage)

---

## 💻 DÉVELOPPEMENT LOCAL

### Prérequis
- Python 3.8+
- pip
- Git
- (Optionnel) PostgreSQL local

### Installation Rapide

```bash
# 1. Cloner le projet
git clone <url-du-repo>
cd hospitalManagement

# 2. Créer environnement virtuel
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 3. Installer les dépendances
pip install -r requirements/development.txt

# 4. Créer le fichier .env
cp .env.example .env

# 5. Modifier .env pour développement
# DEBUG=True
# DATABASE_URL=sqlite:///db.sqlite3

# 6. Appliquer les migrations
python manage.py makemigrations
python manage.py migrate

# 7. Créer un superutilisateur
python manage.py createsuperuser

# 8. Créer les profils dans /admin/
# - Aller sur http://localhost:8000/admin/
# - Créer un profil pour chaque utilisateur avec un rôle

# 9. Lancer le serveur
python manage.py runserver
```

**Accéder à** : http://localhost:8000

### Structure Développement

```
hospitalManagement/
├── venv/                 # Environnement virtuel (ignoré par Git)
├── db.sqlite3            # Base SQLite (ignoré par Git)
├── .env                  # Variables d'environnement (ignoré par Git)
├── manage.py
├── hospital/             # Application principale
└── hospital_project/     # Configuration Django
```

---

## 🐳 PRODUCTION AVEC DOCKER

### Option 1 : Docker avec Base PostgreSQL Locale

**Utilise** : `docker-compose.yml`

```bash
# 1. Créer le fichier .env
cp .env.example .env

# 2. Modifier .env
SECRET_KEY=<générer-une-nouvelle-clé>
DEBUG=False
ALLOWED_HOSTS=votredomaine.com
DB_NAME=hospital_db
DB_USER=hospital_user
DB_PASSWORD=<mot-de-passe-fort>

# 3. Lancer tous les services
docker-compose up -d --build

# 4. Vérifier les logs
docker-compose logs -f web

# 5. Créer un superutilisateur
docker-compose exec web python manage.py createsuperuser

# 6. Accéder à l'application
http://localhost:8000
```

**Services inclus** :
- ✅ PostgreSQL (base de données locale)
- ✅ Redis (cache)
- ✅ Web Django (Gunicorn)
- ✅ Nginx (reverse proxy)
- ✅ Celery (tâches asynchrones)

### Option 2 : Docker avec Base Externe (Prisma Postgres)

**Utilise** : `docker-compose.prod.yml`

```bash
# 1. Créer le fichier .env
cp .env.production.example .env

# 2. Modifier .env avec vos identifiants Prisma Postgres
SECRET_KEY=<votre-clé-secrète-unique>
DEBUG=False
ALLOWED_HOSTS=votredomaine.com
DATABASE_URL=postgresql://user:password@host:port/database_name

# 3. Lancer les services (sans PostgreSQL local)
docker-compose -f docker-compose.prod.yml up -d --build

# 4. Vérifier les logs
docker-compose -f docker-compose.prod.yml logs -f web

# 5. Créer un superutilisateur
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# 6. Accéder à l'application
http://localhost:8000
```

**Services inclus** :
- ✅ Web Django (Gunicorn)
- ✅ Nginx (reverse proxy)
- ⚠️ PostgreSQL EXTERNE (Prisma, Neon, Supabase, etc.)
- ⚠️ Redis EXTERNE (optionnel)

---

## 🗄️ BASE DE DONNÉES EXTERNE

### Prisma Postgres

**1. Créer un compte Prisma**
- Aller sur https://www.prisma.io/
- Créer un nouveau projet
- Obtenir l'URL de connexion

**2. URL de Connexion**
```
postgresql://username:password@aws-0-eu-central-1.pooler.supabase.com:5432/postgres?sslmode=require
```

**3. Configurer .env**
```bash
DATABASE_URL=postgresql://username:password@aws-0-eu-central-1.pooler.supabase.com:5432/postgres
```

**4. Appliquer les migrations**
```bash
# Depuis votre machine locale
python manage.py migrate

# OU depuis Docker
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### Autres Fournisseurs Compatibles

#### Neon (PostgreSQL Serverless)
```bash
DATABASE_URL=postgresql://user:password@ep-cool-darkness-123456.eu-central-1.aws.neon.tech/neondb?sslmode=require
```

#### Supabase (PostgreSQL Hébergé)
```bash
DATABASE_URL=postgresql://postgres:password@db.abcdefghijk.supabase.co:5432/postgres
```

#### Railway (PostgreSQL)
```bash
DATABASE_URL=postgresql://postgres:password@containers-us-west-123.railway.app:5432/railway
```

#### ElephantSQL
```bash
DATABASE_URL=postgresql://user:password@silly.db.elephantsql.com:5432/database
```

---

## 🌐 CONFIGURATION NGINX

### Créer le fichier de configuration

**Fichier** : `docker/nginx/prod.conf`

```nginx
upstream django {
    server web:8000;
}

server {
    listen 80;
    server_name votredomaine.com www.votredomaine.com;
    charset utf-8;
    client_max_body_size 75M;

    # Logs
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Fichiers statiques
    location /static/ {
        alias /app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Fichiers media
    location /media/ {
        alias /app/media/;
        expires 30d;
    }

    # Requêtes Django
    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_connect_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### Configuration HTTPS (Recommandé)

```nginx
server {
    listen 80;
    server_name votredomaine.com www.votredomaine.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name votredomaine.com www.votredomaine.com;
    
    # Certificats SSL
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    # Configuration SSL moderne
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Reste de la configuration identique...
}
```

---

## 🔐 SSL/HTTPS

### Option 1 : Let's Encrypt (Gratuit)

```bash
# Installer Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtenir un certificat
sudo certbot --nginx -d votredomaine.com -d www.votredomaine.com

# Renouvellement automatique
sudo certbot renew --dry-run
```

### Option 2 : Certificat auto-signé (Développement)

```bash
# Créer le dossier
mkdir -p docker/ssl

# Générer le certificat
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout docker/ssl/privkey.pem \
  -out docker/ssl/fullchain.pem \
  -subj "/C=CD/ST=Kinshasa/L=Kinshasa/O=Hospital/CN=localhost"
```

---

## 🚀 DÉPLOIEMENT PRODUCTION COMPLET

### Étape 1 : Préparer l'Environnement

```bash
# 1. Cloner sur le serveur
git clone <url-du-repo>
cd hospitalManagement

# 2. Créer .env
cp .env.production.example .env
nano .env  # Modifier avec vos valeurs

# 3. Générer SECRET_KEY
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# 4. Mettre à jour .env avec :
# - SECRET_KEY (généré ci-dessus)
# - DATABASE_URL (URL Prisma Postgres)
# - ALLOWED_HOSTS (votre domaine)
# - DEBUG=False
```

### Étape 2 : Configuration Base de Données

**Prisma Postgres** :

```bash
# 1. Aller sur https://prisma.io/
# 2. Créer un nouveau projet
# 3. Région : Europe (proche RDC)
# 4. Copier l'URL de connexion

# Format de l'URL :
DATABASE_URL=postgresql://user:password@aws-0-eu-central-1.pooler.supabase.com:5432/postgres?sslmode=require
```

### Étape 3 : Construire et Lancer

```bash
# Avec base externe (Prisma)
docker-compose -f docker-compose.prod.yml up -d --build

# Vérifier le statut
docker-compose -f docker-compose.prod.yml ps

# Voir les logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Étape 4 : Initialisation

```bash
# 1. Créer superutilisateur
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Entrer :
# - Username : admin
# - Email : admin@votredomaine.com
# - Password : <mot-de-passe-fort>

# 2. Créer les profils utilisateurs
# Aller sur https://votredomaine.com/admin/
# Se connecter avec le superuser
# Créer des profils avec rôles (MEDICAL_ADMIN, DOCTOR, etc.)
```

### Étape 5 : Vérification

```bash
# Tester l'application
curl https://votredomaine.com

# Vérifier la base de données
docker-compose -f docker-compose.prod.yml exec web python manage.py dbshell

# Vérifier les migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py showmigrations
```

---

## 🔧 COMMANDES UTILES

### Docker

```bash
# Reconstruire l'image
docker-compose -f docker-compose.prod.yml build --no-cache

# Redémarrer les services
docker-compose -f docker-compose.prod.yml restart

# Arrêter les services
docker-compose -f docker-compose.prod.yml down

# Voir les logs
docker-compose -f docker-compose.prod.yml logs -f web

# Exécuter une commande Django
docker-compose -f docker-compose.prod.yml exec web python manage.py <commande>

# Accéder au shell Django
docker-compose -f docker-compose.prod.yml exec web python manage.py shell

# Backup base de données (si PostgreSQL local)
docker-compose exec db pg_dump -U hospital_user hospital_db > backup.sql
```

### Django

```bash
# Créer migrations
python manage.py makemigrations

# Appliquer migrations
python manage.py migrate

# Collecter fichiers statiques
python manage.py collectstatic --noinput

# Créer superuser
python manage.py createsuperuser

# Shell Django
python manage.py shell

# Tests
python manage.py test
```

---

## 🎯 CONFIGURATION PAR ENVIRONNEMENT

### Développement (.env)

```bash
DEBUG=True
SECRET_KEY=dev-secret-key-not-for-production
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Production (.env)

```bash
DEBUG=False
SECRET_KEY=<clé-unique-très-longue-générée>
DATABASE_URL=postgresql://user:pass@host:port/db
ALLOWED_HOSTS=votredomaine.com,www.votredomaine.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

---

## 📊 MONITORING ET MAINTENANCE

### Logs

```bash
# Logs application
docker-compose -f docker-compose.prod.yml logs -f web

# Logs Nginx
docker-compose -f docker-compose.prod.yml logs -f nginx

# Logs tous services
docker-compose -f docker-compose.prod.yml logs -f
```

### Performance

```bash
# Vérifier utilisation ressources
docker stats

# Optimiser base de données
docker-compose -f docker-compose.prod.yml exec web python manage.py dbshell
# Puis : VACUUM ANALYZE;

# Nettoyer sessions expirées
docker-compose -f docker-compose.prod.yml exec web python manage.py clearsessions
```

### Backup

```bash
# Backup BDD externe (Prisma) - Automatique !
# Prisma Postgres fait des backups automatiques

# Backup fichiers media
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/

# Backup fichiers statiques
tar -czf static_backup_$(date +%Y%m%d).tar.gz static/
```

---

## 🔒 SÉCURITÉ

### Checklist Sécurité Production

- [ ] DEBUG=False
- [ ] SECRET_KEY unique et complexe
- [ ] ALLOWED_HOSTS configuré correctement
- [ ] HTTPS activé (SSL)
- [ ] Certificat SSL valide
- [ ] Base de données avec mot de passe fort
- [ ] Firewall configuré
- [ ] Mises à jour régulières
- [ ] Backups automatiques
- [ ] Monitoring actif

### Générer SECRET_KEY Sécurisée

```python
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### Configuration Firewall

```bash
# Ubuntu/Debian
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 22/tcp    # SSH
sudo ufw enable
```

---

## 🌍 DÉPLOIEMENT SUR SERVEUR CLOUD

### Option A : DigitalOcean

```bash
# 1. Créer un Droplet Ubuntu 22.04
# 2. SSH dans le serveur
ssh root@votre-ip

# 3. Installer Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 4. Installer Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 5. Cloner le projet
git clone <url-du-repo>
cd hospitalManagement

# 6. Configurer .env
nano .env

# 7. Lancer
docker-compose -f docker-compose.prod.yml up -d --build
```

### Option B : AWS EC2

```bash
# 1. Lancer une instance EC2 Ubuntu
# 2. Configurer Security Groups :
#    - Port 80 (HTTP)
#    - Port 443 (HTTPS)
#    - Port 22 (SSH)

# 3. SSH dans l'instance
ssh -i your-key.pem ubuntu@ec2-xx-xx-xx-xx.compute.amazonaws.com

# 4. Suivre les mêmes étapes que DigitalOcean
```

### Option C : Render.com

```bash
# 1. Créer compte sur render.com
# 2. Nouveau Web Service
# 3. Connecter votre repo GitHub
# 4. Configuration :
#    - Environment : Docker
#    - Docker Command : (automatique)
#    - Environment Variables : 
#      * SECRET_KEY
#      * DATABASE_URL
#      * ALLOWED_HOSTS
# 5. Deploy !
```

---

## 🔄 MISES À JOUR

### Mettre à jour le code

```bash
# 1. Pull les derniers changements
git pull origin main

# 2. Reconstruire l'image Docker
docker-compose -f docker-compose.prod.yml build --no-cache

# 3. Arrêter les services
docker-compose -f docker-compose.prod.yml down

# 4. Relancer avec les nouvelles images
docker-compose -f docker-compose.prod.yml up -d

# 5. Appliquer les migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# 6. Collecter les fichiers statiques
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

---

## 🐛 DÉPANNAGE

### Problème : "No module named 'hospital'"

```bash
# Vérifier que vous êtes dans le bon dossier
pwd

# Vérifier PYTHONPATH
docker-compose -f docker-compose.prod.yml exec web python -c "import sys; print(sys.path)"
```

### Problème : "Database connection failed"

```bash
# Vérifier DATABASE_URL
docker-compose -f docker-compose.prod.yml exec web env | grep DATABASE_URL

# Tester la connexion depuis Python
docker-compose -f docker-compose.prod.yml exec web python manage.py dbshell
```

### Problème : "Static files not found"

```bash
# Collecter les fichiers statiques
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Vérifier les permissions
docker-compose -f docker-compose.prod.yml exec web ls -la /app/static
```

### Problème : "Permission Denied"

```bash
# Vérifier que l'utilisateur a un profil
# Aller dans /admin/ > Profiles
# Créer un profil si manquant
```

### Problème : "502 Bad Gateway"

```bash
# Vérifier que l'application web tourne
docker-compose -f docker-compose.prod.yml ps

# Redémarrer le service web
docker-compose -f docker-compose.prod.yml restart web

# Voir les logs
docker-compose -f docker-compose.prod.yml logs -f web
```

---

## 📝 CHECKLIST DÉPLOIEMENT

### Avant le déploiement

- [ ] Tests passent localement
- [ ] .env configuré correctement
- [ ] SECRET_KEY généré et sécurisé
- [ ] DATABASE_URL correct
- [ ] ALLOWED_HOSTS configuré
- [ ] DEBUG=False
- [ ] Fichiers sensibles dans .gitignore

### Après le déploiement

- [ ] Application accessible
- [ ] Superuser créé
- [ ] Profils utilisateurs créés
- [ ] Base de données migrée
- [ ] Fichiers statiques collectés
- [ ] SSL/HTTPS fonctionnel
- [ ] Logs sans erreurs
- [ ] Backup configuré

---

## 💡 BONNES PRATIQUES

### 1. Sécurité

```bash
# Changer le mot de passe admin régulièrement
docker-compose -f docker-compose.prod.yml exec web python manage.py changepassword admin

# Activer 2FA pour les comptes admin
# (À implémenter dans Django Admin)

# Audit de sécurité
pip install safety
safety check
```

### 2. Performance

```bash
# Activer le cache Redis
REDIS_URL=redis://...

# Optimiser PostgreSQL
# Dans psql :
# CREATE INDEX CONCURRENTLY idx_name ON table(column);

# Monitoring avec Sentry
SENTRY_DSN=https://...@sentry.io/...
```

### 3. Backup

```bash
# Script de backup automatique (crontab)
0 2 * * * cd /path/to/app && docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U user dbname > backup_$(date +\%Y\%m\%d).sql
```

---

## 📞 SUPPORT

### Erreur Critique

1. Vérifier les logs : `docker-compose logs -f`
2. Consulter [`DEPLOIEMENT.md`](DEPLOIEMENT.md:1)
3. Consulter [`README.md`](README.md:1)

### Ressources

- **Documentation Django** : https://docs.djangoproject.com/
- **Docker** : https://docs.docker.com/
- **Prisma Postgres** : https://www.prisma.io/docs/

---

## ✅ RÉSUMÉ RAPIDE

### Développement

```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements/development.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Production (Base Externe)

```bash
cp .env.production.example .env
# Modifier .env avec DATABASE_URL de Prisma
docker-compose -f docker-compose.prod.yml up -d --build
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

---

**Date** : 26 Octobre 2025  
**Version** : 2.0  
**Statut** : ✅ Production Ready