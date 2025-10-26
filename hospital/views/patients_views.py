"""
Vues pour la gestion des patients
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q

from ..models import Patient, Centre
from ..forms import PatientForm
from ..services.patient_service import PatientService
from ..permissions import (
    CanAccessPatient, CanManagePatientAdminData, CanManagePatientMedicalData,
    permission_required, object_permission_required
)
from .base import RoleRequiredMixin


@login_required
def patient_list(request):
    """Vue pour la liste des patients avec pagination et filtres côté serveur"""
    # Récupérer les paramètres de filtrage
    search_query = request.GET.get('q', '').strip()
    centre_id = request.GET.get('centre', '').strip()
    is_subscriber = request.GET.get('subscriber', '').strip()
    gender = request.GET.get('gender', '').strip()
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 25)
    
    # Récupérer les patients selon les permissions
    if request.user.profile.role in ['ADMIN', 'MEDICAL_ADMIN']:
        patients = Patient.objects.all()
    elif request.user.profile.role == 'DOCTOR':
        # Les médecins voient tous les patients
        patients = Patient.objects.all()
    elif request.user.profile.role == 'SECRETARY':
        patients = Patient.objects.filter(
            default_centre__in=request.user.profile.centres.all()
        )
    elif request.user.profile.role == 'NURSE':
        # Les infirmiers voient les patients hospitalisés dans leurs centres
        from ..models import Hospitalisation
        patient_ids = Hospitalisation.objects.filter(
            centre__in=request.user.profile.centres.all()
        ).values_list('patient_id', flat=True).distinct()
        patients = Patient.objects.filter(id__in=patient_ids)
    else:
        patients = Patient.objects.none()
    
    # Appliquer les filtres de recherche
    if search_query:
        patients = patients.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(postname__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(id__icontains=search_query)
        )
    
    # Filtre par centre
    if centre_id:
        try:
            patients = patients.filter(default_centre_id=centre_id)
        except (ValueError, TypeError):
            pass
    
    # Filtre par statut d'abonné
    if is_subscriber:
        if is_subscriber.lower() == 'true':
            patients = patients.filter(is_subscriber=True)
        elif is_subscriber.lower() == 'false':
            patients = patients.filter(is_subscriber=False)
    
    # Filtre par genre
    if gender in ['M', 'F']:
        patients = patients.filter(gender=gender)
    
    # Optimiser avec select_related
    patients = patients.select_related('default_centre').order_by('last_name', 'first_name')
    
    # Pagination
    paginator = Paginator(patients, per_page)
    page_obj = paginator.get_page(page)
    
    # Récupérer tous les centres pour le filtre
    centres = Centre.objects.all().order_by('name')
    
    context = {
        'patients': page_obj,
        'page_obj': page_obj,
        'centres': centres,
        'total_count': paginator.count,
        'total_pages': paginator.num_pages,
        # Préserver les filtres dans le contexte
        'current_search': search_query,
        'current_centre': centre_id,
        'current_subscriber': is_subscriber,
        'current_gender': gender,
    }
    
    return render(request, 'hospital/patients/list.html', context)


@login_required
def patient_detail(request, patient_id):
    """Vue pour le détail d'un patient"""
    patient_service = PatientService()
    
    # Récupérer les détails du patient
    result = patient_service.get_patient_detail(request.user, patient_id)
    
    return render(request, 'hospital/patients/detail.html', result)


@login_required
def create_patient_form(request):
    """Vue pour créer un nouveau patient"""
    if request.method == 'POST':
        form = PatientForm(request.POST, user=request.user)
        if form.is_valid():
            patient_service = PatientService()
            try:
                patient = patient_service.create_patient(request.user, form.cleaned_data)
                
                # Si c'est une requête HTMX, retourner une réponse avec notification
                if request.headers.get('HX-Request'):
                    # Fermer le modal et rafraîchir la liste
                    response = HttpResponse()
                    response['HX-Trigger'] = 'closeModalAndRefresh'
                    return response
                
                messages.success(request, f"Le patient {patient} a été créé avec succès.")
                return redirect('patient_list')
            except PermissionDenied as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = PatientForm(user=request.user)
    
    # Filtrer les centres selon le rôle de l'utilisateur
    if request.user.profile.role == 'SECRETARY':
        form.fields['default_centre'].queryset = request.user.profile.centres.all()
    elif request.user.profile.role == 'NURSE':
        form.fields['default_centre'].queryset = request.user.profile.centres.all()
    
    # Vérifier si l'utilisateur peut modifier les données médicales
    can_edit_medical = CanManagePatientMedicalData().has_permission(request, None)
    
    context = {
        'form': form,
        'action': 'create',
        'title': 'Créer un nouveau patient',
        'can_edit_medical': can_edit_medical
    }
    
    return render(request, 'hospital/patients/form.html', context)


@login_required
@object_permission_required([CanAccessPatient])
def edit_patient(request, patient_id):
    """Vue pour modifier un patient"""
    patient_service = PatientService()
    patient = get_object_or_404(Patient, id=patient_id)
    
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient, user=request.user)
        if form.is_valid():
            try:
                updated_patient = patient_service.update_patient(request.user, patient, form.cleaned_data)
                
                # Si c'est une requête HTMX, retourner une réponse avec notification
                if request.headers.get('HX-Request'):
                    # Fermer le modal et rafraîchir la liste
                    response = HttpResponse()
                    response['HX-Trigger'] = 'closeModalAndRefresh'
                    return response
                
                messages.success(request, f"Le patient {updated_patient} a été mis à jour avec succès.")
                return redirect('patient_list')
            except PermissionDenied as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = PatientForm(instance=patient, user=request.user)
    
    # Filtrer les centres selon le rôle de l'utilisateur
    if request.user.profile.role == 'SECRETARY':
        form.fields['default_centre'].queryset = request.user.profile.centres.all()
    elif request.user.profile.role == 'NURSE':
        form.fields['default_centre'].queryset = request.user.profile.centres.all()
    
    # Vérifier si l'utilisateur peut modifier les données médicales
    can_edit_medical = CanManagePatientMedicalData().has_permission(request, None)
    
    context = {
        'form': form,
        'patient': patient,
        'action': 'edit',
        'title': f'Éditer le patient {patient}',
        'can_edit_medical': can_edit_medical
    }
    
    return render(request, 'hospital/patients/form.html', context)


@login_required
@object_permission_required([CanAccessPatient])
def delete_patient(request, patient_id):
    """Vue pour supprimer un patient"""
    patient_service = PatientService()
    patient = get_object_or_404(Patient, id=patient_id)
    
    if request.method == 'POST':
        try:
            patient_service.delete_patient(request.user, patient)
            
            # Si c'est une requête HTMX, retourner une réponse avec notification
            if request.headers.get('HX-Request'):
                # Fermer le modal et rafraîchir la liste
                response = HttpResponse()
                response['HX-Trigger'] = 'closeModalAndRefresh'
                return response
            
            messages.success(request, f"Le patient {patient} a été supprimé avec succès.")
            return redirect('patient_list')
        except PermissionDenied as e:
            messages.error(request, str(e))
            return redirect('patient_detail', patient_id=patient.id)
    
    return render(request, 'hospital/patients/delete_confirm.html', {'patient': patient})


@login_required
@object_permission_required([CanAccessPatient])
def orient_patient(request, patient_id):
    """Vue pour orienter un patient vers un service"""
    patient = get_object_or_404(Patient, id=patient_id)
    
    if request.method == 'POST':
        orientation = request.POST.get('orientation')
        notes = request.POST.get('notes', '')
        
        if orientation:
            # Créer une consultation, hospitalisation ou urgence selon l'orientation
            if orientation == 'consultation':
                from ..models import Consultation
                consultation = Consultation.objects.create(
                    patient=patient,
                    centre=patient.default_centre,
                    reason=notes or "Orientation depuis la liste des patients",
                    status='PENDING'
                )
                messages.success(request, f"Le patient {patient} a été orienté vers une consultation.")
                return redirect('consultation_detail', consultation_id=consultation.id)
            
            elif orientation == 'hospitalisation':
                from ..models import Hospitalisation
                hospitalisation = Hospitalisation.objects.create(
                    patient=patient,
                    centre=patient.default_centre,
                    service="À déterminer",
                    admission_reason=notes or "Orientation depuis la liste des patients"
                )
                messages.success(request, f"Le patient {patient} a été orienté vers une hospitalisation.")
                return redirect('hospitalisation_detail', hospitalisation_id=hospitalisation.id)
            
            elif orientation == 'emergency':
                from ..models import Emergency
                emergency = Emergency.objects.create(
                    patient=patient,
                    centre=patient.default_centre,
                    reason=notes or "Orientation depuis la liste des patients",
                    triage_level='MEDIUM'
                )
                messages.success(request, f"Le patient {patient} a été orienté vers les urgences.")
                return redirect('emergency_detail', emergency_id=emergency.id)
        else:
            messages.error(request, "Veuillez sélectionner une orientation.")
    
    return render(request, 'hospital/patients/orient_form.html', {'patient': patient})


@login_required
def search_patients(request):
    """Vue pour rechercher des patients"""
    query = request.GET.get('q', '')
    page = request.GET.get('page', 1)
    
    if not query:
        return JsonResponse({'error': 'Veuillez entrer un terme de recherche.'})
    
    patient_service = PatientService()
    result = patient_service.search_patients(request.user, query, page)
    
    # Si c'est une requête HTMX, retourner le HTML
    if request.headers.get('HX-Request'):
        html = render_to_string('hospital/partials/patients_list.html', result, request)
        return JsonResponse({'html': html})
    
    # Sinon, retourner JSON
    patients_data = []
    for patient in result['patients']:
        patients_data.append({
            'id': patient.id,
            'name': str(patient),
            'first_name': patient.first_name,
            'last_name': patient.last_name,
            'postname': patient.postname,
            'phone': patient.phone,
            'centre': patient.default_centre.name if patient.default_centre else None,
        })
    
    return JsonResponse({
        'patients': patients_data,
        'pagination': {
            'current_page': page,
            'total_pages': result['total_pages'],
            'total_count': result['total_count'],
        }
    })


@login_required
@object_permission_required([CanAccessPatient])
def generate_document(request, patient_id, doc_type):
    """Vue pour générer des documents pour un patient"""
    patient = get_object_or_404(Patient, id=patient_id)
    
    # Vérifier si l'utilisateur peut accéder aux données médicales
    can_view_medical = CanManagePatientMedicalData().has_permission(request, None)
    
    if doc_type == 'medical_report' and not can_view_medical:
        raise PermissionDenied("Vous n'avez pas accès aux données médicales du patient.")
    
    # Générer le document selon le type
    if doc_type == 'medical_report':
        template = 'hospital/documents/medical_report.html'
        title = f"Rapport médical - {patient}"
    elif doc_type == 'prescription':
        template = 'hospital/documents/prescription.html'
        title = f"Prescription - {patient}"
    elif doc_type == 'discharge_summary':
        template = 'hospital/documents/discharge_summary.html'
        title = f"Résumé de sortie - {patient}"
    else:
        messages.error(request, "Type de document non reconnu.")
        return redirect('patient_detail', patient_id=patient.id)
    
    context = {
        'patient': patient,
        'title': title,
        'date': timezone.now(),
        'user': request.user,
    }
    
    return render(request, template, context)


@login_required
@object_permission_required([CanAccessPatient])
def print_document(request, patient_id, doc_type):
    """Vue pour imprimer des documents pour un patient"""
    response = generate_document(request, patient_id, doc_type)
    
    # Ajouter des en-têtes pour l'impression
    response['Content-Disposition'] = 'inline; filename="document.html"'
    
    return response


@login_required
def refresh_patients_list(request):
    """Vue pour rafraîchir la liste des patients via HTMX"""
    patient_service = PatientService()
    
    # Récupérer les paramètres de pagination
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 25)
    
    # Récupérer les patients
    result = patient_service.get_patients_for_user(
        user=request.user,
        page=page,
        per_page=per_page
    )
    
    # Si c'est une requête HTMX, retourner uniquement le tableau
    if request.headers.get('HX-Request'):
        return render(request, 'hospital/partials/patients_list_refresh.html', result)
    
    # Sinon, retourner la page complète
    centres = Centre.objects.all()
    context = {
        'centres': centres,
        **result
    }
    
    return render(request, 'hospital/patients/list.html', context)