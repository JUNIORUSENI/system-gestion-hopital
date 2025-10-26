# 🚀 GUIDE DE DÉPLOIEMENT - Corrections RDC

Ce fichier contient toutes les étapes pour appliquer les corrections au système.

---

## ⚠️ AVANT DE COMMENCER

**IMPORTANT** : Faites une sauvegarde de votre base de données avant de continuer !

```bash
# Sauvegarde SQLite
cp db.sqlite3 db.sqlite3.backup

# Sauvegarde PostgreSQL
pg_dump hospital_db > backup_$(date +%Y%m%d).sql
```

---

## 📝 ÉTAPE 1 : VÉRIFIER L'ENVIRONNEMENT

```bash
# Activer l'environnement virtuel
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# Vérifier que Django est installé
python manage.py --version
```

---

## 🗄️ ÉTAPE 2 : CRÉER LES MIGRATIONS

```bash
# Créer les nouvelles migrations pour les modifications de modèles
python manage.py makemigrations hospital
```

**Vous devriez voir** :
```
Migrations for 'hospital':
  hospital/migrations/000X_auto_YYYYMMDD_HHMM.py
    - Add index to patient on fields ['last_name', 'first_name']
    - Add index to patient on fields ['date_of_birth']
    - Alter field phone on patient
    - Alter field emergency_contact on patient
    - ... (autres changements)
```

---

## 🔄 ÉTAPE 3 : APPLIQUER LES MIGRATIONS

```bash
# Afficher les migrations en attente
python manage.py showmigrations hospital

# Appliquer toutes les migrations
python manage.py migrate hospital
```

**Résultat attendu** :
```
Running migrations:
  Applying hospital.000X_auto_YYYYMMDD_HHMM... OK
```

---

## 👤 ÉTAPE 4 : CONFIGURER LES PROFILS UTILISATEURS

### Option A : Créer un nouveau superuser

```bash
python manage.py createsuperuser
```

**Suivre les instructions** :
- Username : `admin`
- Email : votre email
- Password : votre mot de passe

### Option B : Utiliser l'admin existant

1. Aller sur **http://localhost:8000/admin/**
2. Se connecter avec votre compte admin
3. Cliquer sur **Profiles**
4. **Créer ou modifier** les profils :

#### Créer un MEDICAL_ADMIN
- User : Sélectionner utilisateur
- Role : **MEDICAL_ADMIN** (Médecin Administrateur)
- Centres : Sélectionner les centres (optionnel pour MEDICAL_ADMIN car accès global)

#### Créer un DOCTOR
- User : Sélectionner utilisateur
- Role : **DOCTOR**
- Centres : Sélectionner les centres où il travaille

#### Créer un NURSE
- User : Sélectionner utilisateur  
- Role : **NURSE**
- Centres : **Obligatoire** - Sélectionner ses centres

#### Créer un SECRETARY
- User : Sélectionner utilisateur
- Role : **SECRETARY**
- Centres : **Obligatoire** - Sélectionner ses centres

---

## 🧪 ÉTAPE 5 : TESTER LE SYSTÈME

### Test 1 : Créer un Patient avec Téléphone RDC

```bash
# Lancer le serveur
python manage.py runserver
```

1. Aller sur **http://localhost:8000**
2. Se connecter
3. **Patients** > **Nouveau Patient**
4. Remplir avec :
   - Nom : TEST
   - Prénom : Patient
   - Date de naissance : 01/01/1990
   - Téléphone : **+243812345678** ou **0812345678**
5. Cliquer **Enregistrer**

**Attendu** : Patient créé avec succès ✅

### Test 2 : Tester Téléphone Invalide

1. Essayer avec : `123456789` (sans +243)
2. **Attendu** : Message d'erreur "Format congolais requis : +243XXXXXXXXX ou 0XXXXXXXXX"

### Test 3 : Tester les Filtres

1. Aller sur **Patients**
2. Utiliser la recherche : taper un nom
3. **Attendu** : Résultats filtrés en temps réel (500ms)
4. Essayer les filtres (Centre, Genre, Statut)
5. Cliquer sur page 2
6. **Attendu** : Filtres préservés ✅

### Test 4 : Dashboard DOCTOR

1. Se connecter en tant que DOCTOR
2. Aller sur dashboard
3. **Vérifier** :
   - Voit uniquement SES patients
   - Voit uniquement SES consultations
   - Liens vers pages dédiées fonctionnent
4. Cliquer sur "Mes Consultations"
5. **Attendu** : Tableau complet de toutes ses consultations

### Test 5 : Notes Hospitalisations

1. Se connecter en tant que NURSE
2. Aller sur une hospitalisation active
3. Cliquer **Éditer**
4. **Vérifier** :
   - Section "Notes Infirmières" visible
   - Section "Notes Médicales" grisée/masquée
5. Ajouter une note infirmière
6. **Enregistrer**
7. **Attendu** : Note ajoutée avec date/heure ✅

### Test 6 : MEDICAL_ADMIN

1. Se connecter en tant que MEDICAL_ADMIN
2. **Vérifier** :
   - Dashboard global (comme ADMIN)
   - Peut créer consultations (comme DOCTOR)
   - Peut gérer utilisateurs dans /admin/
   - Peut tout faire

---

## 🔍 ÉTAPE 6 : VÉRIFIER LES LOGS

### En cas d'erreur

```bash
# Afficher les logs Django
python manage.py runserver

# Consulter les erreurs
# Vérifier dans le terminal les messages d'erreur
```

### Erreurs communes

#### Erreur : "No such table"
```bash
python manage.py migrate
```

#### Erreur : "Permission Denied"
Vérifier que l'utilisateur a un profil avec un rôle dans `/admin/`

#### Erreur : "Invalid phone number"
Utiliser le format : `+243XXXXXXXXX` ou `0XXXXXXXXX`

---

## 📊 ÉTAPE 7 : VALIDATION FINALE

### Checklist de Validation

- [ ] Migrations appliquées sans erreur
- [ ] Au moins un utilisateur de chaque rôle créé
- [ ] Patient créé avec téléphone RDC valide
- [ ] Filtres patients fonctionnent
- [ ] Dashboard DOCTOR affiche ses données uniquement
- [ ] Dashboard MEDICAL_ADMIN affiche vue globale
- [ ] Espace médecin (4 pages) accessibles
- [ ] Notes hospitalisations ajoutables
- [ ] Recherche par ID fonctionne
- [ ] Formulaires tous au même style

---

## 🎯 ÉTAPE 8 : PROCHAINES ACTIONS (OPTIONNEL)

### Données de Test

Pour tester avec des données réalistes :

```bash
# Créer un fichier populate_db.py
python scripts/populate_db.py
```

### Performance

Pour optimiser davantage :

```bash
# Installer django-debug-toolbar (développement)
pip install django-debug-toolbar

# Analyser les requêtes SQL
# Vérifier nombre de requêtes par page
```

### Sécurité

```bash
# Vérifier les vulnérabilités
pip install safety
safety check

# Audit Django
python manage.py check --deploy
```

---

## 📞 EN CAS DE PROBLÈME

### Revenir en arrière

Si quelque chose ne fonctionne pas :

```bash
# Restaurer la base de données
cp db.sqlite3.backup db.sqlite3

# OU pour PostgreSQL
psql hospital_db < backup_YYYYMMDD.sql

# Revenir à la migration précédente
python manage.py migrate hospital 000X  # Numéro de la dernière migration fonctionnelle
```

### Consulter la Documentation

1. [`Rapport.md`](Rapport.md:1) - Analyse complète
2. [`CORRECTIONS_APPLIQUEES.md`](CORRECTIONS_APPLIQUEES.md:1) - Détails techniques
3. [`README.md`](README.md:1) - Guide d'utilisation

---

## ✅ CONFIRMATION DE DÉPLOIEMENT RÉUSSI

Une fois toutes les étapes complétées :

- ✅ Migrations appliquées
- ✅ Profils utilisateurs configurés
- ✅ Tests de validation passés
- ✅ Aucune erreur dans les logs
- ✅ Système accessible et fonctionnel

**FÉLICITATIONS !** 🎉

Votre système de gestion hospitalière est maintenant :
- Adapté au contexte RDC 🇨🇩
- Performant et optimisé
- Avec permissions cohérentes
- Prêt pour la production

---

**Date de déploiement** : _________________  
**Déployé par** : _________________  
**Statut** : ☐ Succès ☐ Erreurs (détailler)

**Notes** :
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________