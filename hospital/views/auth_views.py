"""
Vues pour l'authentification des utilisateurs
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.http import JsonResponse


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