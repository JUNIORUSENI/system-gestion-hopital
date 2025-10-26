"""
Modèles optimisés avec contraintes et indexes
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import date


# --------------------
# CENTRE
# --------------------
class Centre(models.Model):
    name = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name="Nom du centre",
        help_text="Nom unique du centre hospitalier"
    )
    address = models.TextField(
        verbose_name="Adresse",
        help_text="Adresse complète du centre"
    )
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?[\d\s\-\(\)]+$',
                message="Le numéro de téléphone n'est pas valide"
            )
        ],
        verbose_name="Téléphone",
        help_text="Numéro de téléphone du centre"
    )
    email = models.EmailField(
        blank=True, 
        null=True,
        verbose_name="Email",
        help_text="Email du centre"
    )
    capacity = models.PositiveIntegerField(
        default=100,
        verbose_name="Capacité",
        help_text="Nombre maximal de patients"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Indique si le centre est actif"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Centre"
        verbose_name_plural = "Centres"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name


# --------------------
# PATIENT
# --------------------
class Patient(models.Model):
    # Infos administratives (secrétariat)
    first_name = models.CharField(
        max_length=100,
        verbose_name="Prénom",
        help_text="Prénom du patient"
    )
    postname = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Postnom",
        help_text="Postnom du patient"
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name="Nom de famille",
        help_text="Nom de famille du patient"
    )
    date_of_birth = models.DateField(
        verbose_name="Date de naissance",
        help_text="Date de naissance du patient"
    )
    gender = models.CharField(
        max_length=10, 
        choices=[('M', 'Masculin'), ('F', 'Féminin')],
        verbose_name="Genre",
        help_text="Genre du patient"
    )
    phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?[\d\s\-\(\)]+$',
                message="Le numéro de téléphone n'est pas valide"
            )
        ],
        verbose_name="Téléphone",
        help_text="Numéro de téléphone du patient"
    )
    address = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Adresse",
        help_text="Adresse du patient"
    )
    emergency_contact = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Contact d'urgence",
        help_text="Personne à contacter en cas d'urgence"
    )
    is_subscriber = models.BooleanField(
        default=False,
        verbose_name="Abonné",
        help_text="Indique si le patient est abonné"
    )
    insurance_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Numéro d'assurance",
        help_text="Numéro d'assurance maladie"
    )

    # Centre habituel
    default_centre = models.ForeignKey(
        Centre, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="patients",
        verbose_name="Centre par défaut",
        help_text="Centre de santé habituel du patient"
    )

    # Infos médicales (médecin)
    medical_history = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Antécédents médicaux",
        help_text="Historique médical du patient"
    )
    allergies = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Allergies",
        help_text="Allergies connues du patient"
    )
    vaccinations = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Vaccinations",
        help_text="Vaccinations du patient"
    )
    lifestyle = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Mode de vie",
        help_text="Informations sur le mode de vie du patient"
    )
    
    # Champs d'audit
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_patients",
        verbose_name="Créé par",
        help_text="Utilisateur qui a créé le patient"
    )
    modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="modified_patients",
        verbose_name="Modifié par",
        help_text="Dernier utilisateur à avoir modifié le patient"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Patient"
        verbose_name_plural = "Patients"
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['date_of_birth']),
            models.Index(fields=['default_centre']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(date_of_birth__lte=timezone.now().date()),
                name='date_of_birth_not_future',
                violation_error_message="La date de naissance ne peut pas être dans le futur"
            ),
            models.UniqueConstraint(
                fields=['first_name', 'last_name', 'date_of_birth'],
                name='unique_patient',
                violation_error_message="Un patient avec le même nom et la même date de naissance existe déjà"
            ),
        ]

    def __str__(self):
        full_name = self.last_name.upper()
        if self.postname:
            full_name += f" {self.postname.upper()}"
        full_name += f" {self.first_name}"
        return full_name

    def get_age(self):
        """Calcule l'âge du patient"""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )


# --------------------
# CONSULTATION
# --------------------
class Consultation(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'En attente'
        IN_PROGRESS = 'IN_PROGRESS', 'En cours'
        COMPLETED = 'COMPLETED', 'Terminée'
        CANCELLED = 'CANCELLED', 'Annulée'

    patient = models.ForeignKey(
        Patient, 
        on_delete=models.CASCADE, 
        related_name="consultations",
        verbose_name="Patient",
        help_text="Patient concerné par la consultation"
    )
    doctor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="consultations",
        verbose_name="Médecin",
        help_text="Médecin traitant"
    )
    centre = models.ForeignKey(
        Centre, 
        on_delete=models.CASCADE, 
        related_name="consultations",
        verbose_name="Centre",
        help_text="Centre de la consultation"
    )
    date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date",
        help_text="Date de création de la consultation"
    )
    appointment_date = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Date du rendez-vous",
        help_text="Date programmée pour la consultation"
    )
    status = models.CharField(
        max_length=20, 
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Statut",
        help_text="Statut de la consultation"
    )
    reason = models.TextField(
        verbose_name="Motif",
        help_text="Motif de la consultation"
    )
    clinical_exam = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Examen clinique",
        help_text="Résultats de l'examen clinique"
    )
    diagnosis = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Diagnostic",
        help_text="Diagnostic du médecin"
    )
    prescription = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Prescription",
        help_text="Prescription médicale"
    )
    follow_up_date = models.DateField(
        blank=True, 
        null=True,
        verbose_name="Date de suivi",
        help_text="Date prévue pour le suivi"
    )
    end_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Heure de fin",
        help_text="Heure de fin de la consultation"
    )
    
    # Champs d'audit
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_consultations",
        verbose_name="Créé par",
        help_text="Utilisateur qui a créé la consultation"
    )
    modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="modified_consultations",
        verbose_name="Modifié par",
        help_text="Dernier utilisateur à avoir modifié la consultation"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Consultation"
        verbose_name_plural = "Consultations"
        ordering = ['-date']
        indexes = [
            models.Index(fields=['patient', 'date']),
            models.Index(fields=['doctor', 'date']),
            models.Index(fields=['centre', 'date']),
            models.Index(fields=['status']),
            models.Index(fields=['appointment_date']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(appointment_date__isnull=True) | models.Q(appointment_date__gte=models.F('date')),
                name='appointment_date_after_creation',
                violation_error_message="La date du rendez-vous ne peut pas être antérieure à la date de création"
            ),
            models.CheckConstraint(
                check=models.Q(follow_up_date__isnull=True) | models.Q(follow_up_date__gte=models.F('date')),
                name='follow_up_date_after_creation',
                violation_error_message="La date de suivi ne peut pas être antérieure à la date de création"
            ),
        ]

    def __str__(self):
        return f"Consultation {self.patient} - {self.date.strftime('%d/%m/%Y')}"


# --------------------
# HOSPITALISATION
# --------------------
class Hospitalisation(models.Model):
    patient = models.ForeignKey(
        Patient, 
        on_delete=models.CASCADE, 
        related_name="hospitalisations",
        verbose_name="Patient",
        help_text="Patient hospitalisé"
    )
    doctor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="hospitalisations",
        verbose_name="Médecin",
        help_text="Médecin traitant"
    )
    centre = models.ForeignKey(
        Centre, 
        on_delete=models.CASCADE, 
        related_name="hospitalisations",
        verbose_name="Centre",
        help_text="Centre d'hospitalisation"
    )
    admission_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'admission",
        help_text="Date et heure d'admission"
    )
    discharge_date = models.DateTimeField(
        blank=True, 
        null=True,
        verbose_name="Date de sortie",
        help_text="Date et heure de sortie"
    )
    service = models.CharField(
        max_length=100,
        verbose_name="Service",
        help_text="Service d'hospitalisation"
    )
    room = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name="Chambre",
        help_text="Numéro de chambre"
    )
    bed = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name="Lit",
        help_text="Numéro de lit"
    )
    admission_reason = models.TextField(
        verbose_name="Motif d'admission",
        help_text="Raison de l'hospitalisation"
    )
    medical_notes = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Notes médicales",
        help_text="Notes médicales"
    )
    nurse_notes = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Notes infirmières",
        help_text="Notes des infirmiers"
    )
    interventions = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Interventions",
        help_text="Interventions réalisées"
    )
    discharge_summary = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Résumé de sortie",
        help_text="Résumé de la sortie"
    )
    discharge_instructions = models.TextField(
        blank=True,
        null=True,
        verbose_name="Instructions de sortie",
        help_text="Instructions pour le patient à la sortie"
    )
    
    # Champs d'audit
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_hospitalisations",
        verbose_name="Créé par",
        help_text="Utilisateur qui a créé l'hospitalisation"
    )
    modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="modified_hospitalisations",
        verbose_name="Modifié par",
        help_text="Dernier utilisateur à avoir modifié l'hospitalisation"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Hospitalisation"
        verbose_name_plural = "Hospitalisations"
        ordering = ['-admission_date']
        indexes = [
            models.Index(fields=['patient', 'admission_date']),
            models.Index(fields=['doctor', 'admission_date']),
            models.Index(fields=['centre', 'service']),
            models.Index(fields=['room', 'bed']),
            models.Index(fields=['admission_date']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(discharge_date__isnull=True) | models.Q(discharge_date__gte=models.F('admission_date')),
                name='discharge_date_after_admission',
                violation_error_message="La date de sortie ne peut pas être antérieure à la date d'admission"
            ),
        ]

    def __str__(self):
        return f"Hospitalisation {self.patient} - {self.service}"
    
    @property
    def is_active(self):
        """Indique si l'hospitalisation est active"""
        return self.discharge_date is None
    
    @property
    def duration_days(self):
        """Calcule la durée de l'hospitalisation en jours"""
        if self.discharge_date:
            return (self.discharge_date - self.admission_date).days
        else:
            return (timezone.now() - self.admission_date).days


# --------------------
# URGENCE
# --------------------
class Emergency(models.Model):
    class TriageLevel(models.TextChoices):
        LOW = 'LOW', 'Léger'
        MEDIUM = 'MEDIUM', 'Moyen'
        HIGH = 'HIGH', 'Grave'
        CRITICAL = 'CRITICAL', 'Vital'

    class Orientation(models.TextChoices):
        DISCHARGED = 'DISCHARGED', 'Sortie'
        HOSPITALISED = 'HOSPITALISED', 'Hospitalisation'
        TRANSFERRED = 'TRANSFERRED', 'Transfert'

    patient = models.ForeignKey(
        Patient, 
        on_delete=models.CASCADE, 
        related_name="emergencies",
        verbose_name="Patient",
        help_text="Patient concerné par l'urgence"
    )
    doctor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="emergencies",
        verbose_name="Médecin",
        help_text="Médecin traitant"
    )
    centre = models.ForeignKey(
        Centre, 
        on_delete=models.CASCADE, 
        related_name="emergencies",
        verbose_name="Centre",
        help_text="Centre des urgences"
    )
    admission_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Heure d'admission",
        help_text="Heure d'admission aux urgences"
    )
    triage_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Heure de triage",
        help_text="Heure du triage"
    )
    reason = models.TextField(
        verbose_name="Motif",
        help_text="Motif de l'urgence"
    )
    triage_level = models.CharField(
        max_length=10, 
        choices=TriageLevel.choices,
        verbose_name="Niveau de triage",
        help_text="Niveau de priorité de l'urgence"
    )
    vital_signs = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Signes vitaux",
        help_text="Signes vitaux du patient"
    )
    first_aid = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Premiers secours",
        help_text="Premiers secours administrés"
    )
    initial_diagnosis = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Diagnostic initial",
        help_text="Diagnostic initial"
    )
    orientation = models.CharField(
        max_length=100,
        choices=Orientation.choices,
        blank=True, 
        null=True,
        verbose_name="Orientation",
        help_text="Orientation du patient"
    )
    orientation_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Heure d'orientation",
        help_text="Heure de l'orientation"
    )
    orientation_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes d'orientation",
        help_text="Notes relatives à l'orientation"
    )
    
    # Champs d'audit
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_emergencies",
        verbose_name="Créé par",
        help_text="Utilisateur qui a créé l'urgence"
    )
    modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="modified_emergencies",
        verbose_name="Modifié par",
        help_text="Dernier utilisateur à avoir modifié l'urgence"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Urgence"
        verbose_name_plural = "Urgences"
        ordering = ['-admission_time']
        indexes = [
            models.Index(fields=['patient', 'admission_time']),
            models.Index(fields=['doctor', 'admission_time']),
            models.Index(fields=['centre', 'triage_level']),
            models.Index(fields=['triage_level', 'admission_time']),
            models.Index(fields=['orientation']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(triage_time__isnull=True) | models.Q(triage_time__gte=models.F('admission_time')),
                name='triage_time_after_admission',
                violation_error_message="L'heure de triage ne peut pas être antérieure à l'heure d'admission"
            ),
            models.CheckConstraint(
                check=models.Q(orientation_time__isnull=True) | models.Q(orientation_time__gte=models.F('admission_time')),
                name='orientation_time_after_admission',
                violation_error_message="L'heure d'orientation ne peut pas être antérieure à l'heure d'admission"
            ),
        ]

    def __str__(self):
        return f"Urgence {self.patient} - {self.admission_time.strftime('%d/%m/%Y %H:%M')}"
    
    @property
    def waiting_time_minutes(self):
        """Calcule le temps d'attente en minutes"""
        if self.triage_time:
            return (self.triage_time - self.admission_time).total_seconds() // 60
        else:
            return (timezone.now() - self.admission_time).total_seconds() // 60


# --------------------
# PROFIL UTILISATEUR
# --------------------
class Profile(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrateur'
        MEDICAL_ADMIN = 'MEDICAL_ADMIN', 'Médecin Administrateur'
        DOCTOR = 'DOCTOR', 'Médecin'
        NURSE = 'NURSE', 'Infirmier'
        SECRETARY = 'SECRETARY', 'Secrétaire'

    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        verbose_name="Utilisateur",
        help_text="Utilisateur associé au profil"
    )
    role = models.CharField(
        max_length=20, 
        choices=Role.choices,
        verbose_name="Rôle",
        help_text="Rôle de l'utilisateur dans le système"
    )
    centres = models.ManyToManyField(
        Centre, 
        related_name="staff",
        verbose_name="Centres",
        help_text="Centres auxquels l'utilisateur est associé"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?[\d\s\-\(\)]+$',
                message="Le numéro de téléphone n'est pas valide"
            )
        ],
        verbose_name="Téléphone",
        help_text="Numéro de téléphone professionnel"
    )
    license_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Numéro de licence",
        help_text="Numéro de licence professionnelle"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Indique si le profil est actif"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profils"
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


# --------------------
# APPOINTMENT (RENDEZ-VOUS)
# --------------------
class Appointment(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Planifié'
        CONFIRMED = 'CONFIRMED', 'Confirmé'
        COMPLETED = 'COMPLETED', 'Terminé'
        CANCELLED = 'CANCELLED', 'Annulé'

    patient = models.ForeignKey(
        Patient, 
        on_delete=models.CASCADE, 
        related_name="appointments",
        verbose_name="Patient",
        help_text="Patient concerné par le rendez-vous"
    )
    doctor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="appointments",
        verbose_name="Médecin",
        help_text="Médecin concerné par le rendez-vous"
    )
    centre = models.ForeignKey(
        Centre, 
        on_delete=models.CASCADE, 
        related_name="appointments",
        verbose_name="Centre",
        help_text="Centre du rendez-vous"
    )
    date = models.DateTimeField(
        verbose_name="Date",
        help_text="Date et heure du rendez-vous"
    )
    duration = models.IntegerField(
        default=30,
        verbose_name="Durée (minutes)",
        help_text="Durée prévue du rendez-vous en minutes"
    )
    status = models.CharField(
        max_length=20, 
        choices=Status.choices,
        default=Status.SCHEDULED,
        verbose_name="Statut",
        help_text="Statut du rendez-vous"
    )
    reason = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Motif",
        help_text="Motif du rendez-vous"
    )
    notes = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Notes",
        help_text="Notes supplémentaires"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Heure de fin",
        help_text="Heure de fin effective du rendez-vous"
    )
    
    # Champs d'audit
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_appointments",
        verbose_name="Créé par",
        help_text="Utilisateur qui a créé le rendez-vous"
    )
    modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="modified_appointments",
        verbose_name="Modifié par",
        help_text="Dernier utilisateur à avoir modifié le rendez-vous"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Rendez-vous"
        verbose_name_plural = "Rendez-vous"
        ordering = ['date']
        indexes = [
            models.Index(fields=['patient', 'date']),
            models.Index(fields=['doctor', 'date']),
            models.Index(fields=['centre', 'date']),
            models.Index(fields=['status']),
            models.Index(fields=['date']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(duration__gte=5),
                name='duration_minimum',
                violation_error_message="La durée doit être d'au moins 5 minutes"
            ),
            models.CheckConstraint(
                check=models.Q(completed_at__isnull=True) | models.Q(completed_at__gte=models.F('date')),
                name='completion_after_start',
                violation_error_message="L'heure de fin ne peut pas être antérieure à l'heure de début"
            ),
        ]

    def __str__(self):
        return f"Rendez-vous {self.patient} - {self.doctor} - {self.date.strftime('%d/%m/%Y %H:%M')}"
    
    @property
    def end_time(self):
        """Calcule l'heure de fin prévue du rendez-vous"""
        from datetime import timedelta
        return self.date + timedelta(minutes=self.duration)