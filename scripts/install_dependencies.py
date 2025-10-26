#!/usr/bin/env python3
"""
Script d'installation des dépendances pour le projet de gestion hospitalière
Ce script vérifie et installe toutes les dépendances requises
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Exécute une commande et gère les erreurs"""
    print(f"\n{'='*60}")
    print(f"Exécution: {description}")
    print(f"Commande: {command}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True
        )
        print(f"✅ Succès: {description}")
        if result.stdout:
            print(f"Sortie: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'exécution: {description}")
        print(f"Code de retour: {e.returncode}")
        print(f"Erreur: {e.stderr}")
        return False

def check_python_version():
    """Vérifie la version de Python"""
    print("Vérification de la version de Python...")
    version = sys.version_info
    print(f"Version actuelle: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 ou supérieur est requis")
        return False
    
    print("✅ Version de Python compatible")
    return True

def install_pip_dependencies():
    """Installe les dépendances pip"""
    base_dir = Path(__file__).parent.parent
    
    # Installation des dépendances de base
    base_requirements = base_dir / "requirements" / "base.txt"
    if base_requirements.exists():
        if not run_command(
            f"pip install -r {base_requirements}", 
            "Installation des dépendances de base"
        ):
            return False
    
    # Installation des dépendances de développement
    dev_requirements = base_dir / "requirements" / "development.txt"
    if dev_requirements.exists():
        if not run_command(
            f"pip install -r {dev_requirements}", 
            "Installation des dépendances de développement"
        ):
            return False
    
    # Installation des dépendances de production
    prod_requirements = base_dir / "requirements" / "production.txt"
    if prod_requirements.exists():
        if not run_command(
            f"pip install -r {prod_requirements}", 
            "Installation des dépendances de production"
        ):
            return False
    
    return True

def setup_environment():
    """Configure l'environnement"""
    base_dir = Path(__file__).parent.parent
    env_file = base_dir / ".env"
    env_example = base_dir / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        print("Création du fichier .env à partir de .env.example...")
        try:
            with open(env_example, 'r') as src, open(env_file, 'w') as dst:
                dst.write(src.read())
            print("✅ Fichier .env créé avec succès")
        except Exception as e:
            print(f"❌ Erreur lors de la création du fichier .env: {e}")
            return False
    
    return True

def run_migrations():
    """Exécute les migrations Django"""
    base_dir = Path(__file__).parent.parent
    
    return run_command(
        f"cd {base_dir} && python manage.py migrate", 
        "Exécution des migrations Django"
    )

def create_superuser():
    """Propose de créer un superutilisateur"""
    base_dir = Path(__file__).parent.parent
    
    response = input("\nVoulez-vous créer un superutilisateur ? (y/n): ")
    if response.lower() in ['y', 'yes', 'o', 'oui']:
        return run_command(
            f"cd {base_dir} && python manage.py createsuperuser", 
            "Création d'un superutilisateur"
        )
    return True

def collect_static():
    """Collecte les fichiers statiques"""
    base_dir = Path(__file__).parent.parent
    
    return run_command(
        f"cd {base_dir} && python manage.py collectstatic --noinput", 
        "Collecte des fichiers statiques"
    )

def main():
    """Fonction principale"""
    print("🏥 Script d'installation pour le système de gestion hospitalière")
    print("=" * 60)
    
    # Vérification de la version de Python
    if not check_python_version():
        sys.exit(1)
    
    # Installation des dépendances
    if not install_pip_dependencies():
        print("❌ Échec de l'installation des dépendances")
        sys.exit(1)
    
    # Configuration de l'environnement
    if not setup_environment():
        print("❌ Échec de la configuration de l'environnement")
        sys.exit(1)
    
    # Exécution des migrations
    if not run_migrations():
        print("❌ Échec des migrations")
        sys.exit(1)
    
    # Collecte des fichiers statiques
    if not collect_static():
        print("❌ Échec de la collecte des fichiers statiques")
        sys.exit(1)
    
    # Création d'un superutilisateur
    if not create_superuser():
        print("❌ Échec de la création du superutilisateur")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 Installation terminée avec succès !")
    print("=" * 60)
    print("\nProchaines étapes:")
    print("1. Configurez votre fichier .env avec les bonnes valeurs")
    print("2. Lancez le serveur de développement: python manage.py runserver")
    print("3. Accédez à l'application: http://localhost:8000")
    print("4. Consultez la documentation pour plus d'informations")

if __name__ == "__main__":
    main()