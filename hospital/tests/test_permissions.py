"""
Tests pour le système de permissions
"""
from django.test import TestCase
from django.contrib.auth.models import User, AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from unittest.mock import Mock
from ..models import Patient, Centre, Profile
from ..permissions import (
    IsAuthenticated, IsAdmin, IsDoctor, IsNurse, IsSecretary,
    CanAccessPatient, CanManagePatientAdminData, CanManagePatientMedicalData,
    CanAccessStatistics, CanManageUsers, CanManageCentres, CanManageAppointments,
    permission_required, object_permission_required
)


class BasePermissionTest(TestCase):
    """Tests de base pour les permissions"""
    
    def setUp(self):
        self.centre = Centre.objects.create(
            name="Hôpital Test",
            address="123 Rue Test, 75000 Paris",
            phone="0123456789"
        )
        
        # Créer des utilisateurs avec différents rôles
        self.admin_user = User.objects.create_user(
            username="admin",
            password="testpass123"
        )
        Profile.objects.create(user=self.admin_user, role="ADMIN")
        
        self.doctor_user = User.objects.create_user(
            username="doctor",
            password="testpass123"
        )
        Profile.objects.create(user=self.doctor_user, role="DOCTOR")
        
        self.nurse_user = User.objects.create_user(
            username="nurse",
            password="testpass123"
        )
        Profile.objects.create(user=self.nurse_user, role="NURSE")
        
        self.secretary_user = User.objects.create_user(
            username="secretary",
            password="testpass123"
        )
        Profile.objects.create(user=self.secretary_user, role="SECRETARY")
        
        # Ajouter les centres aux profils
        for user in [self.doctor_user, self.nurse_user, self.secretary_user]:
            user.profile.centres.add(self.centre)
        
        # Créer un patient
        self.patient = Patient.objects.create(
            first_name="Jean",
            last_name="Dupont",
            date_of_birth="1990-01-01",
            gender="M",
            default_centre=self.centre
        )
        
        # Créer un utilisateur anonyme
        self.anonymous_user = AnonymousUser()


class IsAuthenticatedTest(BasePermissionTest):
    """Tests pour la permission IsAuthenticated"""
    
    def test_authenticated_user_has_permission(self):
        """Test qu'un utilisateur authentifié a la permission"""
        permission = IsAuthenticated()
        request = Mock()
        request.user = self.doctor_user
        
        self.assertTrue(permission.has_permission(request, None))
    
    def test_anonymous_user_has_no_permission(self):
        """Test qu'un utilisateur anonyme n'a pas la permission"""
        permission = IsAuthenticated()
        request = Mock()
        request.user = self.anonymous_user
        
        self.assertFalse(permission.has_permission(request, None))


class IsAdminTest(BasePermissionTest):
    """Tests pour la permission IsAdmin"""
    
    def test_admin_has_permission(self):
        """Test qu'un administrateur a la permission"""
        permission = IsAdmin()
        request = Mock()
        request.user = self.admin_user
        
        self.assertTrue(permission.has_permission(request, None))
    
    def test_non_admin_has_no_permission(self):
        """Test qu'un non-administrateur n'a pas la permission"""
        permission = IsAdmin()
        request = Mock()
        request.user = self.doctor_user
        
        self.assertFalse(permission.has_permission(request, None))
    
    def test_anonymous_user_has_no_permission(self):
        """Test qu'un utilisateur anonyme n'a pas la permission"""
        permission = IsAdmin()
        request = Mock()
        request.user = self.anonymous_user
        
        self.assertFalse(permission.has_permission(request, None))


class IsDoctorTest(BasePermissionTest):
    """Tests pour la permission IsDoctor"""
    
    def test_doctor_has_permission(self):
        """Test qu'un médecin a la permission"""
        permission = IsDoctor()
        request = Mock()
        request.user = self.doctor_user
        
        self.assertTrue(permission.has_permission(request, None))
    
    def test_non_doctor_has_no_permission(self):
        """Test qu'un non-médecin n'a pas la permission"""
        permission = IsDoctor()
        request = Mock()
        request.user = self.nurse_user
        
        self.assertFalse(permission.has_permission(request, None))


class IsNurseTest(BasePermissionTest):
    """Tests pour la permission IsNurse"""
    
    def test_nurse_has_permission(self):
        """Test qu'un infirmier a la permission"""
        permission = IsNurse()
        request = Mock()
        request.user = self.nurse_user
        
        self.assertTrue(permission.has_permission(request, None))
    
    def test_non_nurse_has_no_permission(self):
        """Test qu'un non-infirmier n'a pas la permission"""
        permission = IsNurse()
        request = Mock()
        request.user = self.doctor_user
        
        self.assertFalse(permission.has_permission(request, None))


class IsSecretaryTest(BasePermissionTest):
    """Tests pour la permission IsSecretary"""
    
    def test_secretary_has_permission(self):
        """Test qu'un secrétaire a la permission"""
        permission = IsSecretary()
        request = Mock()
        request.user = self.secretary_user
        
        self.assertTrue(permission.has_permission(request, None))
    
    def test_non_secretary_has_no_permission(self):
        """Test qu'un non-secrétaire n'a pas la permission"""
        permission = IsSecretary()
        request = Mock()
        request.user = self.doctor_user
        
        self.assertFalse(permission.has_permission(request, None))


class CanAccessPatientTest(BasePermissionTest):
    """Tests pour la permission CanAccessPatient"""
    
    def test_admin_can_access_any_patient(self):
        """Test qu'un administrateur peut accéder à n'importe quel patient"""
        permission = CanAccessPatient()
        request = Mock()
        request.user = self.admin_user
        
        self.assertTrue(permission.has_permission(request, None))
        self.assertTrue(permission.has_object_permission(request, None, self.patient))
    
    def test_doctor_can_access_any_patient(self):
        """Test qu'un médecin peut accéder à n'importe quel patient"""
        permission = CanAccessPatient()
        request = Mock()
        request.user = self.doctor_user
        
        self.assertTrue(permission.has_permission(request, None))
        self.assertTrue(permission.has_object_permission(request, None, self.patient))
    
    def test_secretary_can_access_patient_from_own_centre(self):
        """Test qu'un secrétaire peut accéder aux patients de son centre"""
        permission = CanAccessPatient()
        request = Mock()
        request.user = self.secretary_user
        
        self.assertTrue(permission.has_permission(request, None))
        self.assertTrue(permission.has_object_permission(request, None, self.patient))
    
    def test_secretary_cannot_access_patient_from_other_centre(self):
        """Test qu'un secrétaire ne peut pas accéder aux patients d'un autre centre"""
        # Créer un autre centre et un patient
        other_centre = Centre.objects.create(
            name="Autre Hôpital",
            address="456 Autre Rue, 69000 Lyon",
            phone="0987654321"
        )
        other_patient = Patient.objects.create(
            first_name="Marie",
            last_name="Durand",
            date_of_birth="1985-05-15",
            gender="F",
            default_centre=other_centre
        )
        
        permission = CanAccessPatient()
        request = Mock()
        request.user = self.secretary_user
        
        self.assertTrue(permission.has_permission(request, None))
        self.assertFalse(permission.has_object_permission(request, None, other_patient))


class CanManagePatientAdminDataTest(BasePermissionTest):
    """Tests pour la permission CanManagePatientAdminData"""
    
    def test_admin_can_manage_admin_data(self):
        """Test qu'un administrateur peut gérer les données administratives"""
        permission = CanManagePatientAdminData()
        request = Mock()
        request.user = self.admin_user
        
        self.assertTrue(permission.has_permission(request, None))
    
    def test_doctor_can_manage_admin_data(self):
        """Test qu'un médecin peut gérer les données administratives"""
        permission = CanManagePatientAdminData()
        request = Mock()
        request.user = self.doctor_user
        
        self.assertTrue(permission.has_permission(request, None))
    
    def test_secretary_can_manage_admin_data(self):
        """Test qu'un secrétaire peut gérer les données administratives"""
        permission = CanManagePatientAdminData()
        request = Mock()
        request.user = self.secretary_user
        
        self.assertTrue(permission.has_permission(request, None))
    
    def test_nurse_cannot_manage_admin_data(self):
        """Test qu'un infirmier ne peut pas gérer les données administratives"""
        permission = CanManagePatientAdminData()
        request = Mock()
        request.user = self.nurse_user
        
        self.assertFalse(permission.has_permission(request, None))


class CanManagePatientMedicalDataTest(BasePermissionTest):
    """Tests pour la permission CanManagePatientMedicalData"""
    
    def test_admin_can_manage_medical_data(self):
        """Test qu'un administrateur peut gérer les données médicales"""
        permission = CanManagePatientMedicalData()
        request = Mock()
        request.user = self.admin_user
        
        self.assertTrue(permission.has_permission(request, None))
    
    def test_doctor_can_manage_medical_data(self):
        """Test qu'un médecin peut gérer les données médicales"""
        permission = CanManagePatientMedicalData()
        request = Mock()
        request.user = self.doctor_user
        
        self.assertTrue(permission.has_permission(request, None))
    
    def test_secretary_cannot_manage_medical_data(self):
        """Test qu'un secrétaire ne peut pas gérer les données médicales"""
        permission = CanManagePatientMedicalData()
        request = Mock()
        request.user = self.secretary_user
        
        self.assertFalse(permission.has_permission(request, None))
    
    def test_nurse_cannot_manage_medical_data(self):
        """Test qu'un infirmier ne peut pas gérer les données médicales"""
        permission = CanManagePatientMedicalData()
        request = Mock()
        request.user = self.nurse_user
        
        self.assertFalse(permission.has_permission(request, None))


class PermissionDecoratorTest(BasePermissionTest):
    """Tests pour les décorateurs de permission"""
    
    def test_permission_required_with_valid_permission(self):
        """Test le décorateur permission_required avec une permission valide"""
        @permission_required([IsAuthenticated])
        def test_view(request):
            return "success"
        
        request = Mock()
        request.user = self.doctor_user
        
        result = test_view(request)
        self.assertEqual(result, "success")
    
    def test_permission_required_with_invalid_permission(self):
        """Test le décorateur permission_required avec une permission invalide"""
        @permission_required([IsAuthenticated])
        def test_view(request):
            return "success"
        
        request = Mock()
        request.user = self.anonymous_user
        
        with self.assertRaises(PermissionDenied):
            test_view(request)
    
    def test_object_permission_required_with_valid_permission(self):
        """Test le décorateur object_permission_required avec une permission valide"""
        @object_permission_required([CanAccessPatient])
        def test_view(request, patient_id):
            return "success"
        
        request = Mock()
        request.user = self.admin_user
        
        result = test_view(request, self.patient.id)
        self.assertEqual(result, "success")
    
    def test_object_permission_required_with_invalid_permission(self):
        """Test le décorateur object_permission_required avec une permission invalide"""
        @object_permission_required([CanAccessPatient])
        def test_view(request, patient_id):
            return "success"
        
        # Créer un patient dans un autre centre
        other_centre = Centre.objects.create(
            name="Autre Hôpital",
            address="456 Autre Rue, 69000 Lyon",
            phone="0987654321"
        )
        other_patient = Patient.objects.create(
            first_name="Marie",
            last_name="Durand",
            date_of_birth="1985-05-15",
            gender="F",
            default_centre=other_centre
        )
        
        request = Mock()
        request.user = self.secretary_user
        
        with self.assertRaises(PermissionDenied):
            test_view(request, other_patient.id)


class SpecializedPermissionTest(BasePermissionTest):
    """Tests pour les permissions spécialisées"""
    
    def test_can_access_statistics(self):
        """Test pour la permission CanAccessStatistics"""
        permission = CanAccessStatistics()
        
        # Admin peut accéder aux statistiques
        request = Mock()
        request.user = self.admin_user
        self.assertTrue(permission.has_permission(request, None))
        
        # Docteur peut accéder aux statistiques
        request.user = self.doctor_user
        self.assertTrue(permission.has_permission(request, None))
        
        # Secrétaire ne peut pas accéder aux statistiques
        request.user = self.secretary_user
        self.assertFalse(permission.has_permission(request, None))
    
    def test_can_manage_users(self):
        """Test pour la permission CanManageUsers"""
        permission = CanManageUsers()
        
        # Admin peut gérer les utilisateurs
        request = Mock()
        request.user = self.admin_user
        self.assertTrue(permission.has_permission(request, None))
        
        # Docteur ne peut pas gérer les utilisateurs
        request.user = self.doctor_user
        self.assertFalse(permission.has_permission(request, None))
    
    def test_can_manage_centres(self):
        """Test pour la permission CanManageCentres"""
        permission = CanManageCentres()
        
        # Admin peut gérer les centres
        request = Mock()
        request.user = self.admin_user
        self.assertTrue(permission.has_permission(request, None))
        
        # Docteur ne peut pas gérer les centres
        request.user = self.doctor_user
        self.assertFalse(permission.has_permission(request, None))
    
    def test_can_manage_appointments(self):
        """Test pour la permission CanManageAppointments"""
        permission = CanManageAppointments()
        
        # Admin peut gérer les rendez-vous
        request = Mock()
        request.user = self.admin_user
        self.assertTrue(permission.has_permission(request, None))
        
        # Docteur peut gérer les rendez-vous
        request.user = self.doctor_user
        self.assertTrue(permission.has_permission(request, None))
        
        # Secrétaire peut gérer les rendez-vous
        request.user = self.secretary_user
        self.assertTrue(permission.has_permission(request, None))
        
        # Infirmier ne peut pas gérer les rendez-vous
        request.user = self.nurse_user
        self.assertFalse(permission.has_permission(request, None))