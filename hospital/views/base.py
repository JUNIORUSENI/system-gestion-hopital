"""
Vues de base et mixins pour l'application hospital
"""
from datetime import timedelta

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
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.contrib.auth.models import User

from ..models import Patient, Consultation, Hospitalisation, Emergency, Centre, Profile, Appointment
from ..forms import PatientForm, ConsultationForm, HospitalisationForm, EmergencyForm, CentreForm, UserRegistrationForm, AppointmentForm
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
            
            # Dashboard pour ADMIN et MEDICAL_ADMIN (vue globale)
            if role in ['ADMIN', 'MEDICAL_ADMIN']:
                total_patients = Patient.objects.count()
                total_consultations = Consultation.objects.count()
                total_hospitalisations = Hospitalisation.objects.count()
                total_emergencies = Emergency.objects.count()
                total_users = User.objects.count()
                total_centres = Centre.objects.count()
                
                # Patients récents
                recent_patients = Patient.objects.all().order_by('-created_at')[:5]
                
                # Consultations récentes
                recent_consultations = Consultation.objects.all().select_related(
                    'patient', 'doctor', 'centre'
                ).order_by('-date')[:5]
                
                context = {
                    'role': role,
                    'total_patients': total_patients,
                    'total_consultations': total_consultations,
                    'total_hospitalisations': total_hospitalisations,
                    'total_emergencies': total_emergencies,
                    'total_users': total_users,
                    'total_centres': total_centres,
                    'recent_patients': recent_patients,
                    'recent_consultations': recent_consultations,
                }
            
            # Dashboard pour DOCTOR (ses propres données uniquement)
            elif role == 'DOCTOR':
                # Statistiques personnelles du médecin
                my_patients = Patient.objects.filter(
                    consultations__doctor=request.user
                ).distinct()
                
                my_consultations = Consultation.objects.filter(
                    doctor=request.user
                ).select_related('patient', 'centre').order_by('-date')[:10]
                
                my_pending_consultations = Consultation.objects.filter(
                    doctor=request.user,
                    status__in=['PENDING', 'IN_PROGRESS']
                ).select_related('patient', 'centre').order_by('-date')[:10]
                
                my_completed_consultations = Consultation.objects.filter(
                    doctor=request.user,
                    status='COMPLETED'
                ).select_related('patient', 'centre').order_by('-date')[:10]
                
                my_hospitalisations = Hospitalisation.objects.filter(
                    doctor=request.user
                ).select_related('patient', 'centre').order_by('-admission_date')[:10]
                
                # Hospitalisations actives
                active_hospitalisations = Hospitalisation.objects.filter(
                    doctor=request.user,
                    discharge_date__isnull=True
                ).select_related('patient', 'centre').order_by('-admission_date')[:5]
                
                my_emergencies = Emergency.objects.filter(
                    doctor=request.user
                ).select_related('patient', 'centre').order_by('-admission_time')[:10]
                
                # Urgences non orientées
                pending_emergencies = Emergency.objects.filter(
                    doctor=request.user,
                    orientation__isnull=True
                ).select_related('patient', 'centre').order_by('-admission_time')[:5]
                
                # Rendez-vous à venir
                my_appointments = Appointment.objects.filter(
                    doctor=request.user,
                    date__gte=timezone.now()
                ).exclude(
                    status__in=['COMPLETED', 'CANCELLED']
                ).select_related('patient', 'centre').order_by('date')[:5]
                
                # Statistiques globales
                total_my_patients = my_patients.count()
                total_my_consultations = Consultation.objects.filter(doctor=request.user).count()
                total_my_hospitalisations = Hospitalisation.objects.filter(doctor=request.user).count()
                total_my_emergencies = Emergency.objects.filter(doctor=request.user).count()
                total_pending_consultations = my_pending_consultations.count()
                total_active_hospitalisations = active_hospitalisations.count()
                
                context = {
                    'role': role,
                    'my_patients': my_patients[:5],
                    'my_consultations': my_consultations,
                    'my_pending_consultations': my_pending_consultations,
                    'my_completed_consultations': my_completed_consultations,
                    'my_hospitalisations': my_hospitalisations,
                    'active_hospitalisations': active_hospitalisations,
                    'my_emergencies': my_emergencies,
                    'pending_emergencies': pending_emergencies,
                    'my_appointments': my_appointments,
                    # Statistiques
                    'total_my_patients': total_my_patients,
                    'total_my_consultations': total_my_consultations,
                    'total_my_hospitalisations': total_my_hospitalisations,
                    'total_my_emergencies': total_my_emergencies,
                    'total_pending_consultations': total_pending_consultations,
                    'total_active_hospitalisations': total_active_hospitalisations,
                }
            # Dashboard pour SECRETARY
            elif role == 'SECRETARY':
                # Centres assignés
                my_centres = request.user.profile.centres.all()
                
                # Patients de ses centres
                my_patients = Patient.objects.filter(
                    default_centre__in=my_centres
                ).select_related('default_centre').order_by('-created_at')
                
                # Consultations récentes dans ses centres
                recent_consultations = Consultation.objects.filter(
                    centre__in=my_centres
                ).select_related('patient', 'doctor', 'centre').order_by('-date')[:10]
                
                # Hospitalisations actives dans ses centres
                recent_hospitalisations = Hospitalisation.objects.filter(
                    centre__in=my_centres
                ).select_related('patient', 'doctor', 'centre').order_by('-admission_date')[:10]
                
                # Statistiques
                total_patients_in_centres = my_patients.count()
                active_hospitalisations = recent_hospitalisations.filter(discharge_date__isnull=True).count()
                
                context = {
                    'role': role,
                    'my_patients': my_patients[:5],
                    'total_patients_in_centres': total_patients_in_centres,
                    'recent_consultations': recent_consultations,
                    'recent_hospitalisations': recent_hospitalisations,
                    'active_hospitalisations': active_hospitalisations,
                    'my_centres': my_centres,
                }
            
            # Dashboard pour NURSE
            elif role == 'NURSE':
                # Centres assignés
                my_centres = request.user.profile.centres.all()
                
                # Patients hospitalisés dans ses centres
                patients_in_my_centres = Hospitalisation.objects.filter(
                    centre__in=my_centres,
                    discharge_date__isnull=True  # Seulement les hospitalisations actives
                ).select_related('patient', 'doctor', 'centre').order_by('-admission_date')
                
                # Urgences récentes dans ses centres
                recent_emergencies = Emergency.objects.filter(
                    centre__in=my_centres
                ).select_related('patient', 'doctor', 'centre').order_by('-admission_time')[:10]
                
                # Statistiques
                total_active_hospitalisations = patients_in_my_centres.count()
                critical_emergencies = recent_emergencies.filter(triage_level='CRITICAL').count()
                
                context = {
                    'role': role,
                    'patients_in_my_centres': patients_in_my_centres[:10],
                    'recent_emergencies': recent_emergencies,
                    'total_active_hospitalisations': total_active_hospitalisations,
                    'critical_emergencies': critical_emergencies,
                    'my_centres': my_centres,
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
            'user': request.user,
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
            'user': request.user,
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
            'user': request.user,
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
    """Vue du dashboard personnel du médecin avec informations détaillées"""
    if request.user.profile.role not in ['DOCTOR', 'MEDICAL_ADMIN']:
        raise PermissionDenied("Accès réservé aux médecins")
    
    # Récupérer les consultations du médecin
    my_consultations = Consultation.objects.filter(
        doctor=request.user
    ).select_related('patient', 'centre').order_by('-date')
    
    pending_consultations = my_consultations.filter(status__in=['PENDING', 'IN_PROGRESS'])
    completed_consultations = my_consultations.filter(status='COMPLETED')
    
    # Récupérer les hospitalisations du médecin
    my_hospitalisations = Hospitalisation.objects.filter(
        doctor=request.user
    ).select_related('patient', 'centre').order_by('-admission_date')
    
    active_hospitalisations = my_hospitalisations.filter(discharge_date__isnull=True)
    
    # Récupérer les urgences du médecin
    my_emergencies = Emergency.objects.filter(
        doctor=request.user
    ).select_related('patient', 'centre').order_by('-admission_time')
    
    pending_emergencies = my_emergencies.filter(orientation__isnull=True)
    
    # Récupérer les rendez-vous du médecin
    my_appointments = Appointment.objects.filter(
        doctor=request.user
    ).select_related('patient', 'centre').order_by('date')
    
    upcoming_appointments = my_appointments.filter(
        date__gte=timezone.now(),
        status__in=['SCHEDULED', 'CONFIRMED']
    )
    
    past_appointments = my_appointments.filter(date__lt=timezone.now())
    
    # Statistiques
    total_patients = Patient.objects.filter(
        consultations__doctor=request.user
    ).distinct().count()
    
    total_consultations = my_consultations.count()
    total_hospitalisations = my_hospitalisations.count()
    total_emergencies = my_emergencies.count()
    total_appointments = my_appointments.count()
    
    context = {
        'role': request.user.profile.role,
        'pending_consultations': pending_consultations[:10],
        'completed_consultations': completed_consultations[:10],
        'my_consultations': my_consultations[:10],
        'my_hospitalisations': my_hospitalisations[:10],
        'active_hospitalisations': active_hospitalisations,
        'my_emergencies': my_emergencies[:10],
        'pending_emergencies': pending_emergencies,
        'upcoming_appointments': upcoming_appointments[:10],
        'past_appointments': past_appointments[:10],
        'total_patients': total_patients,
        'total_consultations': total_consultations,
        'total_hospitalisations': total_hospitalisations,
        'total_emergencies': total_emergencies,
        'total_appointments': total_appointments,
        'total_pending_consultations': pending_consultations.count(),
        'total_active_hospitalisations': active_hospitalisations.count(),
        'total_pending_emergencies': pending_emergencies.count(),
        'total_upcoming_appointments': upcoming_appointments.count(),
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
    """Vue pour la page des statistiques - Réservée au MEDICAL_ADMIN"""
    # Vérifier que l'utilisateur est MEDICAL_ADMIN
    if request.user.profile.role not in ['MEDICAL_ADMIN']:
        raise PermissionDenied("Cette page est réservée au Médecin Administrateur")
    
    # Statistiques globales pour MEDICAL_ADMIN uniquement
    base_patients = Patient.objects.all()
    base_consultations = Consultation.objects.all()
    base_hospitalisations = Hospitalisation.objects.all()
    base_emergencies = Emergency.objects.all()
    base_appointments = Appointment.objects.all()
    
    # Calculer les totaux
    total_patients = base_patients.count()
    total_consultations = base_consultations.count()
    total_hospitalisations = base_hospitalisations.count()
    total_emergencies = base_emergencies.count()
    total_appointments = base_appointments.count()
    total_users = User.objects.count()
    total_centres = Centre.objects.count()
    
    # Statistiques du personnel
    total_doctors = User.objects.filter(profile__role='DOCTOR').count()
    total_nurses = User.objects.filter(profile__role='NURSE').count()
    total_secretaries = User.objects.filter(profile__role='SECRETARY').count()
    
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
    
    # Top médecins par consultations
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
    doctors_with_consultations.sort(key=lambda x: x['count'], reverse=True)
    top_doctors = doctors_with_consultations[:10]
    
    # Rendez-vous par statut
    appointments_by_status = {}
    for status in ['SCHEDULED', 'CONFIRMED', 'COMPLETED', 'CANCELLED']:
        appointments_by_status[status] = Appointment.objects.filter(status=status).count()
    
    context = {
        'total_patients': total_patients,
        'total_consultations': total_consultations,
        'total_hospitalisations': total_hospitalisations,
        'total_emergencies': total_emergencies,
        'total_appointments': total_appointments,
        'total_users': total_users,
        'total_centres': total_centres,
        'total_doctors': total_doctors,
        'total_nurses': total_nurses,
        'total_secretaries': total_secretaries,
        'active_hospitalisations': active_hospitalisations,
        'consultations_by_status': consultations_by_status,
        'consultations_by_centre': consultations_by_centre,
        'emergencies_by_level': emergencies_by_level,
        'emergency_orientations': emergency_orientations,
        'patients_by_gender': patients_by_gender,
        'hospitalisations_by_service': hospitalisations_by_service,
        'consultations_last_6_months': consultations_last_6_months,
        'appointments_by_status': appointments_by_status,
        'top_doctors': top_doctors,
        'user_role': request.user.profile.role,
    }
    
    return render(request, 'hospital/statistics.html', context)


@login_required
def doctor_my_consultations(request):
    """Vue dédiée pour toutes les consultations du médecin"""
    if request.user.profile.role not in ['DOCTOR', 'MEDICAL_ADMIN']:
        raise PermissionDenied("Accès réservé aux médecins")
    
    from django.core.paginator import Paginator
    
    # Récupérer les paramètres
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    page = request.GET.get('page', 1)
    
    # Récupérer les consultations du médecin
    consultations = Consultation.objects.filter(doctor=request.user)
    
    # Appliquer la recherche
    if search_query:
        consultations = consultations.filter(
            Q(id__icontains=search_query) |
            Q(patient__first_name__icontains=search_query) |
            Q(patient__last_name__icontains=search_query) |
            Q(patient__postname__icontains=search_query)
        )
    
    # Filtre par statut
    if status_filter:
        consultations = consultations.filter(status=status_filter)
    
    # Optimiser
    consultations = consultations.select_related('patient', 'centre').order_by('-date')
    
    # Pagination
    paginator = Paginator(consultations, 25)
    page_obj = paginator.get_page(page)
    
    return render(request, 'hospital/doctors/my_consultations.html', {
        'consultations': page_obj,
        'page_obj': page_obj,
        'current_search': search_query,
        'current_status': status_filter,
        'total_count': paginator.count,
    })


@login_required
def doctor_my_hospitalisations(request):
    """Vue dédiée pour toutes les hospitalisations du médecin"""
    if request.user.profile.role not in ['DOCTOR', 'MEDICAL_ADMIN']:
        raise PermissionDenied("Accès réservé aux médecins")
    
    from django.core.paginator import Paginator
    
    # Récupérer les paramètres
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    page = request.GET.get('page', 1)
    
    # Récupérer les hospitalisations du médecin
    hospitalisations = Hospitalisation.objects.filter(doctor=request.user)
    
    # Appliquer la recherche
    if search_query:
        hospitalisations = hospitalisations.filter(
            Q(id__icontains=search_query) |
            Q(patient__first_name__icontains=search_query) |
            Q(patient__last_name__icontains=search_query) |
            Q(patient__postname__icontains=search_query) |
            Q(service__icontains=search_query)
        )
    
    # Filtre par statut
    if status_filter == 'active':
        hospitalisations = hospitalisations.filter(discharge_date__isnull=True)
    elif status_filter == 'discharged':
        hospitalisations = hospitalisations.filter(discharge_date__isnull=False)
    
    # Optimiser
    hospitalisations = hospitalisations.select_related('patient', 'centre').order_by('-admission_date')
    
    # Pagination
    paginator = Paginator(hospitalisations, 25)
    page_obj = paginator.get_page(page)
    
    return render(request, 'hospital/doctors/my_hospitalisations.html', {
        'hospitalisations': page_obj,
        'page_obj': page_obj,
        'current_search': search_query,
        'current_status': status_filter,
        'total_count': paginator.count,
    })


@login_required
def doctor_my_emergencies(request):
    """Vue dédiée pour toutes les urgences du médecin"""
    if request.user.profile.role not in ['DOCTOR', 'MEDICAL_ADMIN']:
        raise PermissionDenied("Accès réservé aux médecins")
    
    from django.core.paginator import Paginator
    
    # Récupérer les paramètres
    search_query = request.GET.get('q', '').strip()
    triage_filter = request.GET.get('triage', '').strip()
    page = request.GET.get('page', 1)
    
    # Récupérer les urgences du médecin
    emergencies = Emergency.objects.filter(doctor=request.user)
    
    # Appliquer la recherche
    if search_query:
        emergencies = emergencies.filter(
            Q(id__icontains=search_query) |
            Q(patient__first_name__icontains=search_query) |
            Q(patient__last_name__icontains=search_query) |
            Q(patient__postname__icontains=search_query)
        )
    
    # Filtre par triage
    if triage_filter:
        emergencies = emergencies.filter(triage_level=triage_filter)
    
    # Optimiser
    emergencies = emergencies.select_related('patient', 'centre').order_by('-admission_time')
    
    # Pagination
    paginator = Paginator(emergencies, 25)
    page_obj = paginator.get_page(page)
    
    return render(request, 'hospital/doctors/my_emergencies.html', {
        'emergencies': page_obj,
        'page_obj': page_obj,
        'current_search': search_query,
        'current_triage': triage_filter,
        'total_count': paginator.count,
    })


@login_required
def doctor_my_patients(request):
    """Vue dédiée pour tous les patients du médecin"""
    if request.user.profile.role not in ['DOCTOR', 'MEDICAL_ADMIN']:
        raise PermissionDenied("Accès réservé aux médecins")
    
    from django.core.paginator import Paginator
    
    # Récupérer les paramètres
    search_query = request.GET.get('q', '').strip()
    page = request.GET.get('page', 1)
    
    # Récupérer les patients du médecin (via consultations)
    patients = Patient.objects.filter(
        consultations__doctor=request.user
    ).distinct()
    
    # Appliquer la recherche
    if search_query:
        patients = patients.filter(
            Q(id__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(postname__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Optimiser
    patients = patients.select_related('default_centre').order_by('last_name', 'first_name')
    
    # Pagination
    paginator = Paginator(patients, 25)
    page_obj = paginator.get_page(page)
    
    return render(request, 'hospital/doctors/my_patients.html', {
        'patients': page_obj,
        'page_obj': page_obj,
        'current_search': search_query,
        'total_count': paginator.count,
    })