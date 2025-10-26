"""
Vues pour la gestion des utilisateurs
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.template.loader import render_to_string
from ..models import Profile, Centre
from ..forms import UserRegistrationForm
from ..permissions import (
    CanManageUsers, CanManageCentres,
    permission_required, object_permission_required
)
from .base import LoginRequiredMixin, AdminRequiredMixin


@login_required
@permission_required([CanManageUsers])
def user_list(request):
    """Vue pour la liste des utilisateurs"""
    users = User.objects.select_related('profile').order_by('username')
    
    # Filtrage
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(profile__role=role_filter)
    
    centre_filter = request.GET.get('centre', '')
    if centre_filter:
        users = users.filter(profile__centres__id=centre_filter).distinct()
    
    search_query = request.GET.get('q', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(users, 25)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)
    
    # Récupérer les centres pour le filtre
    centres = Centre.objects.all()
    
    context = {
        'users': page_obj,
        'page_obj': page_obj,
        'centres': centres,
        'role_choices': Profile.ROLE_CHOICES,
    }
    
    return render(request, 'hospital/users/list.html', context)


@login_required
@permission_required([CanManageUsers])
def user_detail(request, user_id):
    """Vue pour le détail d'un utilisateur"""
    user = get_object_or_404(
        User.objects.select_related('profile'),
        id=user_id
    )
    
    return render(request, 'hospital/users/detail.html', {'user_obj': user})


@login_required
@permission_required([CanManageUsers])
def create_user(request):
    """Vue pour créer un nouvel utilisateur"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Créer l'utilisateur
            new_user = form.save()
            
            # Créer le profil
            role = request.POST.get('role', 'NURSE')
            profile = Profile.objects.create(
                user=new_user,
                role=role
            )
            
            # Ajouter les centres si spécifiés
            centres_ids = request.POST.getlist('centres')
            if centres_ids:
                profile.centres.set(centres_ids)
            
            messages.success(request, f"L'utilisateur {new_user.username} a été créé avec succès.")
            return redirect('user_detail', user_id=new_user.id)
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = UserRegistrationForm()
    
    # Récupérer les centres pour le formulaire
    centres = Centre.objects.all()
    
    context = {
        'form': form,
        'centres': centres,
        'role_choices': Profile.ROLE_CHOICES,
        'action': 'create',
    }
    
    return render(request, 'hospital/users/form.html', context)


@login_required
@permission_required([CanManageUsers])
def edit_user(request, user_id):
    """Vue pour modifier un utilisateur"""
    user_obj = get_object_or_404(
        User.objects.select_related('profile'),
        id=user_id
    )
    
    if request.method == 'POST':
        # Mettre à jour les informations de base
        user_obj.first_name = request.POST.get('first_name', '')
        user_obj.last_name = request.POST.get('last_name', '')
        user_obj.email = request.POST.get('email', '')
        
        # Mettre à jour le mot de passe si fourni
        password = request.POST.get('password', '')
        if password:
            user_obj.set_password(password)
        
        user_obj.save()
        
        # Mettre à jour le profil
        profile = user_obj.profile
        profile.role = request.POST.get('role', profile.role)
        profile.save()
        
        # Mettre à jour les centres
        centres_ids = request.POST.getlist('centres')
        if centres_ids:
            profile.centres.set(centres_ids)
        else:
            profile.centres.clear()
        
        messages.success(request, f"L'utilisateur {user_obj.username} a été mis à jour avec succès.")
        return redirect('user_detail', user_id=user_obj.id)
    else:
        # Pré-remplir le formulaire
        form_data = {
            'username': user_obj.username,
            'first_name': user_obj.first_name,
            'last_name': user_obj.last_name,
            'email': user_obj.email,
            'role': user_obj.profile.role,
        }
        
        # Récupérer les centres pour le formulaire
        centres = Centre.objects.all()
        user_centres = user_obj.profile.centres.all()
        
        context = {
            'form_data': form_data,
            'user_obj': user_obj,
            'centres': centres,
            'user_centres': user_centres,
            'role_choices': Profile.ROLE_CHOICES,
            'action': 'edit',
        }
        
        return render(request, 'hospital/users/form.html', context)


@login_required
@permission_required([CanManageUsers])
def delete_user(request, user_id):
    """Vue pour supprimer un utilisateur"""
    user_obj = get_object_or_404(User, id=user_id)
    
    # Empêcher la suppression de son propre compte
    if user_obj == request.user:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
        return redirect('user_detail', user_id=user_obj.id)
    
    if request.method == 'POST':
        username = user_obj.username
        user_obj.delete()
        messages.success(request, f"L'utilisateur {username} a été supprimé avec succès.")
        return redirect('user_list')
    
    return render(request, 'hospital/users/delete_confirm.html', {'user_obj': user_obj})


@login_required
@permission_required([CanManageUsers])
def toggle_user_status(request, user_id):
    """Vue pour activer/désactiver un utilisateur"""
    user_obj = get_object_or_404(User, id=user_id)
    
    # Empêcher la désactivation de son propre compte
    if user_obj == request.user:
        messages.error(request, "Vous ne pouvez pas désactiver votre propre compte.")
        return redirect('user_detail', user_id=user_obj.id)
    
    if request.method == 'POST':
        # Inverser le statut actif
        user_obj.is_active = not user_obj.is_active
        user_obj.save()
        
        status = "activé" if user_obj.is_active else "désactivé"
        messages.success(request, f"L'utilisateur {user_obj.username} a été {status} avec succès.")
        
        return redirect('user_detail', user_id=user_obj.id)
    
    return render(request, 'hospital/users/toggle_status.html', {'user_obj': user_obj})


@login_required
@permission_required([CanManageUsers])
def reset_user_password(request, user_id):
    """Vue pour réinitialiser le mot de passe d'un utilisateur"""
    user_obj = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Générer un mot de passe temporaire
        import secrets
        import string
        temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        
        # Mettre à jour le mot de passe
        user_obj.set_password(temp_password)
        user_obj.save()
        
        messages.success(request, f"Le mot de passe de {user_obj.username} a été réinitialisé. Nouveau mot de passe : {temp_password}")
        return redirect('user_detail', user_id=user_obj.id)
    
    return render(request, 'hospital/users/reset_password.html', {'user_obj': user_obj})


@login_required
def my_profile(request):
    """Vue pour le profil de l'utilisateur connecté"""
    user_obj = request.user
    
    if request.method == 'POST':
        # Mettre à jour les informations de base
        user_obj.first_name = request.POST.get('first_name', '')
        user_obj.last_name = request.POST.get('last_name', '')
        user_obj.email = request.POST.get('email', '')
        user_obj.save()
        
        messages.success(request, "Votre profil a été mis à jour avec succès.")
        return redirect('my_profile')
    
    return render(request, 'hospital/users/my_profile.html', {'user_obj': user_obj})


@login_required
def change_my_password(request):
    """Vue pour changer son propre mot de passe"""
    user_obj = request.user
    
    if request.method == 'POST':
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        # Vérifier le mot de passe actuel
        if not user_obj.check_password(current_password):
            messages.error(request, "Le mot de passe actuel est incorrect.")
            return redirect('change_my_password')
        
        # Vérifier que les nouveaux mots de passe correspondent
        if new_password != confirm_password:
            messages.error(request, "Les nouveaux mots de passe ne correspondent pas.")
            return redirect('change_my_password')
        
        # Mettre à jour le mot de passe
        user_obj.set_password(new_password)
        user_obj.save()
        
        messages.success(request, "Votre mot de passe a été changé avec succès.")
        return redirect('my_profile')
    
    return render(request, 'hospital/users/change_password.html', {'user_obj': user_obj})


@login_required
@permission_required([CanManageUsers])
def search_users(request):
    """Vue pour rechercher des utilisateurs"""
    query = request.GET.get('q', '')
    page = request.GET.get('page', 1)
    
    if not query:
        return JsonResponse({'error': 'Veuillez entrer un terme de recherche.'})
    
    # Filtrer par la requête de recherche
    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query)
    ).select_related('profile').order_by('username')
    
    # Pagination
    paginator = Paginator(users, 25)
    page_obj = paginator.get_page(page)
    
    # Si c'est une requête HTMX, retourner le HTML
    if request.headers.get('HX-Request'):
        context = {
            'users': page_obj,
            'page_obj': page_obj,
        }
        html = render_to_string('hospital/partials/users_list.html', context, request)
        return JsonResponse({'html': html})
    
    # Sinon, retourner JSON
    users_data = []
    for user_obj in page_obj:
        users_data.append({
            'id': user_obj.id,
            'username': user_obj.username,
            'first_name': user_obj.first_name,
            'last_name': user_obj.last_name,
            'email': user_obj.email,
            'role': user_obj.profile.get_role_display(),
            'is_active': user_obj.is_active,
        })
    
    return JsonResponse({
        'users': users_data,
        'pagination': {
            'current_page': page,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
        }
    })


@login_required
@permission_required([CanManageUsers])
def get_users_partial(request):
    """Vue partielle pour la liste des utilisateurs via HTMX"""
    users = User.objects.select_related('profile').order_by('username')
    
    # Filtrage
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(profile__role=role_filter)
    
    centre_filter = request.GET.get('centre', '')
    if centre_filter:
        users = users.filter(profile__centres__id=centre_filter).distinct()
    
    # Pagination
    paginator = Paginator(users, 25)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)
    
    context = {
        'users': page_obj,
        'page_obj': page_obj,
    }
    
    html = render_to_string('hospital/partials/users_list.html', context, request)
    return JsonResponse({'html': html})


@login_required
@permission_required([CanManageUsers])
def user_statistics(request):
    """Vue pour les statistiques des utilisateurs"""
    # Statistiques par rôle
    role_stats = {}
    for role, display in Profile.ROLE_CHOICES:
        count = User.objects.filter(profile__role=role).count()
        role_stats[role] = {
            'display': display,
            'count': count,
        }
    
    # Statistiques par centre
    centre_stats = []
    for centre in Centre.objects.all():
        count = Profile.objects.filter(centres=centre).count()
        if count > 0:
            centre_stats.append({
                'centre': centre.name,
                'count': count,
            })
    
    # Statistiques générales
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = total_users - active_users
    
    context = {
        'role_stats': role_stats,
        'centre_stats': centre_stats,
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
    }
    
    return render(request, 'hospital/users/statistics.html', context)