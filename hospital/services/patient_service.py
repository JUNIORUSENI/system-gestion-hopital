"""
Service pour la gestion des patients
"""
from django.db import transaction
from django.core.cache import cache
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError

from ..models import Patient, Centre
from ..permissions import check_patient_access, can_manage_patient_admin_data, can_manage_patient_medical_data


class PatientService:
    """Service pour la gestion des patients"""
    
    def __init__(self):
        self.cache_timeout = 300  # 5 minutes
    
    def get_patients_for_user(self, user, page=1, per_page=25, use_cache=True):
        """
        Récupérer les patients accessibles pour un utilisateur avec pagination
        """
        cache_key = f'patients_{user.id}_{user.profile.role}_{page}_{per_page}'
        
        if use_cache:
            cached_patients = cache.get(cache_key)
            if cached_patients:
                return cached_patients
        
        # Récupérer les patients selon les permissions de l'utilisateur
        if user.profile.role in ['ADMIN', 'MEDICAL_ADMIN']:
            patients = Patient.objects.all()
        elif user.profile.role == 'DOCTOR':
            patients = Patient.objects.all()
        elif user.profile.role == 'SECRETARY':
            patients = Patient.objects.filter(
                default_centre__in=user.profile.centres.all()
            )
        elif user.profile.role == 'NURSE':
            # Les infirmiers voient les patients hospitalisés dans leurs centres
            from ..models import Hospitalisation
            patient_ids = Hospitalisation.objects.filter(
                centre__in=user.profile.centres.all()
            ).values_list('patient_id', flat=True).distinct()
            patients = Patient.objects.filter(id__in=patient_ids)
        else:
            patients = Patient.objects.none()
        
        # Optimisation avec select_related
        patients = patients.select_related('default_centre').order_by('last_name', 'first_name')
        
        # Pagination
        paginator = Paginator(patients, per_page)
        page_obj = paginator.get_page(page)
        
        result = {
            'patients': page_obj,
            'page_obj': page_obj,
            'total_count': paginator.count,
            'total_pages': paginator.num_pages,
        }
        
        if use_cache:
            cache.set(cache_key, result, self.cache_timeout)
        
        return result
    
    def get_patient_detail(self, user, patient_id):
        """
        Récupérer les détails d'un patient avec vérification des permissions
        """
        patient = get_object_or_404(Patient, id=patient_id)
        
        # Vérifier les permissions
        if not check_patient_access(user, patient):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Vous n'avez pas accès à ce patient")
        
        # Récupérer l'historique médical du patient avec optimisation
        from ..models import Consultation, Hospitalisation, Emergency
        
        consultations = patient.consultations.select_related('doctor', 'centre').order_by('-date')
        hospitalisations = patient.hospitalisations.select_related('doctor', 'centre').order_by('-admission_date')
        emergencies = patient.emergencies.select_related('doctor', 'centre').order_by('-admission_time')
        
        # Déterminer si l'utilisateur peut voir les données médicales
        from ..permissions import can_access_medical_data
        can_view_medical_data = can_access_medical_data(user, patient)
        
        return {
            'patient': patient,
            'consultations': consultations,
            'hospitalisations': hospitalisations,
            'emergencies': emergencies,
            'can_view_medical_data': can_view_medical_data
        }
    
    @transaction.atomic
    def create_patient(self, user, patient_data):
        """
        Créer un patient avec validation des permissions et des données
        """
        # Vérifier les permissions - les secrétaires peuvent créer des patients
        if not (can_manage_patient_admin_data(user) or user.profile.role == 'SECRETARY'):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Vous n'êtes pas autorisé à créer des patients")
        
        # Valider et filtrer les données selon le rôle de l'utilisateur
        validated_data = self._validate_patient_data(user, patient_data)
        
        # Créer le patient
        patient = Patient.objects.create(**validated_data)
        
        # Invalider le cache
        self._invalidate_patients_cache(user)
        
        return patient
    
    @transaction.atomic
    def update_patient(self, user, patient, patient_data):
        """
        Mettre à jour un patient avec validation des permissions et des données
        """
        # Vérifier les permissions d'accès
        if not check_patient_access(user, patient):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Vous n'avez pas accès à ce patient")
        
        # Vérifier les permissions de modification
        can_manage_admin = can_manage_patient_admin_data(user)
        can_manage_medical = can_manage_patient_medical_data(user)
        
        if not (can_manage_admin or can_manage_medical):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Vous n'êtes pas autorisé à modifier les informations de ce patient")
        
        # Valider et filtrer les données selon le rôle de l'utilisateur
        validated_data = self._validate_patient_data(user, patient_data, is_update=True)
        
        # Mettre à jour le patient
        for field, value in validated_data.items():
            setattr(patient, field, value)
        patient.save()
        
        # Invalider le cache
        self._invalidate_patients_cache(user)
        
        return patient
    
    @transaction.atomic
    def delete_patient(self, user, patient):
        """
        Supprimer un patient avec validation des permissions
        """
        # Vérifier les permissions d'accès
        if not check_patient_access(user, patient):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Vous n'avez pas accès à ce patient")
        
        # Seuls les administrateurs peuvent supprimer des patients
        if user.profile.role != 'ADMIN':
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Seuls les administrateurs peuvent supprimer des patients")
        
        patient.delete()
        
        # Invalider le cache
        self._invalidate_patients_cache(user)
    
    def search_patients(self, user, query, page=1, per_page=25):
        """
        Rechercher des patients selon une requête
        """
        if not query:
            return self.get_patients_for_user(user, page, per_page)
        
        # Récupérer les patients selon les permissions de l'utilisateur
        if user.profile.role in ['ADMIN', 'MEDICAL_ADMIN']:
            patients = Patient.objects.all()
        elif user.profile.role == 'DOCTOR':
            patients = Patient.objects.all()
        elif user.profile.role == 'SECRETARY':
            patients = Patient.objects.filter(
                default_centre__in=user.profile.centres.all()
            )
        elif user.profile.role == 'NURSE':
            # Les infirmiers voient les patients hospitalisés dans leurs centres
            from ..models import Hospitalisation
            patient_ids = Hospitalisation.objects.filter(
                centre__in=user.profile.centres.all()
            ).values_list('patient_id', flat=True).distinct()
            patients = Patient.objects.filter(id__in=patient_ids)
        else:
            patients = Patient.objects.none()
        
        # Filtrer par la requête de recherche
        patients = patients.filter(
            first_name__icontains=query
        ) | patients.filter(
            last_name__icontains=query
        ) | patients.filter(
            postname__icontains=query
        ) | patients.filter(
            phone__icontains=query
        )
        
        # Optimisation avec select_related
        patients = patients.select_related('default_centre').order_by('last_name', 'first_name')
        
        # Pagination
        paginator = Paginator(patients, per_page)
        page_obj = paginator.get_page(page)
        
        return {
            'patients': page_obj,
            'page_obj': page_obj,
            'total_count': paginator.count,
            'total_pages': paginator.num_pages,
            'query': query,
        }
    
    def _validate_patient_data(self, user, patient_data, is_update=False):
        """
        Valider et filtrer les données du patient selon le rôle de l'utilisateur
        """
        validated_data = patient_data.copy()
        
        # Si l'utilisateur ne peut pas gérer les données médicales, supprimer ces champs
        if not can_manage_patient_medical_data(user):
            medical_fields = ['medical_history', 'allergies', 'vaccinations', 'lifestyle']
            for field in medical_fields:
                if field in validated_data:
                    validated_data.pop(field, None)
        
        # Validation du centre
        if 'default_centre' in validated_data and validated_data['default_centre']:
            try:
                # Si c'est déjà un objet Centre, l'utiliser directement
                if isinstance(validated_data['default_centre'], Centre):
                    centre = validated_data['default_centre']
                else:
                    # Sinon, le récupérer par ID
                    centre = Centre.objects.get(id=validated_data['default_centre'])
                
                # Vérifier si l'utilisateur a accès à ce centre
                if user.profile.role in ['SECRETARY', 'NURSE']:
                    if centre not in user.profile.centres.all():
                        validated_data.pop('default_centre', None)
            except (Centre.DoesNotExist, ValueError):
                validated_data.pop('default_centre', None)
        
        return validated_data
    
    def _invalidate_patients_cache(self, user):
        """
        Invalider le cache des patients pour un utilisateur
        Supprime toutes les pages pour cet utilisateur
        """
        # Supprimer plusieurs pages potentielles (jusqu'à 10 pages)
        for page_num in range(1, 11):
            for per_page in [10, 25, 50, 100]:
                cache_key = f'patients_{user.id}_{user.profile.role}_{page_num}_{per_page}'
                cache.delete(cache_key)
        
        # Alternative: désactiver le cache pour éviter les incohérences
        # ou utiliser un système de tags de cache plus avancé