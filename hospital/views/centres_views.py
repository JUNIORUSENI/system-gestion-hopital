"""
Vues pour la gestion des centres
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q, Count
from ..models import Centre, Profile, User
from ..forms import CentreForm
from ..permissions import (
    CanManageCentres,
    permission_required, object_permission_required
)
from .base import LoginRequiredMixin, AdminRequiredMixin


@login_required
@permission_required([CanManageCentres])
def centre_list(request):
    """Vue pour la liste des centres"""
    centres = Centre.objects.annotate(
        patient_count=Count('patients', distinct=True),
        staff_count=Count('staff', distinct=True)
    ).order_by('name')
    
    # Filtrage
    search_query = request.GET.get('q', '')
    if search_query:
        centres = centres.filter(
            Q(name__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(centres, 25)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)
    
    context = {
        'centres': page_obj,
        'page_obj': page_obj,
    }
    
    return render(request, 'hospital/centres/list.html', context)


@login_required
@permission_required([CanManageCentres])
def centre_detail(request, centre_id):
    """Vue pour le détail d'un centre"""
    centre = get_object_or_404(
        Centre.objects.annotate(
            patient_count=Count('patients', distinct=True),
            staff_count=Count('staff', distinct=True)
        ),
        id=centre_id
    )
    
    # Récupérer le personnel du centre
    staff = User.objects.filter(
        profile__centres=centre
    ).select_related('profile').order_by('username')
    
    # Récupérer les patients du centre
    from ..models import Patient
    patients = Patient.objects.filter(
        default_centre=centre
    ).order_by('last_name', 'first_name')
    
    context = {
        'centre': centre,
        'staff': staff,
        'patients': patients,
    }
    
    return render(request, 'hospital/centres/detail.html', context)


@login_required
@permission_required([CanManageCentres])
def create_centre(request):
    """Vue pour créer un nouveau centre"""
    if request.method == 'POST':
        form = CentreForm(request.POST)
        if form.is_valid():
            centre = form.save()
            messages.success(request, f"Le centre {centre.name} a été créé avec succès.")
            return redirect('centre_detail', centre_id=centre.id)
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = CentreForm()
    
    return render(request, 'hospital/centres/form.html', {'form': form, 'action': 'create'})


@login_required
@permission_required([CanManageCentres])
def edit_centre(request, centre_id):
    """Vue pour modifier un centre"""
    centre = get_object_or_404(Centre, id=centre_id)
    
    if request.method == 'POST':
        form = CentreForm(request.POST, instance=centre)
        if form.is_valid():
            form.save()
            messages.success(request, f"Le centre {centre.name} a été mis à jour avec succès.")
            return redirect('centre_detail', centre_id=centre.id)
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = CentreForm(instance=centre)
    
    context = {
        'form': form,
        'centre': centre,
        'action': 'edit'
    }
    
    return render(request, 'hospital/centres/form.html', context)


@login_required
@permission_required([CanManageCentres])
def delete_centre(request, centre_id):
    """Vue pour supprimer un centre"""
    centre = get_object_or_404(Centre, id=centre_id)
    
    # Vérifier si le centre a des patients ou du personnel
    from ..models import Patient
    patient_count = Patient.objects.filter(default_centre=centre).count()
    staff_count = Profile.objects.filter(centres=centre).count()
    
    if patient_count > 0 or staff_count > 0:
        messages.error(request, f"Impossible de supprimer le centre {centre.name} car il contient {patient_count} patients et {staff_count} membres du personnel.")
        return redirect('centre_detail', centre_id=centre.id)
    
    if request.method == 'POST':
        centre_name = centre.name
        centre.delete()
        messages.success(request, f"Le centre {centre_name} a été supprimé avec succès.")
        return redirect('centre_list')
    
    return render(request, 'hospital/centres/delete_confirm.html', {'centre': centre})


@login_required
@permission_required([CanManageCentres])
def centre_staff(request, centre_id):
    """Vue pour gérer le personnel d'un centre"""
    centre = get_object_or_404(Centre, id=centre_id)
    
    # Récupérer le personnel actuel du centre
    current_staff = User.objects.filter(
        profile__centres=centre
    ).select_related('profile').order_by('username')
    
    # Récupérer le personnel disponible (non assigné à ce centre)
    available_staff = User.objects.exclude(
        profile__centres=centre
    ).select_related('profile').order_by('username')
    
    context = {
        'centre': centre,
        'current_staff': current_staff,
        'available_staff': available_staff,
    }
    
    return render(request, 'hospital/centres/staff.html', context)


@login_required
@permission_required([CanManageCentres])
def add_staff_to_centre(request, centre_id):
    """Vue pour ajouter du personnel à un centre"""
    centre = get_object_or_404(Centre, id=centre_id)
    
    if request.method == 'POST':
        user_ids = request.POST.getlist('user_ids')
        
        for user_id in user_ids:
            try:
                user = User.objects.get(id=user_id)
                profile = user.profile
                profile.centres.add(centre)
            except User.DoesNotExist:
                continue
        
        messages.success(request, f"Le personnel a été ajouté au centre {centre.name} avec succès.")
        return redirect('centre_staff', centre_id=centre_id)
    
    return redirect('centre_staff', centre_id=centre_id)


@login_required
@permission_required([CanManageCentres])
def remove_staff_from_centre(request, centre_id, user_id):
    """Vue pour retirer du personnel d'un centre"""
    centre = get_object_or_404(Centre, id=centre_id)
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        profile = user.profile
        profile.centres.remove(centre)
        
        messages.success(request, f"{user.username} a été retiré du centre {centre.name} avec succès.")
        return redirect('centre_staff', centre_id=centre_id)
    
    return render(request, 'hospital/centres/remove_staff_confirm.html', {
        'centre': centre,
        'user': user
    })


@login_required
@permission_required([CanManageCentres])
def centre_patients(request, centre_id):
    """Vue pour voir les patients d'un centre"""
    centre = get_object_or_404(Centre, id=centre_id)
    
    # Récupérer les patients du centre
    from ..models import Patient
    patients = Patient.objects.filter(
        default_centre=centre
    ).select_related('default_centre').order_by('last_name', 'first_name')
    
    # Pagination
    paginator = Paginator(patients, 25)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)
    
    context = {
        'centre': centre,
        'patients': page_obj,
        'page_obj': page_obj,
    }
    
    return render(request, 'hospital/centres/patients.html', context)


@login_required
@permission_required([CanManageCentres])
def centre_statistics(request, centre_id):
    """Vue pour les statistiques d'un centre"""
    centre = get_object_or_404(Centre, id=centre_id)
    
    # Statistiques générales
    from ..models import Patient, Consultation, Hospitalisation, Emergency, Appointment
    
    patient_count = Patient.objects.filter(default_centre=centre).count()
    consultation_count = Consultation.objects.filter(centre=centre).count()
    hospitalisation_count = Hospitalisation.objects.filter(centre=centre).count()
    emergency_count = Emergency.objects.filter(centre=centre).count()
    appointment_count = Appointment.objects.filter(centre=centre).count()
    
    # Statistiques par rôle du personnel
    staff_by_role = {}
    for role, display in Profile.ROLE_CHOICES:
        count = User.objects.filter(
            profile__centres=centre,
            profile__role=role
        ).count()
        if count > 0:
            staff_by_role[role] = {
                'display': display,
                'count': count,
            }
    
    # Statistiques mensuelles (consultations)
    from django.utils import timezone
    from datetime import timedelta
    try:
        from dateutil.relativedelta import relativedelta
    except ImportError:
        relativedelta = None
    
    monthly_consultations = []
    for i in range(6):
        if relativedelta:
            month_start = (timezone.now().date().replace(day=1) - relativedelta(months=i))
            month_end = (timezone.now().date().replace(day=1) - relativedelta(months=i-1))
        else:
            # Alternative sans relativedelta
            from datetime import date
            import calendar
            today = timezone.now().date()
            if i == 0:
                month_start = today.replace(day=1)
            else:
                # Calcul manuel pour les mois précédents
                year = today.year
                month = today.month - i
                while month <= 0:
                    month += 12
                    year -= 1
                month_start = date(year, month, 1)
            
            if i == 0:
                # Fin du mois en cours
                last_day = calendar.monthrange(today.year, today.month)[1]
                month_end = date(today.year, today.month, last_day) + timedelta(days=1)
            else:
                # Calcul manuel pour la fin du mois
                year = today.year
                month = today.month - (i-1)
                while month <= 0:
                    month += 12
                    year -= 1
                last_day = calendar.monthrange(year, month)[1]
                month_end = date(year, month, last_day) + timedelta(days=1)
        
        count = Consultation.objects.filter(
            centre=centre,
            date__gte=month_start,
            date__lt=month_end
        ).count()
        
        monthly_consultations.append({
            'month': month_start.strftime('%b %Y'),
            'count': count
        })
    
    monthly_consultations.reverse()  # Ordre chronologique
    
    context = {
        'centre': centre,
        'patient_count': patient_count,
        'consultation_count': consultation_count,
        'hospitalisation_count': hospitalisation_count,
        'emergency_count': emergency_count,
        'appointment_count': appointment_count,
        'staff_by_role': staff_by_role,
        'monthly_consultations': monthly_consultations,
    }
    
    return render(request, 'hospital/centres/statistics.html', context)


@login_required
@permission_required([CanManageCentres])
def search_centres(request):
    """Vue pour rechercher des centres"""
    query = request.GET.get('q', '')
    page = request.GET.get('page', 1)
    
    if not query:
        return JsonResponse({'error': 'Veuillez entrer un terme de recherche.'})
    
    # Filtrer par la requête de recherche
    centres = Centre.objects.filter(
        Q(name__icontains=query) |
        Q(address__icontains=query) |
        Q(phone__icontains=query)
    ).annotate(
        patient_count=Count('patients', distinct=True),
        staff_count=Count('staff', distinct=True)
    ).order_by('name')
    
    # Pagination
    paginator = Paginator(centres, 25)
    page_obj = paginator.get_page(page)
    
    # Si c'est une requête HTMX, retourner le HTML
    if request.headers.get('HX-Request'):
        context = {
            'centres': page_obj,
            'page_obj': page_obj,
        }
        html = render_to_string('hospital/partials/centres_list.html', context, request)
        return JsonResponse({'html': html})
    
    # Sinon, retourner JSON
    centres_data = []
    for centre in page_obj:
        centres_data.append({
            'id': centre.id,
            'name': centre.name,
            'address': centre.address[:50] + '...' if len(centre.address) > 50 else centre.address,
            'phone': centre.phone,
            'patient_count': centre.patient_count,
            'staff_count': centre.staff_count,
        })
    
    return JsonResponse({
        'centres': centres_data,
        'pagination': {
            'current_page': page,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
        }
    })


@login_required
@permission_required([CanManageCentres])
def get_centres_partial(request):
    """Vue partielle pour la liste des centres via HTMX"""
    centres = Centre.objects.annotate(
        patient_count=Count('patients', distinct=True),
        staff_count=Count('staff', distinct=True)
    ).order_by('name')
    
    # Filtrage
    search_query = request.GET.get('q', '')
    if search_query:
        centres = centres.filter(
            Q(name__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(centres, 25)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)
    
    context = {
        'centres': page_obj,
        'page_obj': page_obj,
    }
    
    html = render_to_string('hospital/partials/centres_list.html', context, request)
    return JsonResponse({'html': html})


@login_required
@permission_required([CanManageCentres])
def centre_dashboard(request, centre_id):
    """Vue pour le dashboard d'un centre"""
    centre = get_object_or_404(Centre, id=centre_id)
    
    # Statistiques récentes
    from django.utils import timezone
    from datetime import timedelta
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Consultations récentes
    from ..models import Consultation, Hospitalisation, Emergency, Appointment
    
    today_consultations = Consultation.objects.filter(
        centre=centre, date__date=today
    ).count()
    
    week_consultations = Consultation.objects.filter(
        centre=centre, date__date__gte=week_ago
    ).count()
    
    month_consultations = Consultation.objects.filter(
        centre=centre, date__date__gte=month_ago
    ).count()
    
    # Hospitalisations actives
    active_hospitalisations = Hospitalisation.objects.filter(
        centre=centre, discharge_date__isnull=True
    ).count()
    
    # Urgences récentes
    today_emergencies = Emergency.objects.filter(
        centre=centre, admission_time__date=today
    ).count()
    
    week_emergencies = Emergency.objects.filter(
        centre=centre, admission_time__date__gte=week_ago
    ).count()
    
    # Rendez-vous du jour
    today_appointments = Appointment.objects.filter(
        centre=centre, date__date=today
    ).count()
    
    context = {
        'centre': centre,
        'today_consultations': today_consultations,
        'week_consultations': week_consultations,
        'month_consultations': month_consultations,
        'active_hospitalisations': active_hospitalisations,
        'today_emergencies': today_emergencies,
        'week_emergencies': week_emergencies,
        'today_appointments': today_appointments,
        'today': today,
    }
    
    return render(request, 'hospital/centres/dashboard.html', context)