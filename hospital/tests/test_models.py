"""
Tests pour les modèles de l'application hospital
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from datetime import date, timedelta
from ..models import Patient, Centre, Profile, Consultation, Hospitalisation, Emergency, Appointment


class CentreModelTest(TestCase):
    """Tests pour le modèle Centre"""
    
    def setUp(self):
        self.centre = Centre.objects.create(
            name="Hôpital Test",
            address="123 Rue Test, 75000 Paris",
            phone="0123456789"
        )
    
    def test_centre_creation(self):
        """Test la création d'un centre"""
        self.assertEqual(self.centre.name, "Hôpital Test")
        self.assertEqual(self.centre.address, "123 Rue Test, 75000 Paris")
        self.assertEqual(self.centre.phone, "0123456789")
    
    def test_centre_str(self):
        """Test la représentation string d'un centre"""
        self.assertEqual(str(self.centre), "Hôpital Test")


class PatientModelTest(TestCase):
    """Tests pour le modèle Patient"""
    
    def setUp(self):
        self.centre = Centre.objects.create(
            name="Hôpital Test",
            address="123 Rue Test, 75000 Paris",
            phone="0123456789"
        )
        self.patient = Patient.objects.create(
            first_name="Jean",
            last_name="Dupont",
            date_of_birth=date(1990, 1, 1),
            gender="M",
            default_centre=self.centre
        )
    
    def test_patient_creation(self):
        """Test la création d'un patient"""
        self.assertEqual(self.patient.first_name, "Jean")
        self.assertEqual(self.patient.last_name, "Dupont")
        self.assertEqual(self.patient.date_of_birth, date(1990, 1, 1))
        self.assertEqual(self.patient.gender, "M")
        self.assertEqual(self.patient.default_centre, self.centre)
    
    def test_patient_str(self):
        """Test la représentation string d'un patient"""
        self.assertEqual(str(self.patient), "DUPONT Jean")
    
    def test_patient_str_with_postname(self):
        """Test la représentation string d'un patient avec postnom"""
        patient_with_postname = Patient.objects.create(
            first_name="Pierre",
            postname="de la",
            last_name="Fontaine",
            date_of_birth=date(1985, 5, 15),
            gender="M",
            default_centre=self.centre
        )
        self.assertEqual(str(patient_with_postname), "DE LA FONTAINE Pierre")
    
    def test_patient_age_calculation(self):
        """Test le calcul de l'âge d'un patient"""
        # Créer un patient avec une date de naissance connue
        birth_date = date(1990, 1, 1)
        patient = Patient.objects.create(
            first_name="Test",
            last_name="Age",
            date_of_birth=birth_date,
            gender="M",
            default_centre=self.centre
        )
        
        # Calculer l'âge attendu
        today = date.today()
        expected_age = today.year - birth_date.year - (
            (today.month, today.day) < (birth_date.month, birth_date.day)
        )
        
        # Vérifier que l'âge calculé correspond
        self.assertEqual(patient.get_age(), expected_age)


class ProfileModelTest(TestCase):
    """Tests pour le modèle Profile"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.centre = Centre.objects.create(
            name="Hôpital Test",
            address="123 Rue Test, 75000 Paris",
            phone="0123456789"
        )
        self.profile = Profile.objects.create(
            user=self.user,
            role="DOCTOR"
        )
        self.profile.centres.add(self.centre)
    
    def test_profile_creation(self):
        """Test la création d'un profil"""
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.role, "DOCTOR")
        self.assertIn(self.centre, self.profile.centres.all())
    
    def test_profile_str(self):
        """Test la représentation string d'un profil"""
        self.assertEqual(str(self.profile), "testuser (DOCTOR)")
    
    def test_profile_role_choices(self):
        """Test les choix de rôle valides"""
        valid_roles = ['ADMIN', 'MEDICAL_ADMIN', 'DOCTOR', 'NURSE', 'SECRETARY']
        
        for role in valid_roles:
            profile = Profile.objects.create(
                user=User.objects.create_user(
                    username=f"user_{role}",
                    password="testpass123"
                ),
                role=role
            )
            self.assertEqual(profile.role, role)


class ConsultationModelTest(TestCase):
    """Tests pour le modèle Consultation"""
    
    def setUp(self):
        self.centre = Centre.objects.create(
            name="Hôpital Test",
            address="123 Rue Test, 75000 Paris",
            phone="0123456789"
        )
        self.patient = Patient.objects.create(
            first_name="Jean",
            last_name="Dupont",
            date_of_birth=date(1990, 1, 1),
            gender="M",
            default_centre=self.centre
        )
        self.doctor = User.objects.create_user(
            username="doctor",
            password="testpass123"
        )
        self.consultation = Consultation.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            centre=self.centre,
            reason="Consultation de test",
            diagnosis="Diagnostic de test"
        )
    
    def test_consultation_creation(self):
        """Test la création d'une consultation"""
        self.assertEqual(self.consultation.patient, self.patient)
        self.assertEqual(self.consultation.doctor, self.doctor)
        self.assertEqual(self.consultation.centre, self.centre)
        self.assertEqual(self.consultation.reason, "Consultation de test")
        self.assertEqual(self.consultation.diagnosis, "Diagnostic de test")
        self.assertEqual(self.consultation.status, "PENDING")
    
    def test_consultation_str(self):
        """Test la représentation string d'une consultation"""
        expected = f"Consultation {self.patient} - {self.consultation.date.strftime('%d/%m/%Y')}"
        self.assertEqual(str(self.consultation), expected)
    
    def test_consultation_status_choices(self):
        """Test les choix de statut valides"""
        valid_statuses = ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']
        
        for status in valid_statuses:
            consultation = Consultation.objects.create(
                patient=self.patient,
                doctor=self.doctor,
                centre=self.centre,
                reason=f"Consultation {status}",
                status=status
            )
            self.assertEqual(consultation.status, status)


class HospitalisationModelTest(TestCase):
    """Tests pour le modèle Hospitalisation"""
    
    def setUp(self):
        self.centre = Centre.objects.create(
            name="Hôpital Test",
            address="123 Rue Test, 75000 Paris",
            phone="0123456789"
        )
        self.patient = Patient.objects.create(
            first_name="Jean",
            last_name="Dupont",
            date_of_birth=date(1990, 1, 1),
            gender="M",
            default_centre=self.centre
        )
        self.doctor = User.objects.create_user(
            username="doctor",
            password="testpass123"
        )
        self.hospitalisation = Hospitalisation.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            centre=self.centre,
            service="Cardiologie",
            room="101",
            bed="A",
            admission_reason="Hospitalisation de test"
        )
    
    def test_hospitalisation_creation(self):
        """Test la création d'une hospitalisation"""
        self.assertEqual(self.hospitalisation.patient, self.patient)
        self.assertEqual(self.hospitalisation.doctor, self.doctor)
        self.assertEqual(self.hospitalisation.centre, self.centre)
        self.assertEqual(self.hospitalisation.service, "Cardiologie")
        self.assertEqual(self.hospitalisation.room, "101")
        self.assertEqual(self.hospitalisation.bed, "A")
        self.assertEqual(self.hospitalisation.admission_reason, "Hospitalisation de test")
    
    def test_hospitalisation_str(self):
        """Test la représentation string d'une hospitalisation"""
        expected = f"Hospitalisation {self.patient} - {self.hospitalisation.service}"
        self.assertEqual(str(self.hospitalisation), expected)


class EmergencyModelTest(TestCase):
    """Tests pour le modèle Emergency"""
    
    def setUp(self):
        self.centre = Centre.objects.create(
            name="Hôpital Test",
            address="123 Rue Test, 75000 Paris",
            phone="0123456789"
        )
        self.patient = Patient.objects.create(
            first_name="Jean",
            last_name="Dupont",
            date_of_birth=date(1990, 1, 1),
            gender="M",
            default_centre=self.centre
        )
        self.doctor = User.objects.create_user(
            username="doctor",
            password="testpass123"
        )
        self.emergency = Emergency.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            centre=self.centre,
            reason="Urgence de test",
            triage_level="MEDIUM"
        )
    
    def test_emergency_creation(self):
        """Test la création d'une urgence"""
        self.assertEqual(self.emergency.patient, self.patient)
        self.assertEqual(self.emergency.doctor, self.doctor)
        self.assertEqual(self.emergency.centre, self.centre)
        self.assertEqual(self.emergency.reason, "Urgence de test")
        self.assertEqual(self.emergency.triage_level, "MEDIUM")
    
    def test_emergency_str(self):
        """Test la représentation string d'une urgence"""
        expected = f"Urgence {self.patient} - {self.emergency.admission_time.strftime('%d/%m/%Y %H:%M')}"
        self.assertEqual(str(self.emergency), expected)
    
    def test_emergency_triage_levels(self):
        """Test les niveaux de triage valides"""
        valid_levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        
        for level in valid_levels:
            emergency = Emergency.objects.create(
                patient=self.patient,
                doctor=self.doctor,
                centre=self.centre,
                reason=f"Urgence {level}",
                triage_level=level
            )
            self.assertEqual(emergency.triage_level, level)


class AppointmentModelTest(TestCase):
    """Tests pour le modèle Appointment"""
    
    def setUp(self):
        self.centre = Centre.objects.create(
            name="Hôpital Test",
            address="123 Rue Test, 75000 Paris",
            phone="0123456789"
        )
        self.patient = Patient.objects.create(
            first_name="Jean",
            last_name="Dupont",
            date_of_birth=date(1990, 1, 1),
            gender="M",
            default_centre=self.centre
        )
        self.doctor = User.objects.create_user(
            username="doctor",
            password="testpass123"
        )
        from datetime import datetime, timedelta
        appointment_date = datetime.now() + timedelta(days=1)
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            centre=self.centre,
            date=appointment_date,
            reason="Rendez-vous de test"
        )
    
    def test_appointment_creation(self):
        """Test la création d'un rendez-vous"""
        self.assertEqual(self.appointment.patient, self.patient)
        self.assertEqual(self.appointment.doctor, self.doctor)
        self.assertEqual(self.appointment.centre, self.centre)
        self.assertEqual(self.appointment.reason, "Rendez-vous de test")
        self.assertEqual(self.appointment.status, "SCHEDULED")
        self.assertEqual(self.appointment.duration, 30)
    
    def test_appointment_str(self):
        """Test la représentation string d'un rendez-vous"""
        expected = f"Rendez-vous {self.patient} - {self.doctor} - {self.appointment.date.strftime('%d/%m/%Y %H:%M')}"
        self.assertEqual(str(self.appointment), expected)
    
    def test_appointment_status_choices(self):
        """Test les choix de statut valides"""
        valid_statuses = ['SCHEDULED', 'CONFIRMED', 'COMPLETED', 'CANCELLED']
        
        for status in valid_statuses:
            from datetime import datetime, timedelta
            appointment_date = datetime.now() + timedelta(days=1)
            appointment = Appointment.objects.create(
                patient=self.patient,
                doctor=self.doctor,
                centre=self.centre,
                date=appointment_date,
                reason=f"Rendez-vous {status}",
                status=status
            )
            self.assertEqual(appointment.status, status)