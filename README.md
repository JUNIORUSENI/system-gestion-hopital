# 🏥 Système de Gestion Hospitalière - RDC

Un système complet de gestion hospitalière adapté au contexte de la République Démocratique du Congo, développé avec Django.

## 📋 Table des Matières
- [Fonctionnalités](#-fonctionnalités)
- [Technologies](#-technologies)
- [Installation](#-installation)
- [Configuration](#️-configuration)
- [Utilisation](#-utilisation)
- [Rôles et Permissions](#-rôles-et-permissions)
- [Structure du Projet](#-structure-du-projet)
- [Documentation](#-documentation)

---

## ✨ Fonctionnalités

### Gestion des Patients
- ✅ Création, modification, suppression de patients
- ✅ Dossier patient avec infos administratives et médicales
- ✅ Historique complet (consultations, hospitalisations, urgences)
- ✅ Recherche et filtres avancés (nom, téléphone, centre, genre)
- ✅ Validation des numéros de téléphone congolais (+243XXXXXXXXX)
- ✅ Génération de documents médicaux (ordonnances, rapports)

### Gestion des Consultations
- ✅ Création et suivi des consultations
- ✅ Statuts : En attente, En cours, Terminée, Annulée
- ✅ Examen clinique, diagnostic, prescription
- ✅ Rendez-vous de suivi

### Gestion des Hospitalisations
- ✅ Admission avec service, chambre, lit
- ✅ Notes médicales et notes infirmières
- ✅ Interventions et compte-rendu de sortie
- ✅ Suivi de l'état d'hospitalisation (active/terminée)

### Gestion des Urgences
- ✅ Triage médical (4 niveaux : Léger, Moyen, Grave, Vital)
- ✅ Signes vitaux et premiers soins
- ✅ Orientation (Sortie, Hospitalisation, Transfert)

### Gestion des Rendez-vous
- ✅ Planification avec détection de chevauchement
- ✅ Statuts : Planifié, Confirmé, Terminé, Annulé
- ✅ Durée configurable (15-180 minutes)

### Dashboards par Rôle
- ✅ **ADMIN & MEDICAL_ADMIN** : Vue globale de l'hôpital
- ✅ **DOCTOR** : Ses patients, consultations, rendez-vous
- ✅ **SECRETARY** : Patients et activités de ses centres
- ✅ **NURSE** : Hospitalisations et urgences actives

---

## 🛠 Technologies

- **Backend** : Django 4.x
- **Base de données** : PostgreSQL (recommandé) ou SQLite
- **Frontend** : Bootstrap 5, HTMX
- **Cache** : Django Cache Framework
- **Validation** : Django Validators + Validations personnalisées

---

## 🚀 Installation

### Prérequis
```bash
Python 3.8+
pip (gestionnaire de paquets Python)
PostgreSQL (optionnel mais recommandé)
```

### 1. Cloner le Projet
```bash
git clone <url-du-repo>
cd hospitalManagement
```

### 2. Créer un Environnement Virtuel
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les Dépendances
```bash
pip install -r requirements/development.txt
```

### 4. Configuration de la Base de Données

#### Option A : PostgreSQL (Recommandé)
```bash
# Créer la base de données
createdb hospital_db

# Dans .env
DATABASE_URL=postgresql://user:password@localhost:5432/hospital_db
```

#### Option B : SQLite (Développement)
```python
# settings/development.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### 5. Appliquer les Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Créer un Superutilisateur
```bash
python manage.py createsuperuser
```

### 7. Lancer le Serveur
```bash
python manage.py runserver
```

Accéder à l'application : **http://localhost:8000**

---

## ⚙️ Configuration

### Variables d'Environnement

Créer un fichier `.env` à la racine :

```env
# Django
SECRET_KEY=votre-clé-secrète-très-longue-et-complexe
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de données
DATABASE_URL=postgresql://user:password@localhost:5432/hospital_db

# Cache (optionnel)
REDIS_URL=redis://localhost:6379/1
```

### Configuration des Rôles

Les utilisateurs sont gérés via **Django Admin** : `/admin/`

**Rôles disponibles** :
- `ADMIN` : Administrateur système complet
- `MEDICAL_ADMIN` : Médecin Administrateur (tous droits ADMIN + DOCTOR)
- `DOCTOR` : Médecin
- `NURSE` : Infirmier
- `SECRETARY` : Secrétaire

#### Créer un Profil Utilisateur
1. Aller dans `/admin/`
2. Créer un utilisateur (Users)
3. Créer un profil (Profiles) associé
4. Assigner un rôle et des centres

---

## 📖 Utilisation

### Connexion
1. Aller sur http://localhost:8000
2. Cliquer sur "Se connecter"
3. Utiliser vos identifiants

### Gestion des Patients

#### Créer un Patient
1. **Patients** > **Nouveau Patient**
2. Remplir les informations :
   - **Administratives** : Nom, prénom, date de naissance, téléphone (+243XXXXXXXXX)
   - **Médicales** : Antécédents, allergies, vaccinations (médecins uniquement)
3. Cliquer sur **Enregistrer**

#### Rechercher des Patients
- Utiliser la barre de recherche (nom, téléphone, ID)
- Appliquer des filtres (centre, genre, statut)
- Les filtres sont préservés lors de la pagination

#### Actions Rapides
- **Voir** : Dossier complet du patient
- **Éditer** : Modifier les informations
- **Supprimer** : Supprimer le patient (ADMIN uniquement)

### Créer une Consultation
1. Sur le dossier patient > **Nouvelle consultation**
2. Remplir : Motif, Examen clinique, Diagnostic, Prescription
3. Définir un rendez-vous de suivi si nécessaire

### Créer une Hospitalisation
1. Sur le dossier patient > **Nouvelle hospitalisation**
2. Définir : Service, Chambre, Lit, Motif d'admission
3. Ajouter des notes médicales/infirmières

### Gérer les Urgences
1. **Urgences** > **Nouvelle urgence**
2. Effectuer le triage (niveau d'urgence)
3. Noter les signes vitaux et premiers soins
4. Orienter le patient (sortie, hospitalisation, transfert)

---

## 🔐 Rôles et Permissions

### ADMIN
- ✅ Accès complet à toutes les fonctionnalités
- ✅ Gestion des utilisateurs (via Django Admin)
- ✅ Gestion des centres
- ✅ Suppression de données
- ✅ Vue dashboard globale

### MEDICAL_ADMIN (Médecin Administrateur)
- ✅ **Tous les droits ADMIN**
- ✅ **Tous les droits DOCTOR**
- ✅ Gestion des utilisateurs
- ✅ Gestion des centres
- ✅ Accès médical complet

### DOCTOR (Médecin)
- ✅ Voir tous les patients
- ✅ Créer/modifier consultations, hospitalisations, urgences
- ✅ Gérer ses rendez-vous
- ✅ Accès aux données médicales
- ✅ Dashboard personnel (ses patients uniquement)

### NURSE (Infirmier)
- ✅ Voir patients hospitalisés dans ses centres
- ✅ Ajouter notes infirmières
- ✅ Gérer les urgences (triage, soins)
- ✅ Accès limité aux données médicales

### SECRETARY (Secrétaire)
- ✅ Voir patients de ses centres
- ✅ Créer/modifier patients (infos administratives)
- ✅ Planifier consultations/hospitalisations
- ✅ Pas d'accès aux données médicales détaillées

---

## 📁 Structure du Projet

```
hospitalManagement/
├── hospital/                    # Application principale
│   ├── models.py               # Modèles de données
│   ├── forms.py                # Formulaires
│   ├── permissions.py          # Système de permissions
│   ├── urls.py                 # Routes URL
│   ├── views/                  # Vues modulaires
│   │   ├── base.py            # Vues de base et dashboards
│   │   ├── patients_views.py  # Gestion patients
│   │   ├── consultations_views.py
│   │   ├── hospitalisations_views.py
│   │   └── emergencies_views.py
│   ├── services/              # Logique métier
│   │   ├── patient_service.py
│   │   └── statistics_service.py
│   ├── templates/             # Templates HTML
│   └── static/                # Fichiers statiques
├── hospital_project/           # Configuration Django
│   └── settings/              # Settings par environnement
│       ├── base.py
│       ├── development.py
│       └── production.py
├── requirements/              # Dépendances
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── manage.py
├── README.md
└── CORRECTIONS_APPLIQUEES.md  # Journal des corrections
```

---

## 📚 Documentation

### Fichiers de Documentation
- **`README.md`** : Ce fichier (guide d'utilisation)
- **`CORRECTIONS_APPLIQUEES.md`** : Liste détaillée des corrections apportées
- **`Rapport.md`** : Analyse complète du système

### Validation des Téléphones (RDC)
Le système accepte les formats congolais :
- `+243XXXXXXXXX` (format international)
- `0XXXXXXXXX` (format local)

**Exemples valides** :
- `+243812345678`
- `0812345678`

### Migrations
```bash
# Créer les migrations après modification de modèles
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Voir l'état des migrations
python manage.py showmigrations
```

### Tests
```bash
# Lancer tous les tests
python manage.py test

# Tests spécifiques
python manage.py test hospital.tests.test_models
python manage.py test hospital.tests.test_permissions
```

---

## 🐛 Résolution de Problèmes

### Erreur : "No such table"
```bash
python manage.py migrate
```

### Erreur : "Permission Denied"
Vérifier que l'utilisateur a un profil avec un rôle assigné dans Django Admin.

### Les filtres ne fonctionnent pas
Vérifier que JavaScript est activé dans le navigateur.

### Téléphone invalide
Utiliser le format congolais : `+243XXXXXXXXX` ou `0XXXXXXXXX`

---

## 🤝 Contribution

### Pour Contribuer
1. Fork le projet
2. Créer une branche (`git checkout -b feature/amelioration`)
3. Commit les changements (`git commit -m 'Ajout fonctionnalité'`)
4. Push vers la branche (`git push origin feature/amelioration`)
5. Créer une Pull Request

### Standards de Code
- Suivre PEP 8 pour Python
- Imports organisés (standard, Django, local)
- Docstrings pour toutes les fonctions
- Commentaires en français

---

## 📞 Support

Pour obtenir de l'aide :
1. Consulter la documentation dans `CORRECTIONS_APPLIQUEES.md`
2. Vérifier les commentaires dans le code
3. Consulter le rapport d'analyse complet

---

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

---

## ✨ Remerciements

Développé pour répondre aux besoins spécifiques des établissements de santé en RDC.

**Version** : 2.0 - Corrections RDC  
**Date** : Octobre 2025  
**Statut** : ✅ Production Ready