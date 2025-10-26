"""
Gestionnaires d'erreurs personnalisés pour l'application hospital
"""
import logging
import traceback
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.utils.deprecation import MiddlewareMixin

from .exceptions import HospitalException

logger = logging.getLogger(__name__)


class HospitalErrorMiddleware(MiddlewareMixin):
    """Middleware pour gérer les erreurs de l'application hospital"""
    
    def process_exception(self, request, exception):
        """Traite les exceptions non gérées"""
        # Ne pas gérer les exceptions de débogage si DEBUG=True
        if settings.DEBUG:
            return None
        
        # Journaliser l'exception
        logger.error(
            f"Exception non gérée: {exception}",
            exc_info=True,
            extra={
                'request': request,
                'user': getattr(request, 'user', None),
                'path': request.path,
                'method': request.method,
            }
        )
        
        # Gérer les exceptions personnalisées
        if isinstance(exception, HospitalException):
            return self.handle_hospital_exception(request, exception)
        
        # Gérer les exceptions Django courantes
        if isinstance(exception, PermissionDenied):
            return self.handle_permission_denied(request, exception)
        
        # Gérer les autres exceptions
        return self.handle_generic_exception(request, exception)
    
    def handle_hospital_exception(self, request, exception):
        """Gère les exceptions personnalisées de l'application hospital"""
        from .exceptions import (
            PatientNotFound, ConsultationNotFound, HospitalisationNotFound,
            EmergencyNotFound, AppointmentNotFound, CentreNotFound, UserNotFound,
            InvalidStatusTransition, InsufficientPermissions, ValidationError,
            ResourceConflict, ServiceUnavailable, BusinessRuleViolation
        )
        
        # Déterminer le statut HTTP et le message
        status_code = 500
        error_message = "Une erreur est survenue"
        
        if isinstance(exception, (PatientNotFound, ConsultationNotFound, HospitalisationNotFound,
                                EmergencyNotFound, AppointmentNotFound, CentreNotFound, UserNotFound)):
            status_code = 404
            error_message = str(exception) or "Ressource non trouvée"
        
        elif isinstance(exception, InsufficientPermissions):
            status_code = 403
            error_message = str(exception) or "Permissions insuffisantes"
        
        elif isinstance(exception, (InvalidStatusTransition, ValidationError, BusinessRuleViolation)):
            status_code = 400
            error_message = str(exception) or "Requête invalide"
        
        elif isinstance(exception, ResourceConflict):
            status_code = 409
            error_message = str(exception) or "Conflit de ressources"
        
        elif isinstance(exception, ServiceUnavailable):
            status_code = 503
            error_message = str(exception) or "Service indisponible"
        
        # Retourner une réponse JSON pour les requêtes API
        if request.headers.get('Accept') == 'application/json' or request.path.startswith('/api/'):
            return JsonResponse({
                'error': True,
                'message': error_message,
                'status_code': status_code,
                'type': exception.__class__.__name__,
            }, status=status_code)
        
        # Retourner une page d'erreur pour les requêtes web
        return render(request, 'hospital/errors/error.html', {
            'error_message': error_message,
            'status_code': status_code,
            'exception': exception,
        }, status=status_code)
    
    def handle_permission_denied(self, request, exception):
        """Gère les erreurs de permission"""
        # Si l'utilisateur n'est pas authentifié, rediriger vers la page de connexion
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        
        # Sinon, afficher une page d'erreur 403
        if request.headers.get('Accept') == 'application/json' or request.path.startswith('/api/'):
            return JsonResponse({
                'error': True,
                'message': "Vous n'avez pas la permission d'effectuer cette action",
                'status_code': 403,
                'type': 'PermissionDenied',
            }, status=403)
        
        return render(request, 'hospital/errors/403.html', {
            'error_message': "Vous n'avez pas la permission d'effectuer cette action",
            'status_code': 403,
        }, status=403)
    
    def handle_generic_exception(self, request, exception):
        """Gère les exceptions génériques"""
        # Retourner une réponse JSON pour les requêtes API
        if request.headers.get('Accept') == 'application/json' or request.path.startswith('/api/'):
            return JsonResponse({
                'error': True,
                'message': "Une erreur interne est survenue",
                'status_code': 500,
                'type': 'InternalServerError',
            }, status=500)
        
        # Retourner une page d'erreur pour les requêtes web
        return render(request, 'hospital/errors/500.html', {
            'error_message': "Une erreur interne est survenue",
            'status_code': 500,
        }, status=500)


def custom_404_handler(request, exception):
    """Gestionnaire personnalisé pour les erreurs 404"""
    logger.warning(
        f"404 Not Found: {request.path}",
        extra={
            'request': request,
            'user': getattr(request, 'user', None),
        }
    )
    
    # Retourner une réponse JSON pour les requêtes API
    if request.headers.get('Accept') == 'application/json' or request.path.startswith('/api/'):
        return JsonResponse({
            'error': True,
            'message': "La page demandée n'a pas été trouvée",
            'status_code': 404,
            'type': 'NotFound',
        }, status=404)
    
    # Retourner une page d'erreur pour les requêtes web
    return render(request, 'hospital/errors/404.html', {
        'error_message': "La page demandée n'a pas été trouvée",
        'status_code': 404,
    }, status=404)


def custom_500_handler(request):
    """Gestionnaire personnalisé pour les erreurs 500"""
    logger.error(
        "500 Internal Server Error",
        extra={
            'request': request,
            'user': getattr(request, 'user', None),
        }
    )
    
    # Retourner une réponse JSON pour les requêtes API
    if request.headers.get('Accept') == 'application/json' or request.path.startswith('/api/'):
        return JsonResponse({
            'error': True,
            'message': "Une erreur interne est survenue",
            'status_code': 500,
            'type': 'InternalServerError',
        }, status=500)
    
    # Retourner une page d'erreur pour les requêtes web
    return render(request, 'hospital/errors/500.html', {
        'error_message': "Une erreur interne est survenue",
        'status_code': 500,
    }, status=500)


def log_error(exception, request=None, context=None):
    """
    Fonction utilitaire pour journaliser les erreurs
    """
    error_data = {
        'exception': exception,
        'exception_type': exception.__class__.__name__,
        'exception_message': str(exception),
        'traceback': traceback.format_exc(),
    }
    
    if request:
        error_data.update({
            'request_method': request.method,
            'request_path': request.path,
            'request_user': getattr(request, 'user', None),
            'request_GET': dict(request.GET),
            'request_POST': dict(request.POST),
        })
    
    if context:
        error_data['context'] = context
    
    # Journaliser l'erreur
    logger.error(
        f"Error logged: {exception}",
        extra=error_data,
        exc_info=True
    )


def handle_error_response(request, exception, status_code=500):
    """
    Fonction utilitaire pour générer une réponse d'erreur cohérente
    """
    # Journaliser l'erreur
    log_error(exception, request)
    
    # Retourner une réponse JSON pour les requêtes API
    if request.headers.get('Accept') == 'application/json' or request.path.startswith('/api/'):
        return JsonResponse({
            'error': True,
            'message': str(exception) or "Une erreur est survenue",
            'status_code': status_code,
            'type': exception.__class__.__name__,
        }, status=status_code)
    
    # Retourner une page d'erreur pour les requêtes web
    return render(request, 'hospital/errors/error.html', {
        'error_message': str(exception) or "Une erreur est survenue",
        'status_code': status_code,
        'exception': exception,
    }, status=status_code)