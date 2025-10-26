from django.db import models
from django.contrib.auth.models import User


# --------------------
# CENTRE
# --------------------
class Centre(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.name


# --------------------
# PATIENT
# --------------------
class Patient(models.Model):
    # Infos administratives (secrétariat)
    first_name = models.CharField(max_length=100)
    postname = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=[('M', 'Masculin'), ('F', 'Féminin')])
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    emergency_contact = models.CharField(max_length=100, blank=True, null=True)
    is_subscriber = models.BooleanField(default=False)

    # Centre habituel
    default_centre = models.ForeignKey(Centre, on_delete=models.SET_NULL, null=True, blank=True, related_name="patients")

    # Infos médicales (médecin)
    medical_history = models.TextField(blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    vaccinations = models.TextField(blank=True, null=True)
    lifestyle = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        full_name = self.last_name.upper()
        if self.postname:
            full_name += f" {self.postname.upper()}"
        full_name += f" {self.first_name}"
        return full_name


# --------------------
# CONSULTATION
# --------------------
class Consultation(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="consultations")
    doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    centre = models.ForeignKey(Centre, on_delete=models.CASCADE, related_name="consultations")
    date = models.DateTimeField(auto_now_add=True)
    appointment_date = models.DateTimeField(null=True, blank=True)  # Date du rendez-vous
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'En attente'),
        ('IN_PROGRESS', 'En cours'),
        ('COMPLETED', 'Terminée'),
        ('CANCELLED', 'Annulée')
    ], default='PENDING')  # Statut de la consultation

    reason = models.TextField()
    clinical_exam = models.TextField(blank=True, null=True)
    diagnosis = models.TextField(blank=True, null=True)
    prescription = models.TextField(blank=True, null=True)
    follow_up_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"Consultation {self.patient} - {self.date.strftime('%d/%m/%Y')}"


# --------------------
# HOSPITALISATION
# --------------------
class Hospitalisation(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="hospitalisations")
    doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    centre = models.ForeignKey(Centre, on_delete=models.CASCADE, related_name="hospitalisations")
    admission_date = models.DateTimeField(auto_now_add=True)
    discharge_date = models.DateTimeField(blank=True, null=True)

    service = models.CharField(max_length=100)
    room = models.CharField(max_length=20, blank=True, null=True)
    bed = models.CharField(max_length=20, blank=True, null=True)

    admission_reason = models.TextField()
    medical_notes = models.TextField(blank=True, null=True)
    nurse_notes = models.TextField(blank=True, null=True)
    interventions = models.TextField(blank=True, null=True)
    discharge_summary = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Hospitalisation {self.patient} - {self.service}"


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
    admission_time = models.DateTimeField(auto_now_add=True)

    reason = models.TextField()
    triage_level = models.CharField(max_length=10, choices=URGENCY_LEVELS)
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
        blank=True, null=True
    )

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
    ])
    centres = models.ManyToManyField(Centre, related_name="staff")

    def __str__(self):
        return f"{self.user.username} ({self.role})"


# --------------------
# APPOINTMENT (RENDEZ-VOUS)
# --------------------
class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    centre = models.ForeignKey(Centre, on_delete=models.CASCADE, related_name="appointments")
    date = models.DateTimeField()
    reason = models.TextField(blank=True, null=True)
    duration = models.IntegerField(default=30)  # Durée en minutes
    status = models.CharField(max_length=20, choices=[
        ('SCHEDULED', 'Planifié'),
        ('CONFIRMED', 'Confirmé'),
        ('COMPLETED', 'Terminé'),
        ('CANCELLED', 'Annulé')
    ], default='SCHEDULED')
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Rendez-vous {self.patient} - {self.doctor} - {self.date.strftime('%d/%m/%Y %H:%M')}"