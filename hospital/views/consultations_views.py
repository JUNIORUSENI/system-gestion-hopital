"""
Vues pour la gestion des consultations
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from ..models import Patient, Consultation
from ..forms import ConsultationForm
from ..permissions import check_patient_access, can_manage_patient_medical_data


@login_required
def consultation_detail(request, consultation_id):
    """Vue pour le détail d'une consultation"""
    consultation = get_object_or_404(Consultation, id=consultation_id)
    
    # Vérifier si l'utilisateur a le droit d'accéder à cette consultation
    if not check_patient_access(request.user, consultation.patient):
        raise PermissionDenied("Vous n'avez pas accès à cette consultation")
    
    return render(request, 'hospital/consultations/detail.html', {
        'consultation': consultation
    })


@login_required
def consultation_list(request):
    """Vue pour la liste des consultations avec pagination"""
    from django.core.paginator import Paginator
    
    # Les administrateurs peuvent voir toutes les consultations
    if request.user.profile.role in ['ADMIN', 'MEDICAL_ADMIN']:
        consultations = Consultation.objects.all()
    elif request.user.profile.role == 'DOCTOR':
        # Les médecins peuvent voir toutes les consultations des patients de tous les centres
        consultations = Consultation.objects.all()
    elif request.user.profile.role in ['SECRETARY', 'NURSE']:
        # Les secrétaires et infirmiers voient les consultations des patients de leurs centres
        consultations = Consultation.objects.filter(patient__default_centre__in=request.user.profile.centres.all())
    else:
        consultations = Consultation.objects.none()
    
    # Pagination
    paginator = Paginator(consultations, 25)  # 25 consultations par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'hospital/consultations/list.html', {
        'consultations': page_obj,
        'page_obj': page_obj
    })


@login_required
def consultation_create(request):
    """Vue pour créer une consultation"""
    # Vérifier que l'utilisateur est un médecin ou admin
    if not can_manage_patient_medical_data(request.user):
        raise PermissionDenied("Seuls les médecins et administrateurs peuvent créer des consultations")
    
    if request.method == 'POST':
        # Traitement de la création de consultation
        patient_id = request.POST.get('patient_id')
        patient = get_object_or_404(Patient, id=patient_id)
        
        # Vérifier si l'utilisateur a le droit d'accéder à ce patient
        if not check_patient_access(request.user, patient):
            raise PermissionDenied("Vous n'avez pas accès à ce patient")
        
        # Gérer la date de suivi
        follow_up_date = request.POST.get('follow_up_date')
        if follow_up_date:
            follow_up_date_value = follow_up_date
        else:
            follow_up_date_value = None
            
        # Gérer la date de rendez-vous
        appointment_date = request.POST.get('appointment_date')
        if appointment_date and appointment_date.strip() != '':  # Vérifier que la valeur n'est pas vide ou espace(s)
            appointment_date_value = appointment_date
        else:
            appointment_date_value = None
        
        consultation = Consultation.objects.create(
            patient=patient,
            doctor=request.user,
            centre=patient.default_centre,
            appointment_date=appointment_date_value,
            status=request.POST.get('status', 'PENDING'),
            reason=request.POST.get('reason', ''),
            clinical_exam=request.POST.get('clinical_exam', ''),
            diagnosis=request.POST.get('diagnosis', ''),
            prescription=request.POST.get('prescription', ''),
            follow_up_date=follow_up_date_value
        )
        
        messages.success(request, "Consultation créée avec succès.")
        # Si c'est une requête HTMX, on renvoie un script pour fermer la modale et rafraîchir la page
        if request.headers.get('HX-Request'):
            script = """
            <div class="alert alert-success">
                Consultation créée avec succès.
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
    
    # Partie GET - Afficher le formulaire
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
    
    patients = Patient.objects.all()
    # Filtrer les patients selon les droits d'accès de l'utilisateur
    filtered_patients = []
    for patient in patients:
        if check_patient_access(request.user, patient):
            filtered_patients.append(patient)
    
    return render(request, 'hospital/consultations/form.html', {
        'patients': filtered_patients,
        'selected_patient': selected_patient,
        'title': 'Créer une nouvelle consultation'
    })


@login_required
def consultation_edit(request, consultation_id):
    """Vue pour éditer une consultation"""
    consultation = get_object_or_404(Consultation, id=consultation_id)
    
    # Vérifier si l'utilisateur a le droit d'accéder à cette consultation
    if not check_patient_access(request.user, consultation.patient):
        raise PermissionDenied("Vous n'avez pas accès à cette consultation")
    
    # Vérifier que l'utilisateur est un médecin ou admin
    if not can_manage_patient_medical_data(request.user):
        raise PermissionDenied("Seuls les médecins et administrateurs peuvent modifier des consultations")
    
    if request.method == 'POST':
        # Sauvegarder les anciennes valeurs importantes
        old_consultation = Consultation.objects.get(id=consultation_id)
        
        consultation.reason = request.POST.get('reason') or old_consultation.reason
        consultation.clinical_exam = request.POST.get('clinical_exam') or old_consultation.clinical_exam
        consultation.diagnosis = request.POST.get('diagnosis') or old_consultation.diagnosis
        consultation.prescription = request.POST.get('prescription') or old_consultation.prescription
        
        # Gérer la date de suivi
        follow_up_date = request.POST.get('follow_up_date')
        if follow_up_date:
            consultation.follow_up_date = follow_up_date
        else:
            consultation.follow_up_date = old_consultation.follow_up_date  # Garder l'ancienne valeur
            
        # Gérer la date de rendez-vous
        appointment_date = request.POST.get('appointment_date')
        if appointment_date and appointment_date.strip() != '':  # Vérifier que la valeur n'est pas vide ou espace(s)
            consultation.appointment_date = appointment_date
        else:
            consultation.appointment_date = old_consultation.appointment_date  # Garder l'ancienne valeur
            
        consultation.status = request.POST.get('status') or old_consultation.status
        consultation.save()
        
        messages.success(request, "Consultation mise à jour avec succès.")
        # Si c'est une requête HTMX, on renvoie un script pour fermer la modale et rafraîchir la page
        if request.headers.get('HX-Request'):
            script = """
            <div class="alert alert-success">
                Consultation mise à jour avec succès.
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
        return redirect('consultation_list')
    
    return render(request, 'hospital/consultations/form.html', {
        'consultation': consultation,
        'title': f'Éditer la consultation - {consultation.patient}',
        'patients': Patient.objects.all()
    })


@login_required
def consultation_delete(request, consultation_id):
    """Vue pour supprimer une consultation"""
    consultation = get_object_or_404(Consultation, id=consultation_id)
    
    if request.method == 'POST':
        patient_id = consultation.patient.id
        consultation.delete()
        messages.success(request, "Consultation supprimée avec succès.")
        # Si c'est une requête HTMX, on renvoie un script pour fermer la modale et rafraîchir la page
        if request.headers.get('HX-Request'):
            script = """
            <div class="alert alert-success">
                Consultation supprimée avec succès.
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
    
    return render(request, 'hospital/consultations/delete_confirm.html', {
        'consultation': consultation
    })