"""
Système de permissions centralisé pour le projet hospital
"""
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import AnonymousUser

from .models import Patient, Consultation, Hospitalisation, Emergency


class BasePermission:
    """Classe de base pour les permissions"""
    
    def has_permission(self, request, view, obj=None):
        """Vérifie si l'utilisateur a la permission d'accéder à la vue"""
        raise NotImplementedError
    
    def has_object_permission(self, request, view, obj):
        """Vérifie si l'utilisateur a la permission sur un objet spécifique"""
        raise NotImplementedError


class IsAuthenticated(BasePermission):
    """Permission pour les utilisateurs authentifiés"""
    
    def has_permission(self, request, view, obj=None):
        return request.user.is_authenticated


class IsAdmin(BasePermission):
    """Permission pour les administrateurs (ADMIN uniquement)"""
    
    def has_permission(self, request, view, obj=None):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.role == 'ADMIN'
        )


class IsMedicalAdmin(BasePermission):
    """Permission pour les médecins administrateurs (a TOUS les droits)"""
    
    def has_permission(self, request, view, obj=None):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.role == 'MEDICAL_ADMIN'
        )


class IsAdminOrMedicalAdmin(BasePermission):
    """Permission pour les administrateurs (ADMIN ou MEDICAL_ADMIN)"""
    
    def has_permission(self, request, view, obj=None):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'profile') and
            request.user.profile.role in ['ADMIN', 'MEDICAL_ADMIN']
        )


class IsDoctor(BasePermission):
    """Permission pour les médecins"""
    
    def has_permission(self, request, view, obj=None):
        return (
            request.user.is_authenticated and 
            hasattr(request.user, 'profile') and 
            request.user.profile.role == 'DOCTOR'
        )


class IsNurse(BasePermission):
    """Permission pour les infirmiers"""
    
    def has_permission(self, request, view, obj=None):
        return (
            request.user.is_authenticated and 
            hasattr(request.user, 'profile') and 
            request.user.profile.role == 'NURSE'
        )


class IsSecretary(BasePermission):
    """Permission pour les secrétaires"""
    
    def has_permission(self, request, view, obj=None):
        return (
            request.user.is_authenticated and 
            hasattr(request.user, 'profile') and 
            request.user.profile.role == 'SECRETARY'
        )


class CanAccessPatient(BasePermission):
    """Permission pour accéder à un patient"""
    
    def has_permission(self, request, view, obj=None):
        if not request.user.is_authenticated:
            return False
        
        # Pour les listes, on vérifie le rôle général
        if hasattr(request.user, 'profile'):
            return request.user.profile.role in ['ADMIN', 'MEDICAL_ADMIN', 'DOCTOR', 'SECRETARY', 'NURSE']
        return False
    
    def has_object_permission(self, request, view, obj):
        """Vérifie l'accès à un patient spécifique"""
        if not isinstance(obj, Patient):
            return False
        
        if not request.user.is_authenticated or not hasattr(request.user, 'profile'):
            return False
        
        user_role = request.user.profile.role
        
        # Admin et Medical Admin ont accès à tous les patients
        if user_role in ['ADMIN', 'MEDICAL_ADMIN']:
            return True
        
        # Les médecins ont accès à tous les patients
        if user_role == 'DOCTOR':
            return True
        
        # Les secrétaires ont accès aux patients de leurs centres
        if user_role == 'SECRETARY':
            return obj.default_centre in request.user.profile.centres.all()
        
        # Les infirmiers ont accès aux patients hospitalisés dans leurs centres
        if user_role == 'NURSE':
            return Hospitalisation.objects.filter(
                patient=obj, 
                centre__in=request.user.profile.centres.all()
            ).exists()
        
        return False


class CanAccessMedicalData(BasePermission):
    """Permission pour accéder aux données médicales"""
    
    def has_permission(self, request, view, obj=None):
        if not request.user.is_authenticated or not hasattr(request.user, 'profile'):
            return False
        
        user_role = request.user.profile.role
        return user_role in ['ADMIN', 'MEDICAL_ADMIN', 'DOCTOR', 'NURSE']
    
    def has_object_permission(self, request, view, obj):
        """Vérifie l'accès aux données médicales d'un patient"""
        if isinstance(obj, Patient):
            patient = obj
        elif hasattr(obj, 'patient'):
            patient = obj.patient
        else:
            return False
        
        if not request.user.is_authenticated or not hasattr(request.user, 'profile'):
            return False
        
        user_role = request.user.profile.role
        
        # Admin et Medical Admin ont accès à toutes les données médicales
        if user_role in ['ADMIN', 'MEDICAL_ADMIN']:
            return True
        
        # Les médecins ont accès à toutes les données médicales
        if user_role == 'DOCTOR':
            return True
        
        # Les infirmiers ont accès limité aux données médicales pour les soins
        if user_role == 'NURSE':
            return True
        
        return False


class CanManagePatientAdminData(BasePermission):
    """Permission pour gérer les données administratives des patients"""
    
    def has_permission(self, request, view, obj=None):
        if not request.user.is_authenticated or not hasattr(request.user, 'profile'):
            return False
        
        user_role = request.user.profile.role
        return user_role in ['ADMIN', 'MEDICAL_ADMIN', 'DOCTOR', 'SECRETARY']


class CanManagePatientMedicalData(BasePermission):
    """Permission pour gérer les données médicales des patients"""
    
    def has_permission(self, request, view, obj=None):
        if not request.user.is_authenticated or not hasattr(request.user, 'profile'):
            return False
        
        user_role = request.user.profile.role
        return user_role in ['ADMIN', 'MEDICAL_ADMIN', 'DOCTOR']


class CanManageUsers(BasePermission):
    """Permission pour gérer les utilisateurs (gestion via Django Admin uniquement)"""
    
    def has_permission(self, request, view, obj=None):
        if not request.user.is_authenticated or not hasattr(request.user, 'profile'):
            return False
        
        # Seuls ADMIN et MEDICAL_ADMIN peuvent gérer les utilisateurs
        return request.user.profile.role in ['ADMIN', 'MEDICAL_ADMIN']


class CanManageCentres(BasePermission):
    """Permission pour gérer les centres"""
    
    def has_permission(self, request, view, obj=None):
        if not request.user.is_authenticated or not hasattr(request.user, 'profile'):
            return False
        
        # Seuls ADMIN et MEDICAL_ADMIN peuvent gérer les centres
        return request.user.profile.role in ['ADMIN', 'MEDICAL_ADMIN']


class CanAccessStatistics(BasePermission):
    """Permission pour accéder aux statistiques"""
    
    def has_permission(self, request, view, obj=None):
        if not request.user.is_authenticated or not hasattr(request.user, 'profile'):
            return False
        
        user_role = request.user.profile.role
        return user_role in ['ADMIN', 'MEDICAL_ADMIN', 'DOCTOR']


class CanManageAppointments(BasePermission):
    """Permission pour gérer les rendez-vous"""
    
    def has_permission(self, request, view, obj=None):
        if not request.user.is_authenticated or not hasattr(request.user, 'profile'):
            return False
        
        user_role = request.user.profile.role
        # MEDICAL_ADMIN a aussi les droits de médecin donc peut gérer les rendez-vous
        return user_role in ['ADMIN', 'MEDICAL_ADMIN', 'DOCTOR']


# Classe request factice pour les fonctions utilitaires
class DummyRequest:
    def __init__(self, user):
        self.user = user

# Fonctions utilitaires pour les permissions
def check_patient_access(user, patient):
    """
    Fonction utilitaire pour vérifier si un utilisateur a accès à un patient
    Conserve la compatibilité avec le code existant
    """
    permission = CanAccessPatient()
    dummy_request = DummyRequest(user)
    return permission.has_object_permission(dummy_request, None, patient)


def can_access_medical_data(user, patient=None):
    """
    Fonction utilitaire pour vérifier si un utilisateur peut accéder aux données médicales
    """
    permission = CanAccessMedicalData()
    dummy_request = DummyRequest(user)
    if patient:
        return permission.has_object_permission(dummy_request, None, patient)
    return permission.has_permission(dummy_request, None)


def can_manage_patient_admin_data(user):
    """
    Fonction utilitaire pour vérifier si un utilisateur peut gérer les données administratives
    """
    permission = CanManagePatientAdminData()
    dummy_request = DummyRequest(user)
    return permission.has_permission(dummy_request, None)


def can_manage_patient_medical_data(user):
    """
    Fonction utilitaire pour vérifier si un utilisateur peut gérer les données médicales
    """
    permission = CanManagePatientMedicalData()
    dummy_request = DummyRequest(user)
    return permission.has_permission(dummy_request, None)


# Décorateur de permission réutilisable
def permission_required(permission_classes):
    """
    Décorateur pour vérifier les permissions avant l'exécution d'une vue
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            for permission_class in permission_classes:
                permission = permission_class()
                if not permission.has_permission(request, view_func):
                    raise PermissionDenied("Vous n'avez pas la permission d'accéder à cette ressource")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def object_permission_required(permission_classes):
    """
    Décorateur pour vérifier les permissions sur un objet avant l'exécution d'une vue
    Nécessite que la vue ait un paramètre object_id ou similaire
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            # Récupérer l'objet selon le type de vue
            obj = None
            if 'patient_id' in kwargs:
                from .models import Patient
                try:
                    obj = Patient.objects.get(id=kwargs['patient_id'])
                except Patient.DoesNotExist:
                    raise PermissionDenied("Patient non trouvé")
            elif 'consultation_id' in kwargs:
                from .models import Consultation
                try:
                    obj = Consultation.objects.get(id=kwargs['consultation_id'])
                except Consultation.DoesNotExist:
                    raise PermissionDenied("Consultation non trouvée")
            elif 'hospitalisation_id' in kwargs:
                from .models import Hospitalisation
                try:
                    obj = Hospitalisation.objects.get(id=kwargs['hospitalisation_id'])
                except Hospitalisation.DoesNotExist:
                    raise PermissionDenied("Hospitalisation non trouvée")
            elif 'emergency_id' in kwargs:
                from .models import Emergency
                try:
                    obj = Emergency.objects.get(id=kwargs['emergency_id'])
                except Emergency.DoesNotExist:
                    raise PermissionDenied("Urgence non trouvée")
            
            if obj:
                for permission_class in permission_classes:
                    permission = permission_class()
                    if not permission.has_object_permission(request, view_func, obj):
                        raise PermissionDenied("Vous n'avez pas la permission d'accéder à cette ressource")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator