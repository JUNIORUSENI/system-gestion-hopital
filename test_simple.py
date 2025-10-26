#!/usr/bin/env python
"""
Script de test simple pour vérifier les formulaires de patients
"""
import os
import sys
import django

# Ajouter le répertoire du projet au chemin Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital_project.settings.development')
django.setup()

from hospital.forms import PatientForm
from hospital.models import Centre
from django.contrib.auth.models import User
from hospital.models import Profile

def test_form():
    """Test simple du formulaire"""
    print("=== Test simple du formulaire Patient ===")
    
    # Créer un utilisateur de test
    user = User.objects.filter(username='joseph').first()
    if not user:
        print("✗ Utilisateur joseph non trouvé")
        return
    
    # Récupérer un centre
    centre = Centre.objects.first()
    if not centre:
        print("✗ Aucun centre trouvé")
        return
    
    print(f"✓ Utilisateur: {user.username}")
    print(f"✓ Centre: {centre.name}")
    
    # Tester le formulaire avec des données correctes
    form_data = {
        'first_name': 'Test',
        'last_name': 'Patient',
        'date_of_birth': '1990-01-01',
        'gender': 'M',
        'phone': '0123456789',
        'address': '123 rue Test',
        'emergency_contact': '0987654321',
        'is_subscriber': False,
        'default_centre': centre.id,  # ID du centre, pas l'objet
    }
    
    form = PatientForm(data=form_data, user=user)
    if form.is_valid():
        print("✓ Formulaire valide")
        print(f"  Champs: {list(form.fields.keys())}")
        
        # Vérifier la valeur du centre
        centre_value = form.cleaned_data.get('default_centre')
        print(f"  Valeur du centre dans cleaned_data: {centre_value} (type: {type(centre_value)})")
        
        # Créer le patient
        try:
            patient = form.save()
            print(f"✓ Patient créé: {patient}")
        except Exception as e:
            print(f"✗ Erreur lors de la création: {e}")
    else:
        print("✗ Formulaire invalide")
        print(f"  Erreurs: {form.errors}")

if __name__ == '__main__':
    test_form()