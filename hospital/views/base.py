"""
Vues de base et mixins pour l'application hospital
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from datetime import timedelta
from django.db.models import Count
from ..models import Patient, Consultation, Hospitalisation, Emergency, Centre, Profile, Appointment
from ..forms import PatientForm, ConsultationForm, HospitalisationForm, EmergencyForm, CentreForm, UserRegistrationForm, AppointmentForm
from django.contrib.auth.models import User
from ..permissions import check_patient_access, can_access_medical_data, can_manage_patient_admin_data, can_manage_patient_medical_data


class RoleRequiredMixin(UserPassesTestMixin):
    """Mixin pour vérifier le rôle de l'utilisateur"""
    allowed_roles = []
    
    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        
        if not hasattr(self.request.user, 'profile'):
            return False
        
        return self.request.user.profile.role in self.allowed_roles
    
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
        return super().handle_no_permission()


# Pas besoin de redéfinir LoginRequiredMixin, on utilise celui de Django


def custom_logout(request):
    """Vue personnalisée pour la déconnexion"""
    logout(request)
    return redirect('dashboard')  # Redirige vers la page d'accueil après déconnexion


def dashboard(request):
    """Vue du dashboard principal"""
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile'):
            role = request.user.profile.role
            if role in ['ADMIN', 'MEDICAL_ADMIN']:
                # Statistiques pour l'administrateur et le médecin administrateur
                total_patients = Patient.objects.count()
                total_consultations = Consultation.objects.count()
                total_hospitalisations = Hospitalisation.objects.count()
                total_emergencies = Emergency.objects.count()
                total_users = User.objects.count()
                total_centres = Centre.objects.count()
                
                context = {
                    'role': role,
                    'total_patients': total_patients,
                    'total_consultations': total_consultations,
                    'total_hospitalisations': total_hospitalisations,
                    'total_emergencies': total_emergencies,
                    'total_users': total_users,
                    'total_centres': total_centres,
                }
            elif role in ['DOCTOR', 'MEDICAL_ADMIN']:
                # Données spécifiques au médecin - maintenant avec accès à tous les patients
                my_consultations = Consultation.objects.all().order_by('-date')[:10]
                my_pending_consultations = Consultation.objects.filter(
                    status__in=['PENDING', 'IN_PROGRESS']
                ).order_by('-date')[:10]
                my_completed_consultations = Consultation.objects.filter(
                    status='COMPLETED'
                ).order_by('-date')[:10]
                my_hospitalisations = Hospitalisation.objects.all().order_by('-admission_date')[:10]
                my_emergencies = Emergency.objects.all().order_by('-admission_time')[:10]
                
                # Récupérer les rendez-vous à venir seulement pour ce médecin
                my_appointments = Appointment.objects.filter(
                    doctor=request.user,
                    date__gte=timezone.now()
                ).exclude(
                    status__in=['COMPLETED', 'CANCELLED']
                ).order_by('date')[:5]
                
                context = {
                    'role': role,
                    'my_consultations': my_consultations,
                    'my_pending_consultations': my_pending_consultations,
                    'my_completed_consultations': my_completed_consultations,
                    'my_hospitalisations': my_hospitalisations,
                    'my_emergencies': my_emergencies,
                    'my_appointments': my_appointments,
                }
            elif role == 'SECRETARY':
                # Données spécifiques au secrétaire
                my_patients = Patient.objects.filter(default_centre__in=request.user.profile.centres.all())
                recent_consultations = Consultation.objects.filter(
                    patient__default_centre__in=request.user.profile.centres.all()
                ).order_by('-date')[:10]
                recent_hospitalisations = Hospitalisation.objects.filter(
                    centre__in=request.user.profile.centres.all()
                ).order_by('-admission_date')[:10]
                
                context = {
                    'role': role,
                    'my_patients': my_patients,
                    'recent_consultations': recent_consultations,
                    'recent_hospitalisations': recent_hospitalisations,
                }
            elif role == 'NURSE':
                # Données spécifiques à l'infirmier
                patients_in_my_centres = Hospitalisation.objects.filter(
                    centre__in=request.user.profile.centres.all()
                ).select_related('patient')
                
                context = {
                    'role': role,
                    'patients_in_my_centres': patients_in_my_centres,
                }
            else:
                context = {'role': 'VISITOR'}
        else:
            context = {'role': 'NO_PROFILE'}
        
        return render(request, 'hospital/dashboard.html', context)
    else:
        return render(request, 'hospital/welcome.html')


def get_patients_partial(request):
    """Vue partielle pour la liste des patients via HTMX"""
    patients = Patient.objects.all()
    html = render_to_string('hospital/partials/patients_list.html', {'patients': patients})
    return JsonResponse({'html': html})


def generate_document(request, patient_id, doc_type):
    """Vue pour générer différents types de documents médicaux"""
    from ..models import Patient
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Vérifier si l'utilisateur a le droit d'accéder à ce patient
    if not check_patient_access(request.user, patient):
        raise PermissionDenied("Vous n'avez pas accès à ce patient")
    
    # Seuls les médecins peuvent générer des documents médicaux
    if not can_manage_patient_medical_data(request.user):
        raise PermissionDenied("Seuls les médecins peuvent générer des documents médicaux")
    
    # Selon le type de document demandé
    if doc_type == 'prescription':
        # Récupérer la dernière consultation pour une prescription de suivi
        last_consultation = patient.consultations.last()
        context = {
            'patient': patient,
            'consultation': last_consultation,
            'doctor': request.user,
            'title': 'Ordonnance'
        }
        return render(request, 'hospital/documents/prescription.html', context)
    
    elif doc_type == 'medical_report':
        # Générer un rapport médical basé sur l'historique du patient
        consultations = patient.consultations.all()
        hospitalisations = patient.hospitalisations.all()
        emergencies = patient.emergencies.all()
        
        context = {
            'patient': patient,
            'consultations': consultations,
            'hospitalisations': hospitalisations,
            'emergencies': emergencies,
            'doctor': request.user,
            'title': 'Rapport Médical'
        }
        return render(request, 'hospital/documents/medical_report.html', context)
    
    elif doc_type == 'discharge_summary':
        # Récupérer la dernière hospitalisation pour le résumé de sortie
        last_hospitalisation = patient.hospitalisations.order_by('-admission_date').first()
        if not last_hospitalisation or not last_hospitalisation.discharge_summary:
            messages.error(request, "Aucun résumé de sortie disponible pour ce patient.")
            return redirect('patient_detail', patient_id=patient.id)
        
        context = {
            'patient': patient,
            'hospitalisation': last_hospitalisation,
            'doctor': request.user,
            'title': 'Compte-rendu de Sortie'
        }
        return render(request, 'hospital/documents/discharge_summary.html', context)
    
    else:
        messages.error(request, "Type de document non supporté.")
        return redirect('patient_detail', patient_id=patient.id)


def print_document(request, patient_id, doc_type):
    """Vue pour imprimer ou exporter les documents"""
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Vérifier si l'utilisateur a le droit d'accéder à ce patient
    if not check_patient_access(request.user, patient):
        raise PermissionDenied("Vous n'avez pas accès à ce patient")
    
    # Seuls les médecins peuvent imprimer ou exporter des documents médicaux
    if not can_manage_patient_medical_data(request.user):
        raise PermissionDenied("Seuls les médecins peuvent imprimer des documents médicaux")
    
    # Appeler la fonction de génération de document
    response = generate_document(request, patient_id, doc_type)
    return response


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


class CustomLoginView(LoginView):
    """Vue personnalisée pour la connexion d'un utilisateur"""
    template_name = 'hospital/registration/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return self.request.GET.get('next', '/')


@login_required
def doctor_dashboard(request):
    """Vue du dashboard personnel du médecin"""
    if request.user.profile.role != 'DOCTOR':
        raise PermissionDenied("Accès réservé aux médecins")
    
    # Récupérer les consultations du médecin
    my_consultations = Consultation.objects.filter(doctor=request.user).order_by('-date')
    pending_consultations = my_consultations.filter(status='PENDING')
    completed_consultations = my_consultations.filter(status='COMPLETED')
    
    # Récupérer les rendez-vous du médecin
    my_appointments = Appointment.objects.filter(doctor=request.user).order_by('date')
    upcoming_appointments = my_appointments.filter(date__gte=timezone.now(), status__in=['SCHEDULED', 'CONFIRMED'])
    past_appointments = my_appointments.filter(date__lt=timezone.now())
    
    # Statistiques
    total_patients = Patient.objects.filter(
        consultations__doctor=request.user
    ).distinct().count()
    
    context = {
        'role': 'DOCTOR',
        'pending_consultations': pending_consultations,
        'completed_consultations': completed_consultations,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'total_patients': total_patients,
    }
    
    return render(request, 'hospital/doctors/dashboard.html', context)


@login_required
def medical_admin_dashboard(request):
    """Dashboard détaillé pour le Médecin Administrateur"""
    # Vérifier que l'utilisateur a le bon rôle
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'MEDICAL_ADMIN':
        raise PermissionDenied("Accès réservé au Médecin Administrateur")
    
    # Statistiques générales de l'hôpital
    total_patients = Patient.objects.count()
    total_consultations = Consultation.objects.count()
    total_hospitalisations = Hospitalisation.objects.count()
    total_emergencies = Emergency.objects.count()
    total_appointments = Appointment.objects.count()
    total_doctors = User.objects.filter(profile__role='DOCTOR').count()
    total_nurses = User.objects.filter(profile__role='NURSE').count()
    total_secretaries = User.objects.filter(profile__role='SECRETARY').count()
    total_centres = Centre.objects.count()
    
    # Consultations par statut
    consultations_by_status = {}
    for status in ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']:
        consultations_by_status[status] = Consultation.objects.filter(status=status).count()
    
    # Hospitalisations actives
    active_hospitalisations = Hospitalisation.objects.filter(discharge_date__isnull=True).count()
    
    # Urgences par niveau
    emergencies_by_level = {}
    for level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
        emergencies_by_level[level] = Emergency.objects.filter(triage_level=level).count()
    
    # Rendez-vous par statut
    appointments_by_status = {}
    for status in ['SCHEDULED', 'CONFIRMED', 'COMPLETED', 'CANCELLED']:
        appointments_by_status[status] = Appointment.objects.filter(status=status).count()
    
    # Consultations par médecin (top 10)
    doctors_with_consultations = []
    doctors = User.objects.filter(profile__role='DOCTOR')
    for doctor in doctors:
        consultation_count = Consultation.objects.filter(doctor=doctor).count()
        if consultation_count > 0:
            doctors_with_consultations.append({
                'doctor': doctor,
                'count': consultation_count,
                'full_name': doctor.get_full_name() or doctor.username
            })
    
    # Trier par nombre de consultations
    doctors_with_consultations.sort(key=lambda x: x['count'], reverse=True)
    top_doctors = doctors_with_consultations[:10]
    
    # Hospitalisations par service
    hospitalisations_by_service = []
    services = Hospitalisation.objects.values('service').distinct()
    for service_obj in services:
        service = service_obj['service']
        if service:  # Ne pas inclure les services vides
            count = Hospitalisation.objects.filter(service=service).count()
            hospitalisations_by_service.append({
                'service': service,
                'count': count
            })
    
    # Trier par nombre d'hospitalisations
    hospitalisations_by_service.sort(key=lambda x: x['count'], reverse=True)
    top_services = hospitalisations_by_service[:10]
    
    # Consultations des 7 derniers jours
    weekly_consultations = []
    for i in range(7):
        date = timezone.now() - timedelta(days=6-i)
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        count = Consultation.objects.filter(
            date__gte=start_of_day,
            date__lt=end_of_day
        ).count()
        
        weekly_consultations.append({
            'date': start_of_day.strftime('%d/%m'),
            'count': count,
            'day_name': start_of_day.strftime('%A')
        })
    
    # Consultations des 4 dernières semaines
    monthly_consultations = []
    for i in range(4):
        # Calculer le début et la fin du mois
        first_day = timezone.now().replace(day=1) - timedelta(days=30*i)
        # Obtenir le dernier jour du mois
        if first_day.month == 12:
            last_day = first_day.replace(year=first_day.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            last_day = first_day.replace(month=first_day.month + 1, day=1) - timedelta(days=1)
        
        count = Consultation.objects.filter(
            date__gte=first_day,
            date__lt=last_day + timedelta(days=1)
        ).count()
        
        monthly_consultations.append({
            'month': first_day.strftime('%m/%Y'),
            'count': count
        })
    
    context = {
        'role': 'MEDICAL_ADMIN',
        'total_patients': total_patients,
        'total_consultations': total_consultations,
        'total_hospitalisations': total_hospitalisations,
        'total_emergencies': total_emergencies,
        'total_appointments': total_appointments,
        'total_doctors': total_doctors,
        'total_nurses': total_nurses,
        'total_secretaries': total_secretaries,
        'total_centres': total_centres,
        'consultations_by_status': consultations_by_status,
        'active_hospitalisations': active_hospitalisations,
        'emergencies_by_level': emergencies_by_level,
        'appointments_by_status': appointments_by_status,
        'top_doctors': top_doctors,
        'top_services': top_services,
        'weekly_consultations': weekly_consultations,
        'monthly_consultations': monthly_consultations,
    }
    
    return render(request, 'hospital/medical_admin/dashboard.html', context)


@login_required
def statistics_view(request):
    """Vue pour la page des statistiques"""
    # Initialiser les variables
    total_patients = 0
    total_consultations = 0
    total_hospitalisations = 0
    total_emergencies = 0
    total_appointments = 0
    total_users = 0
    total_centres = 0
    
    # Définir les bases de données selon le rôle
    if request.user.profile.role in ['ADMIN', 'MEDICAL_ADMIN']:
        # Administrateur et Médecin Administrateur: accès à toutes les données
        base_patients = Patient.objects.all()
        base_consultations = Consultation.objects.all()
        base_hospitalisations = Hospitalisation.objects.all()
        base_emergencies = Emergency.objects.all()
        base_appointments = Appointment.objects.all()
        total_users = User.objects.count()
        total_centres = Centre.objects.count()
    elif request.user.profile.role == 'DOCTOR':
        # Médecin: statistiques liées à ses activités
        base_patients = Patient.objects.filter(consultations__doctor=request.user).distinct()
        base_consultations = Consultation.objects.filter(doctor=request.user)
        base_hospitalisations = Hospitalisation.objects.filter(doctor=request.user)
        base_emergencies = Emergency.objects.filter(doctor=request.user)
        base_appointments = Appointment.objects.filter(doctor=request.user)
    
    # Calculer les totaux
    total_patients = base_patients.count()
    total_consultations = base_consultations.count()
    total_hospitalisations = base_hospitalisations.count()
    total_emergencies = base_emergencies.count()
    total_appointments = base_appointments.count()
    
    # Calculer des statistiques supplémentaires
    # Consultations par statut
    consultations_by_status = {}
    for status in ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']:
        consultations_by_status[status] = base_consultations.filter(status=status).count()
    
    # Hospitalisations actives
    active_hospitalisations = base_hospitalisations.filter(discharge_date__isnull=True).count()
    
    # Urgences par niveau
    emergencies_by_level = {}
    for level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
        emergencies_by_level[level] = base_emergencies.filter(triage_level=level).count()
    
    # Orientations des urgences
    emergency_orientations = {}
    for orientation in ['DISCHARGED', 'HOSPITALISED', 'TRANSFERRED']:
        emergency_orientations[orientation] = base_emergencies.filter(orientation=orientation).count()
    
    # Patients par genre
    patients_by_gender = {}
    patients_by_gender['M'] = base_patients.filter(gender='M').count()
    patients_by_gender['F'] = base_patients.filter(gender='F').count()
    
    # Hospitalisations par service
    hospitalisations_by_service = list(
        base_hospitalisations
        .exclude(service__isnull=True)
        .exclude(service__exact='')
        .values('service')
        .annotate(count=Count('service'))
        .order_by('-count')
    )
    
    # Taux de consultation par centre
    consultations_by_centre = []
    if request.user.profile.role in ['ADMIN', 'MEDICAL_ADMIN']:
        for centre in Centre.objects.all():
            consultation_count = Consultation.objects.filter(centre=centre).count()
            if consultation_count > 0:
                consultations_by_centre.append({
                    'centre': centre.name,
                    'count': consultation_count
                })
    else:
        for centre in request.user.profile.centres.all():
            consultation_count = Consultation.objects.filter(
                doctor=request.user, centre=centre
            ).count()
            if consultation_count > 0:
                consultations_by_centre.append({
                    'centre': centre.name,
                    'count': consultation_count
                })
    
    # Consultations des 6 derniers mois
    consultations_last_6_months = []
    for i in range(6):
        date = timezone.now() - timedelta(days=i*30)
        month_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        count = base_consultations.filter(
            date__gte=month_start,
            date__lt=month_end
        ).count()
        consultations_last_6_months.append({
            'month': month_start.strftime('%b %Y'),
            'count': count
        })
    consultations_last_6_months.reverse()
    
    context = {
        'total_patients': total_patients,
        'total_consultations': total_consultations,
        'total_hospitalisations': total_hospitalisations,
        'total_emergencies': total_emergencies,
        'total_appointments': total_appointments,
        'total_users': total_users,
        'total_centres': total_centres,
        'active_hospitalisations': active_hospitalisations,
        'consultations_by_status': consultations_by_status,
        'consultations_by_centre': consultations_by_centre,
        'emergencies_by_level': emergencies_by_level,
        'emergency_orientations': emergency_orientations,
        'patients_by_gender': patients_by_gender,
        'hospitalisations_by_service': hospitalisations_by_service,
        'consultations_last_6_months': consultations_last_6_months,
        'user_role': request.user.profile.role,
    }
    
    return render(request, 'hospital/statistics.html', context)