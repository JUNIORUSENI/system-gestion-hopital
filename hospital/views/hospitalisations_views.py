"""
Vues pour la gestion des hospitalisations
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.models import User

from ..models import Patient, Hospitalisation, Centre
from ..forms import HospitalisationForm
from ..permissions import check_patient_access, can_manage_patient_medical_data, can_manage_patient_admin_data


@login_required
def hospitalisation_list(request):
    """Vue pour la liste des hospitalisations avec pagination et recherche"""
    # Récupérer les paramètres de recherche et filtrage
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    service_filter = request.GET.get('service', '').strip()
    page = request.GET.get('page', 1)
    
    # Les administrateurs peuvent voir toutes les hospitalisations
    if request.user.profile.role in ['ADMIN', 'MEDICAL_ADMIN']:
        hospitalisations = Hospitalisation.objects.all()
    elif request.user.profile.role == 'DOCTOR':
        # Les médecins voient toutes les hospitalisations
        hospitalisations = Hospitalisation.objects.all()
    elif request.user.profile.role in ['SECRETARY', 'NURSE']:
        # Les secrétaires et infirmiers voient les hospitalisations de leurs centres
        hospitalisations = Hospitalisation.objects.filter(centre__in=request.user.profile.centres.all())
    else:
        hospitalisations = Hospitalisation.objects.none()
    
    # Appliquer la recherche
    if search_query:
        hospitalisations = hospitalisations.filter(
            Q(id__icontains=search_query) |
            Q(patient__first_name__icontains=search_query) |
            Q(patient__last_name__icontains=search_query) |
            Q(patient__postname__icontains=search_query) |
            Q(service__icontains=search_query) |
            Q(room__icontains=search_query) |
            Q(bed__icontains=search_query)
        )
    
    # Filtre par statut (actif/terminé)
    if status_filter == 'active':
        hospitalisations = hospitalisations.filter(discharge_date__isnull=True)
    elif status_filter == 'discharged':
        hospitalisations = hospitalisations.filter(discharge_date__isnull=False)
    
    # Filtre par service
    if service_filter:
        hospitalisations = hospitalisations.filter(service__icontains=service_filter)
    
    # Optimiser avec select_related
    hospitalisations = hospitalisations.select_related('patient', 'doctor', 'centre').order_by('-admission_date')
    
    # Récupérer les services uniques pour le filtre
    services = Hospitalisation.objects.values_list('service', flat=True).distinct().order_by('service')
    
    # Pagination
    paginator = Paginator(hospitalisations, 25)
    page_obj = paginator.get_page(page)
    
    return render(request, 'hospital/hospitalisations/list.html', {
        'hospitalisations': page_obj,
        'page_obj': page_obj,
        'services': services,
        'current_search': search_query,
        'current_status': status_filter,
        'current_service': service_filter,
        'total_count': paginator.count,
    })


@login_required
def hospitalisation_create(request):
    """Vue pour créer une hospitalisation"""
    # Vérifier que l'utilisateur est un médecin ou admin (pour les données médicales)
    # ou secrétaire pour l'admission administrative
    if not (request.user.profile.role in ['DOCTOR', 'ADMIN', 'SECRETARY']):
        raise PermissionDenied("Vous n'êtes pas autorisé à créer des hospitalisations")
    
    if request.method == 'POST':
        patient_id = request.POST.get('patient_id')
        patient = get_object_or_404(Patient, id=patient_id)
        
        # Vérifier si l'utilisateur a le droit d'accéder à ce patient
        if not check_patient_access(request.user, patient):
            raise PermissionDenied("Vous n'avez pas accès à ce patient")
        
        # Déterminer qui peut définir les champs médicaux
        can_manage_medical = can_manage_patient_medical_data(request.user)
        
        hospitalisation_data = {
            'patient': patient,
            'centre_id': request.POST.get('centre_id'),
            'service': request.POST.get('service'),
            'room': request.POST.get('room'),
            'bed': request.POST.get('bed'),
            'admission_reason': request.POST.get('admission_reason'),
        }
        
        # Les champs médicaux ne peuvent être définis que par les médecins
        if can_manage_medical:
            hospitalisation_data['medical_notes'] = request.POST.get('medical_notes')
            doctor_id = request.POST.get('doctor_id')
            if doctor_id:
                hospitalisation_data['doctor_id'] = doctor_id
            else:
                hospitalisation_data['doctor'] = request.user
        else:
            # Pour les secrétaires, ne pas permettre la saisie des champs médicaux
            hospitalisation_data['doctor'] = request.user if request.user.is_authenticated else None
        
        hospitalisation = Hospitalisation.objects.create(**hospitalisation_data)
        
        messages.success(request, "Hospitalisation créée avec succès.")
        # Si c'est une requête HTMX, on renvoie un script pour fermer la modale et rafraîchir la page
        if request.headers.get('HX-Request'):
            script = """
            <div class="alert alert-success">
                Hospitalisation créée avec succès.
            </div>
            <script>
                // Fermer la modale
                const modal = document.querySelector('.modal');
                if (modal) {
                    const modalInstance = bootstrap.Modal.getInstance(modal);
                    if (modalInstance) {
                        modalInstance.hide();
                    } else {
                        // Si l'instance n'existe pas, on la crée et on la ferme
                        const bsModal = new bootstrap.Modal(modal);
                        bsModal.hide();
                    }
                }
                // Rafraîchir la page après un court délai pour permettre la fermeture de la modale
                setTimeout(function() {
                    window.location.reload();
                }, 300);
            </script>
            """
            return HttpResponse(script)
        return redirect('patient_detail', patient_id=patient.id)
    
    patients = Patient.objects.all()
    # Filtrer les patients selon les droits d'accès de l'utilisateur
    filtered_patients = []
    for patient in patients:
        if check_patient_access(request.user, patient):
            filtered_patients.append(patient)
    
    # Récupérer le patient_id depuis les paramètres GET s'il est présent
    selected_patient_id = request.GET.get('patient_id')
    selected_patient = None
    if selected_patient_id:
        try:
            selected_patient = Patient.objects.get(id=selected_patient_id)
            # Vérifier si l'utilisateur a le droit d'accéder à ce patient
            if not check_patient_access(request.user, selected_patient):
                selected_patient = None
        except Patient.DoesNotExist:
            selected_patient = None
    
    centres = Centre.objects.all()
    doctors = User.objects.filter(profile__role='DOCTOR')
    
    # Déterminer les rôles
    can_edit_medical = can_manage_patient_medical_data(request.user)
    is_nurse = request.user.profile.role == 'NURSE'
    is_doctor = request.user.profile.role in ['DOCTOR', 'MEDICAL_ADMIN']
    
    return render(request, 'hospital/hospitalisations/form.html', {
        'patients': filtered_patients,
        'centres': centres,
        'doctors': doctors,
        'title': 'Créer une nouvelle hospitalisation',
        'can_edit_medical': can_edit_medical,
        'is_nurse': is_nurse,
        'is_doctor': is_doctor,
        'selected_patient': selected_patient,
        'selected_patient_id': selected_patient_id
    })


@login_required
def hospitalisation_edit(request, hospitalisation_id):
    """Vue pour éditer une hospitalisation"""
    hospitalisation = get_object_or_404(Hospitalisation, id=hospitalisation_id)
    
    # Vérifier si l'utilisateur a le droit d'accéder à cette hospitalisation
    if not check_patient_access(request.user, hospitalisation.patient):
        raise PermissionDenied("Vous n'avez pas accès à cette hospitalisation")
    
    # Vérifier les permissions d'édition
    can_manage_medical = can_manage_patient_medical_data(request.user)
    is_nurse = request.user.profile.role == 'NURSE'
    
    if request.method == 'POST':
        # Vérifier que l'utilisateur a la permission de modifier
        if not (can_manage_medical or is_nurse):
            raise PermissionDenied("Vous n'êtes pas autorisé à modifier cette hospitalisation")
        
        # Sauvegarder les anciennes valeurs importantes
        old_hospitalisation = Hospitalisation.objects.get(id=hospitalisation_id)
        
        hospitalisation.service = request.POST.get('service') or old_hospitalisation.service
        hospitalisation.room = request.POST.get('room') or old_hospitalisation.room
        hospitalisation.bed = request.POST.get('bed') or old_hospitalisation.bed
        hospitalisation.admission_reason = request.POST.get('admission_reason') or old_hospitalisation.admission_reason
        hospitalisation.centre_id = request.POST.get('centre_id') or old_hospitalisation.centre_id
        hospitalisation.doctor_id = request.POST.get('doctor_id') or old_hospitalisation.doctor_id
        
        # Seulement les médecins peuvent modifier les notes médicales
        if can_manage_medical:
            hospitalisation.medical_notes = request.POST.get('medical_notes') or old_hospitalisation.medical_notes
            # Les médecins peuvent également mettre à jour le résumé de sortie
            hospitalisation.discharge_summary = request.POST.get('discharge_summary') or old_hospitalisation.discharge_summary
        else:
            # Si ce n'est pas un médecin, conserver les anciennes notes médicales et résumé
            hospitalisation.medical_notes = old_hospitalisation.medical_notes
            hospitalisation.discharge_summary = old_hospitalisation.discharge_summary
        
        # Les infirmiers peuvent ajouter des notes infirmières
        if is_nurse:
            nurse_notes = request.POST.get('nurse_notes', '')
            if nurse_notes.strip():
                # Ajouter les nouvelles notes aux anciennes avec une date/heure
                current_time = timezone.now().strftime("%d/%m/%Y %H:%M")
                new_note = f"[{current_time}] {nurse_notes}\n"
                if hospitalisation.nurse_notes:
                    hospitalisation.nurse_notes = new_note + hospitalisation.nurse_notes
                else:
                    hospitalisation.nurse_notes = new_note
        else:
            # Si ce n'est pas un infirmier, conserver les anciennes notes infirmières
            hospitalisation.nurse_notes = old_hospitalisation.nurse_notes
        
        hospitalisation.save()
        
        messages.success(request, "Hospitalisation mise à jour avec succès.")
        # Si c'est une requête HTMX, on renvoie un script pour fermer la modale et rafraîchir la page
        if request.headers.get('HX-Request'):
            script = """
            <div class="alert alert-success">
                Hospitalisation mise à jour avec succès.
            </div>
            <script>
                // Fermer la modale
                const modal = document.querySelector('.modal');
                if (modal) {
                    const modalInstance = bootstrap.Modal.getInstance(modal);
                    if (modalInstance) {
                        modalInstance.hide();
                    } else {
                        // Si l'instance n'existe pas, on la crée et on la ferme
                        const bsModal = new bootstrap.Modal(modal);
                        bsModal.hide();
                    }
                }
                // Rafraîchir la page après un court délai pour permettre la fermeture de la modale
                setTimeout(function() {
                    window.location.reload();
                }, 300);
            </script>
            """
            return HttpResponse(script)
        return redirect('hospitalisation_list')
    
    patients = Patient.objects.all()
    # Filtrer les patients selon les droits d'accès de l'utilisateur
    filtered_patients = []
    for patient in patients:
        if check_patient_access(request.user, patient):
            filtered_patients.append(patient)
    
    centres = Centre.objects.all()
    doctors = User.objects.filter(profile__role='DOCTOR')
    
    # Déterminer les champs visibles selon le rôle
    can_edit_medical = can_manage_patient_medical_data(request.user)
    is_nurse = request.user.profile.role == 'NURSE'
    is_doctor = request.user.profile.role in ['DOCTOR', 'MEDICAL_ADMIN']
    
    return render(request, 'hospital/hospitalisations/form.html', {
        'hospitalisation': hospitalisation,
        'patients': filtered_patients,
        'centres': centres,
        'doctors': doctors,
        'title': f'Éditer l\'hospitalisation - {hospitalisation.patient}',
        'can_edit_medical': can_edit_medical,
        'is_nurse': is_nurse,
        'is_doctor': is_doctor
    })


@login_required
def hospitalisation_discharge(request, hospitalisation_id):
    """Vue pour la sortie d'hospitalisation et le résumé de sortie"""
    hospitalisation = get_object_or_404(Hospitalisation, id=hospitalisation_id)
    
    # Vérifier si l'utilisateur a le droit d'accéder à cette hospitalisation
    if not check_patient_access(request.user, hospitalisation.patient):
        raise PermissionDenied("Vous n'avez pas accès à cette hospitalisation")
    
    # Seulement les médecins peuvent effectuer une sortie
    if not can_manage_patient_medical_data(request.user):
        raise PermissionDenied("Seuls les médecins peuvent effectuer une sortie d'hospitalisation")
    
    if request.method == 'POST':
        # Mettre à jour les informations de sortie
        hospitalisation.discharge_summary = request.POST.get('discharge_summary')
        hospitalisation.discharge_date = timezone.now()
        
        # Mettre à jour les interventions et notes médicales si fournies
        interventions = request.POST.get('interventions')
        if interventions:
            if hospitalisation.interventions:
                hospitalisation.interventions += "\n" + f"[{timezone.now().strftime('%d/%m/%Y %H:%M')}] {interventions}"
            else:
                hospitalisation.interventions = f"[{timezone.now().strftime('%d/%m/%Y %H:%M')}] {interventions}"
        
        hospitalisation.save()
        
        messages.success(request, "Patient sorti avec succès.")
        # Si c'est une requête HTMX, on renvoie un script pour fermer la modale et rafraîchir la page
        if request.headers.get('HX-Request'):
            script = """
            <div class="alert alert-success">
                Patient sorti avec succès.
            </div>
            <script>
                // Fermer la modale
                const modal = document.querySelector('.modal');
                if (modal) {
                    const modalInstance = bootstrap.Modal.getInstance(modal);
                    if (modalInstance) {
                        modalInstance.hide();
                    } else {
                        // Si l'instance n'existe pas, on la crée et on la ferme
                        const bsModal = new bootstrap.Modal(modal);
                        bsModal.hide();
                    }
                }
                // Rafraîchir la page après un court délai pour permettre la fermeture de la modale
                setTimeout(function() {
                    window.location.reload();
                }, 300);
            </script>
            """
            return HttpResponse(script)
        return redirect('patient_detail', patient_id=hospitalisation.patient.id)
    
    return render(request, 'hospital/hospitalisations/discharge_form.html', {
        'hospitalisation': hospitalisation,
        'title': f'Sortie - {hospitalisation.patient.first_name} {hospitalisation.patient.last_name}'
    })


@login_required
def hospitalisation_delete(request, hospitalisation_id):
    """Vue pour supprimer une hospitalisation"""
    hospitalisation = get_object_or_404(Hospitalisation, id=hospitalisation_id)
    
    if request.method == 'POST':
        patient_id = hospitalisation.patient.id
        hospitalisation.delete()
        messages.success(request, "Hospitalisation supprimée avec succès.")
        # Si c'est une requête HTMX, on renvoie un script pour fermer la modale et rafraîchir la page
        if request.headers.get('HX-Request'):
            script = """
            <div class="alert alert-success">
                Hospitalisation supprimée avec succès.
            </div>
            <script>
                // Fermer la modale
                const modal = document.querySelector('.modal');
                if (modal) {
                    const modalInstance = bootstrap.Modal.getInstance(modal);
                    if (modalInstance) {
                        modalInstance.hide();
                    } else {
                        // Si l'instance n'existe pas, on la crée et on la ferme
                        const bsModal = new bootstrap.Modal(modal);
                        bsModal.hide();
                    }
                }
                // Rafraîchir la page après un court délai pour permettre la fermeture de la modale
                setTimeout(function() {
                    window.location.reload();
                }, 300);
            </script>
            """
            return HttpResponse(script)
        return redirect('patient_detail', patient_id=patient_id)
    
    return render(request, 'hospital/hospitalisations/delete_confirm.html', {
        'hospitalisation': hospitalisation
    })


@login_required
def hospitalisation_detail(request, hospitalisation_id):
    """Vue pour le détail d'une hospitalisation"""
    hospitalisation = get_object_or_404(Hospitalisation, id=hospitalisation_id)
    
    # Vérifier si l'utilisateur a le droit d'accéder à cette hospitalisation
    if not check_patient_access(request.user, hospitalisation.patient):
        raise PermissionDenied("Vous n'avez pas accès à cette hospitalisation")
    
    return render(request, 'hospital/hospitalisations/detail.html', {
        'hospitalisation': hospitalisation
    })