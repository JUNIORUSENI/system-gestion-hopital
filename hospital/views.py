"""
Fichier principal des vues - Importe uniquement les vues de base
Les vues spécifiques sont maintenant dans des fichiers séparés
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from .models import Patient, Consultation, Hospitalisation, Emergency, Centre, Profile, Appointment
from .forms import PatientForm, ConsultationForm, HospitalisationForm, EmergencyForm, CentreForm, UserRegistrationForm, AppointmentForm
from django.contrib.auth.models import User

# Importer les fonctions de permissions depuis le module centralisé
from .permissions import (
    check_patient_access, can_access_medical_data, 
    can_manage_patient_admin_data, can_manage_patient_medical_data,
    role_required
)

# Importer les vues de base
from .views.base import (
    dashboard, custom_logout, statistics_view, doctor_dashboard,
    medical_admin_dashboard, get_patients_partial, generate_document
)

# Importer les vues des patients
from .views.patients_views import (
    patient_list, patient_detail, create_patient_form, edit_patient, 
    delete_patient, orient_patient, search_patients, print_document
)

# Importer les vues des consultations
from .views.consultations_views import (
    consultation_list, consultation_detail, consultation_create, 
    consultation_edit, consultation_delete
)

# Importer les vues des hospitalisations
from .views.hospitalisations_views import (
    hospitalisation_list, hospitalisation_detail, hospitalisation_create, 
    hospitalisation_edit, hospitalisation_delete, hospitalisation_discharge
)

# Importer les vues des urgences
from .views.emergencies_views import (
    emergency_list, emergency_detail, emergency_create, emergency_edit, 
    emergency_delete, emergency_triage
)

# Importer les vues des rendez-vous
from .views.appointments_views import (
    appointment_list, appointment_create, appointment_edit, 
    appointment_delete, appointment_toggle_status
)

# Importer les vues d'authentification
from .views.auth_views import register

# Importer les vues des utilisateurs (si elles existent)
try:
    from .views.users_views import (
        user_list, user_detail, create_user, edit_user, delete_user, 
        toggle_user_status, reset_user_password, my_profile, change_my_password, 
        search_users, get_users_partial, user_statistics
    )
except ImportError:
    pass

# Importer les vues des centres (si elles existent)
try:
    from .views.centres_views import (
        centre_list, centre_detail, create_centre, edit_centre, delete_centre, 
        centre_staff, add_staff_to_centre, remove_staff_from_centre, centre_patients, 
        centre_statistics, search_centres, get_centres_partial, centre_dashboard
    )
except ImportError:
    pass


# Vues héritées pour la compatibilité - Ces vues sont maintenant dans les fichiers séparés
# mais on les garde ici pour la compatibilité avec les templates qui pourraient les référencer directement

@login_required
def consultation_detail(request, consultation_id):
    """Vue pour le détail d'une consultation - Déléguée à consultations_views"""
    from .views.consultations_views import consultation_detail as _consultation_detail
    return _consultation_detail(request, consultation_id)


@login_required
def hospitalisation_detail(request, hospitalisation_id):
    """Vue pour le détail d'une hospitalisation - Déléguée à hospitalisations_views"""
    from .views.hospitalisations_views import hospitalisation_detail as _hospitalisation_detail
    return _hospitalisation_detail(request, hospitalisation_id)


@login_required
def emergency_detail(request, emergency_id):
    """Vue pour le détail d'une urgence - Déléguée à emergencies_views"""
    from .views.emergencies_views import emergency_detail as _emergency_detail
    return _emergency_detail(request, emergency_id)


@login_required
def appointment_detail(request, appointment_id):
    """Vue pour le détail d'un rendez-vous - Déléguée à appointments_views"""
    from .views.appointments_views import appointment_detail as _appointment_detail
    return _appointment_detail(request, appointment_id)


# Classe de connexion personnalisée pour la compatibilité
class CustomLoginView(LoginView):
    """Vue personnalisée pour la connexion d'un utilisateur"""
    template_name = 'hospital/registration/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return self.request.GET.get('next', '/')


# Fonction register pour la compatibilité
def register(request):
    """Vue pour l'inscription d'un nouvel utilisateur"""
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        
        user = User.objects.create_user(username=username, email=email, password=password, 
                                        first_name=first_name, last_name=last_name)
        login(request, user)
        messages.success(request, "Votre compte a été créé avec succès.")
        return redirect('dashboard')
    
    return render(request, 'hospital/registration/register.html')