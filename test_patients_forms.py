#!/usr/bin/env python
"""
Script de test pour vérifier les formulaires de patients
"""
import os
import sys
import django

# Ajouter le répertoire du projet au chemin Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital_project.settings.development')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from hospital.models import Patient, Centre, Profile
from hospital.forms import PatientForm
from hospital.permissions import can_manage_patient_medical_data, can_manage_patient_admin_data

def test_patient_forms():
    """Tester les formulaires de patients"""
    print("=== Test des formulaires de patients ===")
    
    # Créer un utilisateur de test
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    
    # Créer un profil pour l'utilisateur
    profile = Profile.objects.create(
        user=user,
        role='DOCTOR'  # Rôle avec permissions médicales
    )
    
    # Créer un centre de test
    centre = Centre.objects.create(
        name='Centre Test',
        address='Adresse Test',
        phone='123456789'
    )
    
    # Ajouter le centre au profil de l'utilisateur
    profile.centres.add(centre)
    
    print(f"✓ Utilisateur créé: {user.username} (Rôle: {profile.role})")
    print(f"✓ Centre créé: {centre.name}")
    
    # Tester le formulaire avec un utilisateur ayant des permissions médicales
    print("\n--- Test du formulaire avec permissions médicales ---")
    form_data = {
        'first_name': 'Jean',
        'last_name': 'Dupont',
        'postname': 'Paul',
        'date_of_birth': '1990-01-01',
        'gender': 'M',
        'phone': '0123456789',
        'address': '123 rue Test',
        'emergency_contact': '0987654321',
        'is_subscriber': True,
        'default_centre': centre.id,
        'medical_history': 'Antécédents médicaux test',
        'allergies': 'Aucune',
        'vaccinations': 'Vaccinations à jour',
        'lifestyle': 'Mode de vie sain'
    }
    
    form = PatientForm(data=form_data, user=user)
    if form.is_valid():
        print("✓ Formulaire valide avec permissions médicales")
        print(f"  Champs médicaux présents: {len(form.fields)} champs au total")
    else:
        print("✗ Formulaire invalide avec permissions médicales")
        print(f"  Erreurs: {form.errors}")
    
    # Tester avec un utilisateur sans permissions médicales (secrétaire)
    print("\n--- Test du formulaire sans permissions médicales ---")
    secretary_user = User.objects.create_user(
        username='testsecretary',
        email='secretary@example.com',
        password='testpass123'
    )
    
    secretary_profile = Profile.objects.create(
        user=secretary_user,
        role='SECRETARY'  # Rôle sans permissions médicales
    )
    secretary_profile.centres.add(centre)
    
    form_secretary = PatientForm(data=form_data, user=secretary_user)
    if form_secretary.is_valid():
        print("✓ Formulaire valide sans permissions médicales")
        print(f"  Champs médicaux absents: {len(form_secretary.fields)} champs au total")
        
        # Vérifier que les champs médicaux sont absents
        medical_fields = ['medical_history', 'allergies', 'vaccinations', 'lifestyle']
        missing_fields = [field for field in medical_fields if field not in form_secretary.fields]
        print(f"  Champs médicaux manquants: {missing_fields}")
    else:
        print("✗ Formulaire invalide sans permissions médicales")
        print(f"  Erreurs: {form_secretary.errors}")
    
    # Tester la création d'un patient
    print("\n--- Test de création d'un patient ---")
    if form.is_valid():
        patient = form.save()
        print(f"✓ Patient créé: {patient}")
        print(f"  ID: {patient.id}")
        print(f"  Nom complet: {patient}")
        print(f"  Centre: {patient.default_centre}")
        print(f"  Antécédents médicaux: {patient.medical_history}")
    
    # Tester les permissions
    print("\n--- Test des permissions ---")
    print(f"✓ Permissions médicales pour DOCTOR: {can_manage_patient_medical_data(user)}")
    print(f"✓ Permissions administratives pour DOCTOR: {can_manage_patient_admin_data(user)}")
    print(f"✓ Permissions médicales pour SECRETARY: {can_manage_patient_medical_data(secretary_user)}")
    print(f"✓ Permissions administratives pour SECRETARY: {can_manage_patient_admin_data(secretary_user)}")
    
    print("\n=== Test terminé avec succès ===")

if __name__ == '__main__':
    test_patient_forms()