"""
Vues pour la gestion des rendez-vous
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from ..models import Patient, Appointment, Centre
from ..forms import AppointmentForm
from ..permissions import check_patient_access
from django.contrib.auth.models import User


@login_required
def appointment_list(request):
    """Vue pour la liste des rendez-vous"""
    # Vérifier que l'utilisateur est un médecin ou admin
    if not (request.user.profile.role in ['DOCTOR', 'ADMIN', 'MEDICAL_ADMIN']):
        raise PermissionDenied("Seuls les médecins et administrateurs peuvent gérer les rendez-vous")
    
    from django.core.paginator import Paginator
    
    # Les administrateurs peuvent voir tous les rendez-vous
    if request.user.profile.role in ['ADMIN', 'MEDICAL_ADMIN']:
        appointments = Appointment.objects.all()
    elif request.user.profile.role == 'DOCTOR':
        # Les médecins voient leurs rendez-vous
        appointments = Appointment.objects.filter(doctor=request.user)
    else:
        appointments = Appointment.objects.none()
    
    # Pagination
    paginator = Paginator(appointments, 25)  # 25 rendez-vous par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filtrer les patients selon les droits d'accès de l'utilisateur
    if request.user.profile.role in ['ADMIN', 'MEDICAL_ADMIN']:
        patients = Patient.objects.all()
    else:
        patients = Patient.objects.filter(default_centre__in=request.user.profile.centres.all())
    
    # Filtrer les centres selon les droits d'accès de l'utilisateur
    if request.user.profile.role in ['ADMIN', 'MEDICAL_ADMIN']:
        centres = Centre.objects.all()
    else:
        centres = request.user.profile.centres.all()
    
    # Filtrer les médecins selon les droits d'accès de l'utilisateur
    if request.user.profile.role in ['ADMIN', 'MEDICAL_ADMIN']:
        doctors = User.objects.filter(profile__role='DOCTOR')
    else:
        doctors = User.objects.filter(profile__role='DOCTOR', profile__centres__in=request.user.profile.centres.all())
    
    return render(request, 'hospital/appointments/list.html', {
        'appointments': page_obj,
        'page_obj': page_obj,
        'patients': patients,
        'centres': centres,
        'doctors': doctors,
    })


@login_required
def appointment_create(request):
    """Vue pour créer un rendez-vous"""
    # Vérifier que l'utilisateur est un médecin ou admin
    if not (request.user.profile.role in ['DOCTOR', 'ADMIN']):
        raise PermissionDenied("Seuls les médecins et administrateurs peuvent créer des rendez-vous")
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save()
            messages.success(request, "Rendez-vous créé avec succès.")
            # Si c'est une requête HTMX, on renvoie un script pour fermer la modale et rafraîchir la page
            if request.headers.get('HX-Request'):
                script = """
                <div class="alert alert-success">
                    Rendez-vous créé avec succès.
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
            return redirect('appointment_list')
    else:
        form = AppointmentForm(initial={'date': timezone.now()})
        # Si l'utilisateur est médecin, assigner par défaut
        if request.user.profile.role == 'DOCTOR':
            # Initialiser le formulaire avec le médecin connecté
            form.fields['doctor'].initial = request.user.id
    
    # Filtrer les patients selon les droits d'accès de l'utilisateur
    if request.user.profile.role == 'ADMIN':
        form.fields['patient'].queryset = Patient.objects.all()
        form.fields['centre'].queryset = Centre.objects.all()
        form.fields['doctor'].queryset = User.objects.filter(profile__role='DOCTOR')
    elif request.user.profile.role == 'DOCTOR':
        form.fields['patient'].queryset = Patient.objects.filter(
            default_centre__in=request.user.profile.centres.all()
        )
        form.fields['centre'].queryset = request.user.profile.centres.all()
        form.fields['doctor'].queryset = User.objects.filter(id=request.user.id)
    
    return render(request, 'hospital/appointments/form.html', {
        'form': form,
        'title': 'Créer un nouveau rendez-vous'
    })


@login_required
def appointment_edit(request, appointment_id):
    """Vue pour éditer un rendez-vous"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Vérifier que l'utilisateur a le droit de modifier ce rendez-vous
    if not (request.user.profile.role == 'ADMIN' or 
            (request.user.profile.role == 'DOCTOR' and appointment.doctor == request.user)):
        raise PermissionDenied("Vous n'avez pas le droit de modifier ce rendez-vous")
    
    if request.method == 'POST':
        # Sauvegarder les anciennes valeurs importantes
        old_appointment = Appointment.objects.get(id=appointment_id)
        
        # Créer les données pour le formulaire, en conservant les anciennes valeurs si pas dans le POST
        form_data = request.POST.copy()
        
        # Conserver les champs critiques si non fournis
        for field_name in ['date', 'patient', 'centre']:
            if field_name not in form_data or not form_data[field_name].strip():
                field_value = getattr(old_appointment, field_name)
                if field_value is not None:
                    form_data[field_name] = field_value
        
        form = AppointmentForm(form_data, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, "Rendez-vous mis à jour avec succès.")
            # Si c'est une requête HTMX, on renvoie un script pour fermer la modale et rafraîchir la page
            if request.headers.get('HX-Request'):
                script = """
                <div class="alert alert-success">
                    Rendez-vous mis à jour avec succès.
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
            return redirect('appointment_list')
    else:
        form = AppointmentForm(instance=appointment)
    
    # Filtrer les patients selon les droits d'accès de l'utilisateur
    if request.user.profile.role == 'ADMIN':
        form.fields['patient'].queryset = Patient.objects.all()
        form.fields['centre'].queryset = Centre.objects.all()
        form.fields['doctor'].queryset = User.objects.filter(profile__role='DOCTOR')
    elif request.user.profile.role == 'DOCTOR':
        form.fields['patient'].queryset = Patient.objects.filter(
            default_centre__in=request.user.profile.centres.all()
        )
        form.fields['centre'].queryset = request.user.profile.centres.all()
        form.fields['doctor'].queryset = User.objects.filter(id=request.user.id)
    
    return render(request, 'hospital/appointments/form.html', {
        'form': form,
        'title': f'Éditer le rendez-vous - {appointment.patient}',
        'appointment': appointment
    })


@login_required
def appointment_delete(request, appointment_id):
    """Vue pour supprimer un rendez-vous"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Vérifier que l'utilisateur a le droit de supprimer ce rendez-vous
    if not (request.user.profile.role == 'ADMIN' or 
            (request.user.profile.role == 'DOCTOR' and appointment.doctor == request.user)):
        raise PermissionDenied("Vous n'avez pas le droit de supprimer ce rendez-vous")
    
    if request.method == 'POST':
        patient_id = appointment.patient.id
        appointment.delete()
        messages.success(request, "Rendez-vous supprimé avec succès.")
        # Si c'est une requête HTMX, on renvoie un script pour fermer la modale et rafraîchir la page
        if request.headers.get('HX-Request'):
            script = """
            <div class="alert alert-success">
                Rendez-vous supprimé avec succès.
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
        return redirect('appointment_list')
    
    return render(request, 'hospital/appointments/delete_confirm.html', {'appointment': appointment})


@login_required
def appointment_toggle_status(request, appointment_id):
    """Vue pour basculer le statut d'un rendez-vous (SCHEDULED vers COMPLETED et vice versa)"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Vérifier que l'utilisateur a le droit de modifier ce rendez-vous
    if not (request.user.profile.role == 'ADMIN' or 
            (request.user.profile.role == 'DOCTOR' and appointment.doctor == request.user)):
        raise PermissionDenied("Vous n'avez pas le droit de modifier ce rendez-vous")
    
    # Basculer entre SCHEDULED et COMPLETED
    if appointment.status == 'SCHEDULED':
        appointment.status = 'COMPLETED'
        message = "Rendez-vous marqué comme terminé."
    elif appointment.status == 'COMPLETED':
        appointment.status = 'SCHEDULED'
        message = "Rendez-vous remis à l'état planifié."
    else:
        # Pour les autres statuts (CONFIRMED, CANCELLED), on peut basculer vers COMPLETED
        appointment.status = 'COMPLETED'
        message = "Rendez-vous marqué comme terminé."
    
    appointment.save()
    messages.success(request, message)
    
    # Si c'est une requête HTMX, on renvoie un script pour rafraîchir la page
    if request.headers.get('HX-Request'):
        script = """
        <div class="alert alert-success">
            """ + message + """
        </div>
        <script>
            // Rafraîchir la page après un court délai
            setTimeout(function() {
                window.location.reload();
            }, 300);
        </script>
        """
        return HttpResponse(script)
    
    return redirect('appointment_list')