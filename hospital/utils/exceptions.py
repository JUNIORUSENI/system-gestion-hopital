"""
Exceptions personnalisées pour l'application hospital
"""
from django.core.exceptions import PermissionDenied


class HospitalException(Exception):
    """Exception de base pour l'application hospital"""
    pass


class PatientNotFound(HospitalException):
    """Exception levée lorsqu'un patient n'est pas trouvé"""
    pass


class ConsultationNotFound(HospitalException):
    """Exception levée lorsqu'une consultation n'est pas trouvée"""
    pass


class HospitalisationNotFound(HospitalException):
    """Exception levée lorsqu'une hospitalisation n'est pas trouvée"""
    pass


class EmergencyNotFound(HospitalException):
    """Exception levée lorsqu'une urgence n'est pas trouvée"""
    pass


class AppointmentNotFound(HospitalException):
    """Exception levée lorsqu'un rendez-vous n'est pas trouvé"""
    pass


class CentreNotFound(HospitalException):
    """Exception levée lorsqu'un centre n'est pas trouvé"""
    pass


class UserNotFound(HospitalException):
    """Exception levée lorsqu'un utilisateur n'est pas trouvé"""
    pass


class InvalidStatusTransition(HospitalException):
    """Exception levée lorsqu'une transition de statut est invalide"""
    pass


class InsufficientPermissions(HospitalException, PermissionDenied):
    """Exception levée lorsque les permissions sont insuffisantes"""
    pass


class ValidationError(HospitalException):
    """Exception levée lors d'une erreur de validation"""
    pass


class ResourceConflict(HospitalException):
    """Exception levée lors d'un conflit de ressources"""
    pass


class ServiceUnavailable(HospitalException):
    """Exception levée lorsqu'un service n'est pas disponible"""
    pass


class BusinessRuleViolation(HospitalException):
    """Exception levée lorsqu'une règle métier est violée"""
    pass