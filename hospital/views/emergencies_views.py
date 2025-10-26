"""
Vues pour la gestion des urgences
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from ..models import Patient, Emergency, Centre
from ..forms import EmergencyForm
from ..permissions import check_patient_access, can_manage_patient_medical_data, can_manage_patient_admin_data
from django.contrib.auth.models import User


@login_required
def emergency_create(request):
    """Vue pour créer une urgence"""
    # Vérifier que l'utilisateur est autorisé à créer des urgences
    if not (hasattr(request.user, 'profile') and request.user.profile.role in ['DOCTOR', 'NURSE', 'ADMIN', 'SECRETARY']):
        raise PermissionDenied("Vous n'êtes pas autorisé à créer des urgences")
    
    if request.method == 'POST':
        patient_id = request.POST.get('patient_id')
        patient = get_object_or_404(Patient, id=patient_id)
        
        # Vérifier si l'utilisateur a le droit d'accéder à ce patient
        if not check_patient_access(request.user, patient):
            raise PermissionDenied("Vous n'avez pas accès à ce patient")
        
        # Déterminer qui peut définir les champs médicaux
        can_manage_medical = can_manage_patient_medical_data(request.user)
        
        emergency_data = {
            'patient': patient,
            'centre_id': request.POST.get('centre_id'),
            'reason': request.POST.get('reason'),
        }
        
        # Définir le niveau de triage par défaut si non fourni et l'utilisateur est médical
        if 'triage_level' in request.POST:
            emergency_data['triage_level'] = request.POST.get('triage_level')
        elif request.user.profile.role in ['NURSE', 'DOCTOR']:
            # Si c'est un personnel médical et pas de triage fourni, on peut laisser vide
            # pour permettre le triage ultérieur
            pass
        else:
            # Pour les autres, pas de triage
            pass
        
        # Les champs médicaux ne peuvent être définis que par les médecins ou infirmiers
        if can_manage_medical or request.user.profile.role == 'NURSE':
            # Seuls les médecins peuvent poser un diagnostic initial ou orientation
            if request.user.profile.role == 'DOCTOR':
                emergency_data['initial_diagnosis'] = request.POST.get('initial_diagnosis')
                emergency_data['orientation'] = request.POST.get('orientation')
                doctor_id = request.POST.get('doctor_id')
                if doctor_id:
                    emergency_data['doctor_id'] = doctor_id
                else:
                    emergency_data['doctor'] = request.user
            else:
                # Pour les infirmiers, assigner le médecin courant s'il est présent
                emergency_data['doctor'] = request.user if hasattr(request.user, 'profile') and request.user.profile.role == 'DOCTOR' else None
            
            # Les deux (médecins et infirmiers) peuvent enregistrer les signes vitaux et premiers soins
            emergency_data['vital_signs'] = request.POST.get('vital_signs')
            emergency_data['first_aid'] = request.POST.get('first_aid')
        else:
            # Pour les secrétaires, limiter aux informations d'admission
            emergency_data['doctor'] = request.user if request.user.is_authenticated else None
        
        emergency = Emergency.objects.create(**emergency_data)
        
        messages.success(request, "Urgence enregistrée avec succès.")
        # Si c'est une requête HTMX, on renvoie un script pour fermer la modale et rafraîchir la page
        if request.headers.get('HX-Request'):
            script = """
            <div class="alert alert-success">
                Urgence enregistrée avec succès.
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
    return render(request, 'hospital/emergencies/form.html', {
        'patients': filtered_patients,
        'centres': centres,
        'doctors': doctors,
        'title': 'Enregistrer une nouvelle urgence',
        'can_manage_medical': can_manage_patient_medical_data(request.user),
        'selected_patient': selected_patient
    })


@login_required
def emergency_triage(request, emergency_id):
    """Vue pour le triage médical d'une urgence"""
    # Vérifier que l'utilisateur a un profil
    if not hasattr(request.user, 'profile'):
        raise PermissionDenied("Utilisateur sans profil")
    
    emergency = get_object_or_404(Emergency, id=emergency_id)
    
    # Vérifier si l'utilisateur a le droit d'accéder à cette urgence
    if not check_patient_access(request.user, emergency.patient):
        raise PermissionDenied("Vous n'avez pas accès à cette urgence")
    
    # Seuls les médecins et infirmiers peuvent effectuer un triage
    if request.user.profile.role not in ['DOCTOR', 'NURSE']:
        raise PermissionDenied("Seuls les médecins et infirmiers peuvent effectuer un triage")
    
    if request.method == 'POST':
        # Mettre à jour les informations de triage
        emergency.triage_level = request.POST.get('triage_level')
        emergency.vital_signs = request.POST.get('vital_signs')
        emergency.first_aid = request.POST.get('first_aid')
        
        # Seuls les médecins peuvent poser un diagnostic initial ou orientation
        if request.user.profile.role == 'DOCTOR':
            emergency.initial_diagnosis = request.POST.get('initial_diagnosis')
            emergency.orientation = request.POST.get('orientation')
            if request.POST.get('doctor_id'):
                emergency.doctor_id = request.POST.get('doctor_id')
        
        emergency.save()
        
        messages.success(request, "Triage effectué avec succès.")
        # Si c'est une requête HTMX, on renvoie un script pour fermer la modale et rafraîchir la page
        if request.headers.get('HX-Request'):
            script = """
            <div class="alert alert-success">
                Triage effectué avec succès.
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
        return redirect('patient_detail', patient_id=emergency.patient.id)
    
    doctors = User.objects.filter(profile__role='DOCTOR')
    
    return render(request, 'hospital/emergencies/triage_form.html', {
        'emergency': emergency,
        'doctors': doctors,
        'title': f'Triage - {emergency.patient.first_name} {emergency.patient.last_name}'
    })


@login_required
def emergency_edit(request, emergency_id):
    """Vue pour éditer une urgence"""
    # Vérifier que l'utilisateur a un profil
    if not hasattr(request.user, 'profile'):
        raise PermissionDenied("Utilisateur sans profil")
    
    emergency = get_object_or_404(Emergency, id=emergency_id)
    
    # Vérifier si l'utilisateur a le droit d'accéder à cette urgence
    if not check_patient_access(request.user, emergency.patient):
        raise PermissionDenied("Vous n'avez pas accès à cette urgence")
    
    # Vérifier les permissions d'édition
    can_manage_medical = can_manage_patient_medical_data(request.user)
    is_nurse = request.user.profile.role in ['NURSE', 'DOCTOR']
    
    if request.method == 'POST':
        # Sauvegarder les anciennes valeurs importantes
        old_emergency = Emergency.objects.get(id=emergency_id)
        
        # Seulement les médecins peuvent modifier les informations médicales critiques
        if can_manage_medical:
            emergency.triage_level = request.POST.get('triage_level') or old_emergency.triage_level
            emergency.initial_diagnosis = request.POST.get('initial_diagnosis') or old_emergency.initial_diagnosis
            emergency.orientation = request.POST.get('orientation') or old_emergency.orientation
            emergency.doctor_id = request.POST.get('doctor_id') or old_emergency.doctor_id
        else:
            # Conserver les anciennes valeurs médicales si l'utilisateur n'a pas les droits
            emergency.triage_level = old_emergency.triage_level
            emergency.initial_diagnosis = old_emergency.initial_diagnosis
            emergency.orientation = old_emergency.orientation
            emergency.doctor_id = old_emergency.doctor_id
        
        # Les médecins et infirmiers peuvent modifier les signes vitaux et premiers soins
        if is_nurse:
            emergency.vital_signs = request.POST.get('vital_signs') or old_emergency.vital_signs
            emergency.first_aid = request.POST.get('first_aid') or old_emergency.first_aid
        else:
            # Conserver les anciennes valeurs si l'utilisateur n'est pas médical
            emergency.vital_signs = old_emergency.vital_signs
            emergency.first_aid = old_emergency.first_aid
        
        # Les informations générales peuvent être modifiées par les autorisés
        if can_manage_patient_admin_data(request.user):
            emergency.reason = request.POST.get('reason') or old_emergency.reason
            emergency.centre_id = request.POST.get('centre_id') or old_emergency.centre_id
        else:
            # Conserver les anciennes valeurs si l'utilisateur n'a pas les droits
            emergency.reason = old_emergency.reason
            emergency.centre_id = old_emergency.centre_id
        
        emergency.save()
        
        messages.success(request, "Urgence mise à jour avec succès.")
        # Si c'est une requête HTMX, on renvoie un script pour fermer la modale et rafraîchir la page
        if request.headers.get('HX-Request'):
            script = """
            <div class="alert alert-success">
                Urgence mise à jour avec succès.
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
        return redirect('emergency_list')
    
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
    is_nurse = request.user.profile.role in ['NURSE', 'DOCTOR']
    
    return render(request, 'hospital/emergencies/form.html', {
        'emergency': emergency,
        'patients': filtered_patients,
        'centres': centres,
        'doctors': doctors,
        'title': f'Éditer l\'urgence - {emergency.patient}',
        'can_edit_medical': can_edit_medical,
        'is_nurse': is_nurse
    })


@login_required
def emergency_delete(request, emergency_id):
    """Vue pour supprimer une urgence"""
    # Vérifier que l'utilisateur a un profil
    if not hasattr(request.user, 'profile'):
        raise PermissionDenied("Utilisateur sans profil")
    
    emergency = get_object_or_404(Emergency, id=emergency_id)
    
    # Vérifier si l'utilisateur a le droit d'accéder à cette urgence
    if not check_patient_access(request.user, emergency.patient):
        raise PermissionDenied("Vous n'avez pas accès à cette urgence")
    
    # Seuls les administrateurs peuvent supprimer des urgences
    if request.user.profile.role != 'ADMIN':
        raise PermissionDenied("Seuls les administrateurs peuvent supprimer des urgences")
    
    if request.method == 'POST':
        patient_id = emergency.patient.id
        emergency.delete()
        messages.success(request, "Urgence supprimée avec succès.")
        # Si c'est une requête HTMX, on renvoie un script pour fermer la modale et rafraîchir la page
        if request.headers.get('HX-Request'):
            script = """
            <div class="alert alert-success">
                Urgence supprimée avec succès.
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
    
    return render(request, 'hospital/emergencies/delete_confirm.html', {
        'emergency': emergency
    })


@login_required
def emergency_detail(request, emergency_id):
    """Vue pour le détail d'une urgence"""
    emergency = get_object_or_404(Emergency, id=emergency_id)
    
    # Vérifier si l'utilisateur a le droit d'accéder à cette urgence
    if not check_patient_access(request.user, emergency.patient):
        raise PermissionDenied("Vous n'avez pas accès à cette urgence")
    
    return render(request, 'hospital/emergencies/detail.html', {
        'emergency': emergency
    })


@login_required
def emergency_list(request):
    """Vue pour la liste des urgences avec pagination"""
    # Vérifier que l'utilisateur a un profil
    if not hasattr(request.user, 'profile'):
        raise PermissionDenied("Utilisateur sans profil")
    
    from django.core.paginator import Paginator
    
    # Les administrateurs peuvent voir toutes les urgences
    if request.user.profile.role in ['ADMIN', 'MEDICAL_ADMIN']:
        emergencies = Emergency.objects.all()
    elif request.user.profile.role == 'DOCTOR':
        # Les médecins peuvent voir toutes les urgences des patients de tous les centres
        emergencies = Emergency.objects.all()
    elif request.user.profile.role in ['SECRETARY', 'NURSE']:
        # Les secrétaires et infirmiers voient les urgences de leurs centres
        emergencies = Emergency.objects.filter(centre__in=request.user.profile.centres.all())
    else:
        emergencies = Emergency.objects.none()
    
    # Pagination
    paginator = Paginator(emergencies, 25)  # 25 urgences par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'hospital/emergencies/list.html', {
        'emergencies': page_obj,
        'page_obj': page_obj
    })