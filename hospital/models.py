from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from datetime import date, timedelta


# Validateur pour numéro de téléphone congolais
phone_validator = RegexValidator(
    regex=r'^\+?243[0-9]{9}$|^0[0-9]{9}$',
    message="Le numéro de téléphone doit être au format congolais : +243XXXXXXXXX ou 0XXXXXXXXX"
)


# --------------------
# CENTRE
# --------------------
class Centre(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    address = models.TextField()
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[phone_validator]
    )

    class Meta:
        ordering = ['name']
        verbose_name = "Centre médical"
        verbose_name_plural = "Centres médicaux"

    def __str__(self):
        return self.name


# --------------------
# PATIENT
# --------------------
class Patient(models.Model):
    # Infos administratives (secrétariat)
    first_name = models.CharField(max_length=100, db_index=True)
    postname = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, db_index=True)
    date_of_birth = models.DateField(db_index=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Masculin'), ('F', 'Féminin')])
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[phone_validator],
        db_index=True
    )
    address = models.TextField(blank=True, null=True)
    emergency_contact = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[phone_validator]
    )
    is_subscriber = models.BooleanField(default=False)

    # Centre habituel
    default_centre = models.ForeignKey(
        Centre,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="patients"
    )

    # Infos médicales (médecin)
    medical_history = models.TextField(blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    vaccinations = models.TextField(blank=True, null=True)
    lifestyle = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = "Patient"
        verbose_name_plural = "Patients"
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['date_of_birth']),
            models.Index(fields=['created_at']),
        ]

    def clean(self):
        """Validation personnalisée"""
        super().clean()
        
        # Vérifier que la date de naissance n'est pas dans le futur
        if self.date_of_birth and self.date_of_birth > date.today():
            raise ValidationError({'date_of_birth': "La date de naissance ne peut pas être dans le futur."})
        
        # Vérifier que l'âge est réaliste (pas plus de 120 ans)
        if self.date_of_birth:
            age = (date.today() - self.date_of_birth).days / 365.25
            if age > 120:
                raise ValidationError({'date_of_birth': "La date de naissance n'est pas valide (âge > 120 ans)."})
            if age < 0:
                raise ValidationError({'date_of_birth': "La date de naissance n'est pas valide."})

    def save(self, *args, **kwargs):
        """Override save pour appeler clean"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        full_name = self.last_name.upper()
        if self.postname:
            full_name += f" {self.postname.upper()}"
        full_name += f" {self.first_name}"
        return full_name

    @property
    def age(self):
        """Calcule l'âge du patient"""
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None


# --------------------
# CONSULTATION
# --------------------
class Consultation(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="consultations")
    doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    centre = models.ForeignKey(Centre, on_delete=models.CASCADE, related_name="consultations")
    date = models.DateTimeField(auto_now_add=True, db_index=True)
    appointment_date = models.DateTimeField(null=True, blank=True, db_index=True)
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'En attente'),
        ('IN_PROGRESS', 'En cours'),
        ('COMPLETED', 'Terminée'),
        ('CANCELLED', 'Annulée')
    ], default='PENDING', db_index=True)

    reason = models.TextField()
    clinical_exam = models.TextField(blank=True, null=True)
    diagnosis = models.TextField(blank=True, null=True)
    prescription = models.TextField(blank=True, null=True)
    follow_up_date = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ['-date']
        verbose_name = "Consultation"
        verbose_name_plural = "Consultations"
        indexes = [
            models.Index(fields=['-date']),
            models.Index(fields=['patient', '-date']),
            models.Index(fields=['doctor', '-date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Consultation {self.patient} - {self.date.strftime('%d/%m/%Y')}"


# --------------------
# HOSPITALISATION
# --------------------
class Hospitalisation(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="hospitalisations")
    doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    centre = models.ForeignKey(Centre, on_delete=models.CASCADE, related_name="hospitalisations")
    admission_date = models.DateTimeField(auto_now_add=True, db_index=True)
    discharge_date = models.DateTimeField(blank=True, null=True, db_index=True)

    service = models.CharField(max_length=100, db_index=True)
    room = models.CharField(max_length=20, blank=True, null=True)
    bed = models.CharField(max_length=20, blank=True, null=True)

    admission_reason = models.TextField()
    medical_notes = models.TextField(blank=True, null=True)
    nurse_notes = models.TextField(blank=True, null=True)
    interventions = models.TextField(blank=True, null=True)
    discharge_summary = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-admission_date']
        verbose_name = "Hospitalisation"
        verbose_name_plural = "Hospitalisations"
        indexes = [
            models.Index(fields=['-admission_date']),
            models.Index(fields=['patient', '-admission_date']),
            models.Index(fields=['discharge_date']),
            models.Index(fields=['service']),
        ]

    def __str__(self):
        return f"Hospitalisation {self.patient} - {self.service}"

    @property
    def is_active(self):
        """Vérifie si l'hospitalisation est active (pas encore sortie)"""
        return self.discharge_date is None


# --------------------
# URGENCE
# --------------------
class Emergency(models.Model):
    URGENCY_LEVELS = [
        ('LOW', 'Léger'),
        ('MEDIUM', 'Moyen'),
        ('HIGH', 'Grave'),
        ('CRITICAL', 'Vital'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="emergencies")
    doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    centre = models.ForeignKey(Centre, on_delete=models.CASCADE, related_name="emergencies")
    admission_time = models.DateTimeField(auto_now_add=True, db_index=True)

    reason = models.TextField()
    triage_level = models.CharField(max_length=10, choices=URGENCY_LEVELS, db_index=True)
    vital_signs = models.TextField(blank=True, null=True)
    first_aid = models.TextField(blank=True, null=True)
    initial_diagnosis = models.TextField(blank=True, null=True)

    orientation = models.CharField(
        max_length=100,
        choices=[
            ('DISCHARGED', 'Sortie'),
            ('HOSPITALISED', 'Hospitalisation'),
            ('TRANSFERRED', 'Transfert'),
        ],
        blank=True, null=True,
        db_index=True
    )

    class Meta:
        ordering = ['-admission_time']
        verbose_name = "Urgence"
        verbose_name_plural = "Urgences"
        indexes = [
            models.Index(fields=['-admission_time']),
            models.Index(fields=['patient', '-admission_time']),
            models.Index(fields=['triage_level']),
            models.Index(fields=['orientation']),
        ]

    def __str__(self):
        return f"Urgence {self.patient} - {self.admission_time.strftime('%d/%m/%Y %H:%M')}"


# --------------------
# PROFIL UTILISATEUR
# --------------------
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[
        ('ADMIN', 'Administrateur'),
        ('MEDICAL_ADMIN', 'Médecin Administrateur'),
        ('DOCTOR', 'Médecin'),
        ('NURSE', 'Infirmier'),
        ('SECRETARY', 'Secrétaire'),
    ], db_index=True)
    centres = models.ManyToManyField(Centre, related_name="staff", blank=True)

    class Meta:
        ordering = ['user__username']
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateurs"

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    def has_admin_rights(self):
        """Vérifie si l'utilisateur a des droits d'admin"""
        return self.role in ['ADMIN', 'MEDICAL_ADMIN']

    def has_medical_rights(self):
        """Vérifie si l'utilisateur a des droits médicaux"""
        return self.role in ['DOCTOR', 'MEDICAL_ADMIN', 'NURSE']


# --------------------
# APPOINTMENT (RENDEZ-VOUS)
# --------------------
class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    centre = models.ForeignKey(Centre, on_delete=models.CASCADE, related_name="appointments")
    date = models.DateTimeField(db_index=True)
    reason = models.TextField(blank=True, null=True)
    duration = models.IntegerField(
        default=30,
        validators=[MinValueValidator(15), MaxValueValidator(180)]
    )
    status = models.CharField(max_length=20, choices=[
        ('SCHEDULED', 'Planifié'),
        ('CONFIRMED', 'Confirmé'),
        ('COMPLETED', 'Terminé'),
        ('CANCELLED', 'Annulé')
    ], default='SCHEDULED', db_index=True)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date']
        verbose_name = "Rendez-vous"
        verbose_name_plural = "Rendez-vous"
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['patient', 'date']),
            models.Index(fields=['doctor', 'date']),
            models.Index(fields=['status']),
        ]

    def clean(self):
        """Validation des chevauchements de rendez-vous"""
        super().clean()
        
        if self.date and self.doctor and self.duration:
            # Calculer l'heure de fin
            from datetime import timedelta
            end_time = self.date + timedelta(minutes=self.duration)
            
            # Vérifier les chevauchements pour le même médecin
            overlapping = Appointment.objects.filter(
                doctor=self.doctor,
                date__lt=end_time,
                date__gte=self.date - timedelta(minutes=180)
            ).exclude(pk=self.pk if self.pk else None)
            
            if overlapping.exists():
                raise ValidationError({
                    'date': "Ce créneau horaire chevauche un autre rendez-vous du médecin."
                })

    def __str__(self):
        return f"Rendez-vous {self.patient} - {self.doctor} - {self.date.strftime('%d/%m/%Y %H:%M')}"