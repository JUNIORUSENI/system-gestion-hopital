"""
Validateurs personnalisés pour les formulaires de l'application hospital
"""
import re
from datetime import date, datetime, timedelta
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils import timezone


def validate_phone_number(value):
    """
    Valide un numéro de téléphone international
    Accepte les formats: +33612345678, 0612345678, (0)6 12 34 56 78
    """
    if not value:
        return
    
    # Supprimer tous les caractères non numériques sauf le +
    cleaned = re.sub(r'[^\d+]', '', value)
    
    # Vérifier que le numéro commence par un indicatif pays ou un 0
    if not (cleaned.startswith('+') or cleaned.startswith('0')):
        raise ValidationError(
            'Le numéro de téléphone doit commencer par un indicatif pays (+) ou par 0'
        )
    
    # Vérifier la longueur minimale
    if len(cleaned) < 10:
        raise ValidationError(
            'Le numéro de téléphone doit contenir au moins 10 chiffres'
        )
    
    # Vérifier que le numéro ne contient que des chiffres et éventuellement un +
    if not re.match(r'^\+?\d+$', cleaned):
        raise ValidationError(
            'Le numéro de téléphone ne peut contenir que des chiffres et éventuellement un + au début'
        )


def validate_email(value):
    """
    Validation améliorée pour les adresses email
    """
    if not value:
        return
    
    # Validation de base avec Django
    email_regex = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    if not email_regex.match(value):
        raise ValidationError(
            'Veuillez entrer une adresse email valide'
        )
    
    # Vérifications supplémentaires
    if value.count('@') != 1:
        raise ValidationError(
            'L\'adresse email doit contenir exactement un symbole @'
        )
    
    local_part, domain_part = value.split('@')
    
    if len(local_part) > 64:
        raise ValidationError(
            'La partie locale de l\'adresse email est trop longue (maximum 64 caractères)'
        )
    
    if len(domain_part) > 253:
        raise ValidationError(
            'La partie domaine de l\'adresse email est trop longue (maximum 253 caractères)'
        )


def validate_date_of_birth(value):
    """
    Valide une date de naissance
    """
    if not value:
        return
    
    today = date.today()
    
    # Vérifier que la date n'est pas dans le futur
    if value > today:
        raise ValidationError(
            'La date de naissance ne peut pas être dans le futur'
        )
    
    # Vérifier que la personne n'est pas trop âgée (130 ans)
    max_age = 130
    if value < today.replace(year=today.year - max_age):
        raise ValidationError(
            f'La date de naissance est trop ancienne (maximum {max_age} ans)'
        )


def validate_future_date(value):
    """
    Valide qu'une date est dans le futur
    """
    if not value:
        return
    
    today = date.today()
    
    if value <= today:
        raise ValidationError(
            'Cette date doit être dans le futur'
        )


def validate_future_datetime(value):
    """
    Valide qu'une date/heure est dans le futur
    """
    if not value:
        return
    
    now = timezone.now()
    
    if value <= now:
        raise ValidationError(
            'Cette date et heure doivent être dans le futur'
        )


def validate_appointment_datetime(value):
    """
    Valide une date/heure de rendez-vous
    """
    if not value:
        return
    
    now = timezone.now()
    
    # Vérifier que la date est dans le futur
    if value <= now:
        raise ValidationError(
            'La date du rendez-vous doit être dans le futur'
        )
    
    # Vérifier que le rendez-vous n'est pas trop loin dans le futur (1 an)
    max_future = now + timedelta(days=365)
    if value > max_future:
        raise ValidationError(
            'La date du rendez-vous ne peut pas dépasser un an dans le futur'
        )
    
    # Vérifier que le rendez-vous est pendant les heures d'ouverture (8h-20h)
    if value.hour < 8 or value.hour > 20:
        raise ValidationError(
            'Les rendez-vous doivent être planifiés entre 8h et 20h'
        )
    
    # Vérifier que le rendez-vous n'est pas le week-end
    if value.weekday() >= 5:  # 5 = Samedi, 6 = Dimanche
        raise ValidationError(
            'Les rendez-vous ne peuvent pas être planifiés le week-end'
        )


def validate_duration(value):
    """
    Valide une durée en minutes
    """
    if not value:
        return
    
    if value <= 0:
        raise ValidationError(
            'La durée doit être positive'
        )
    
    if value > 480:  # 8 heures
        raise ValidationError(
            'La durée ne peut pas dépasser 8 heures (480 minutes)'
        )


def validate_patient_name(value):
    """
    Valide un nom de patient (prénom, nom, postnom)
    """
    if not value:
        return
    
    # Vérifier la longueur
    if len(value) < 2:
        raise ValidationError(
            'Le nom doit contenir au moins 2 caractères'
        )
    
    if len(value) > 100:
        raise ValidationError(
            'Le nom ne peut pas dépasser 100 caractères'
        )
    
    # Vérifier les caractères autorisés
    if not re.match(r'^[a-zA-Zàâäéèêëïîôöùûüÿçñæœ\'\-\s]+$', value):
        raise ValidationError(
            'Le nom ne peut contenir que des lettres, des espaces, des tirets et des apostrophes'
        )


def validate_reason_text(value):
    """
    Valide un texte de motif (consultation, hospitalisation, etc.)
    """
    if not value:
        return
    
    if len(value) < 10:
        raise ValidationError(
            'Le motif doit contenir au moins 10 caractères'
        )
    
    if len(value) > 2000:
        raise ValidationError(
            'Le motif ne peut pas dépasser 2000 caractères'
        )


def validate_medical_text(value):
    """
    Valide un texte médical (diagnostic, prescription, etc.)
    """
    if not value:
        return
    
    if len(value) < 10:
        raise ValidationError(
            'Ce champ doit contenir au moins 10 caractères'
        )
    
    if len(value) > 10000:
        raise ValidationError(
            'Ce champ ne peut pas dépasser 10000 caractères'
        )


def validate_room_number(value):
    """
    Valide un numéro de chambre
    """
    if not value:
        return
    
    if not re.match(r'^[A-Z0-9-]+$', value.upper()):
        raise ValidationError(
            'Le numéro de chambre ne peut contenir que des lettres majuscules, des chiffres et des tirets'
        )


def validate_bed_number(value):
    """
    Valide un numéro de lit
    """
    if not value:
        return
    
    if not re.match(r'^[A-Z0-9]+$', value.upper()):
        raise ValidationError(
            'Le numéro de lit ne peut contenir que des lettres majuscules et des chiffres'
        )


def validate_service_name(value):
    """
    Valide un nom de service
    """
    if not value:
        return
    
    if len(value) < 2:
        raise ValidationError(
            'Le nom du service doit contenir au moins 2 caractères'
        )
    
    if len(value) > 100:
        raise ValidationError(
            'Le nom du service ne peut pas dépasser 100 caractères'
        )


def validate_triage_level(value):
    """
    Valide un niveau de triage d'urgence
    """
    valid_levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    
    if value not in valid_levels:
        raise ValidationError(
            f'Le niveau de triage doit être l\'un des suivants: {", ".join(valid_levels)}'
        )


def validate_insurance_number(value):
    """
    Valide un numéro d'assurance
    """
    if not value:
        return
    
    # Format général: lettres et chiffres, tirets autorisés
    if not re.match(r'^[A-Z0-9-]+$', value.upper()):
        raise ValidationError(
            'Le numéro d\'assurance ne peut contenir que des lettres majuscules, des chiffres et des tirets'
        )
    
    if len(value) < 5:
        raise ValidationError(
            'Le numéro d\'assurance doit contenir au moins 5 caractères'
        )
    
    if len(value) > 50:
        raise ValidationError(
            'Le numéro d\'assurance ne peut pas dépasser 50 caractères'
        )


def validate_license_number(value):
    """
    Valide un numéro de licence professionnelle
    """
    if not value:
        return
    
    # Format général: lettres et chiffres
    if not re.match(r'^[A-Z0-9]+$', value.upper()):
        raise ValidationError(
            'Le numéro de licence ne peut contenir que des lettres majuscules et des chiffres'
        )
    
    if len(value) < 5:
        raise ValidationError(
            'Le numéro de licence doit contenir au moins 5 caractères'
        )
    
    if len(value) > 50:
        raise ValidationError(
            'Le numéro de licence ne peut pas dépasser 50 caractères'
        )


# Validateurs avec expressions régulières pour Django
phone_validator = RegexValidator(
    regex=r'^\+?[\d\s\-\(\)]+$',
    message='Le numéro de téléphone n\'est pas valide',
    code='invalid_phone'
)

room_validator = RegexValidator(
    regex=r'^[A-Z0-9-]+$',
    message='Le numéro de chambre ne peut contenir que des lettres majuscules, des chiffres et des tirets',
    code='invalid_room'
)

bed_validator = RegexValidator(
    regex=r'^[A-Z0-9]+$',
    message='Le numéro de lit ne peut contenir que des lettres majuscules et des chiffres',
    code='invalid_bed'
)

insurance_validator = RegexValidator(
    regex=r'^[A-Z0-9-]+$',
    message='Le numéro d\'assurance ne peut contenir que des lettres majuscules, des chiffres et des tirets',
    code='invalid_insurance'
)

license_validator = RegexValidator(
    regex=r'^[A-Z0-9]+$',
    message='Le numéro de licence ne peut contenir que des lettres majuscules et des chiffres',
    code='invalid_license'
)