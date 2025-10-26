"""
URL configuration for hospital_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt

# Handler d'erreurs personnalisés
handler404 = 'hospital.utils.error_handlers.custom_404_handler'
handler500 = 'hospital.utils.error_handlers.custom_500_handler'


@require_GET
@csrf_exempt
def root_health_check(request):
    """
    Endpoint de santé à la racine pour les load balancers
    """
    return JsonResponse({
        'status': 'ok',
        'service': 'hospital-management',
        'version': '1.0.0',
    })


urlpatterns = [
    # Rediriger vers le dashboard de l'application hospital
    path('', include('hospital.urls')),
    
    # Endpoint de santé (pour les load balancers)
    path('health/', root_health_check, name='root_health_check'),
    
    # Admin Django
    path('admin/', admin.site.urls),
    
    # URLs de monitoring supprimées (pas besoin)
    # path('api/', include('hospital.urls_monitoring')),
]

# URLs du debug toolbar en développement
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]

# Servir les fichiers statiques et médias en développement
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
