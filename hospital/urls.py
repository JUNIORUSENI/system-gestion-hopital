from django.urls import path
from django.contrib.auth.views import LoginView
from . import views

# Importer les vues modulaires
from .views.base import (
    dashboard, custom_logout, statistics_view, doctor_dashboard,
    medical_admin_dashboard, get_patients_partial, register
)
from .views.patients_views import (
    patient_list, patient_detail, create_patient_form, edit_patient,
    delete_patient, orient_patient, search_patients, generate_document,
    print_document, refresh_patients_list
)
from .views.consultations_views import (
    consultation_list, consultation_detail, consultation_create,
    consultation_edit, consultation_delete
)
from .views.hospitalisations_views import (
    hospitalisation_list, hospitalisation_detail, hospitalisation_create,
    hospitalisation_edit, hospitalisation_delete, hospitalisation_discharge
)
from .views.emergencies_views import (
    emergency_list, emergency_detail, emergency_create, emergency_edit,
    emergency_delete, emergency_triage
)
from .views.appointments_views import (
    appointment_list, appointment_create, appointment_edit,
    appointment_delete, appointment_toggle_status
)
# from .views.users_views import (
#     user_list, user_detail, create_user, edit_user, delete_user,
#     toggle_user_status, reset_user_password, my_profile, change_my_password,
#     search_users, get_users_partial, user_statistics
# )
# from .views.centres_views import (
#     centre_list, centre_detail, create_centre, edit_centre, delete_centre,
#     centre_staff, add_staff_to_centre, remove_staff_from_centre, centre_patients,
#     centre_statistics, search_centres, get_centres_partial, centre_dashboard
# )

urlpatterns = [
    # Accueil et dashboard
    path('', dashboard, name='dashboard'),
    path('welcome/', dashboard, name='welcome'),
    path('login/', LoginView.as_view(template_name='hospital/registration/login.html'), name='login'),
    path('logout/', custom_logout, name='logout'),
    path('register/', register, name='register'),
    path('doctor-dashboard/', doctor_dashboard, name='doctor_dashboard'),
    
    # Gestion des patients
    path('patients/', patient_list, name='patient_list'),
    path('patients/<int:patient_id>/', patient_detail, name='patient_detail'),
    path('patients/create/', create_patient_form, name='create_patient_form'),
    path('patients/<int:patient_id>/edit/', edit_patient, name='edit_patient'),
    path('patients/<int:patient_id>/delete/', delete_patient, name='delete_patient'),
    path('patients/<int:patient_id>/orient/', orient_patient, name='orient_patient'),
    path('patients/<int:patient_id>/document/<str:doc_type>/', generate_document, name='generate_document'),
    path('patients/<int:patient_id>/print/<str:doc_type>/', print_document, name='print_document'),
    path('patients/refresh/', refresh_patients_list, name='refresh_patients_list'),
    
    # Gestion des consultations
    path('consultations/', consultation_list, name='consultation_list'),
    path('consultations/create/', consultation_create, name='consultation_create'),
    path('consultations/<int:consultation_id>/', consultation_detail, name='consultation_detail'),
    path('consultations/<int:consultation_id>/edit/', consultation_edit, name='consultation_edit'),
    path('consultations/<int:consultation_id>/delete/', consultation_delete, name='consultation_delete'),
    
    # Gestion des hospitalisations
    path('hospitalisations/', hospitalisation_list, name='hospitalisation_list'),
    path('hospitalisations/create/', hospitalisation_create, name='hospitalisation_create'),
    path('hospitalisations/<int:hospitalisation_id>/', hospitalisation_detail, name='hospitalisation_detail'),
    path('hospitalisations/<int:hospitalisation_id>/edit/', hospitalisation_edit, name='hospitalisation_edit'),
    path('hospitalisations/<int:hospitalisation_id>/discharge/', hospitalisation_discharge, name='hospitalisation_discharge'),
    path('hospitalisations/<int:hospitalisation_id>/delete/', hospitalisation_delete, name='hospitalisation_delete'),
    
    # Gestion des urgences
    path('emergencies/', emergency_list, name='emergency_list'),
    path('emergencies/create/', emergency_create, name='emergency_create'),
    path('emergencies/<int:emergency_id>/', emergency_detail, name='emergency_detail'),
    path('emergencies/<int:emergency_id>/edit/', emergency_edit, name='emergency_edit'),
    path('emergencies/<int:emergency_id>/triage/', emergency_triage, name='emergency_triage'),
    path('emergencies/<int:emergency_id>/delete/', emergency_delete, name='emergency_delete'),
    
    # Gestion des rendez-vous
    path('appointments/', appointment_list, name='appointment_list'),
    path('appointments/create/', appointment_create, name='appointment_create'),
    path('appointments/<int:appointment_id>/edit/', appointment_edit, name='appointment_edit'),
    path('appointments/<int:appointment_id>/delete/', appointment_delete, name='appointment_delete'),
    path('appointments/<int:appointment_id>/toggle-status/', appointment_toggle_status, name='appointment_toggle_status'),
    
    # Gestion des utilisateurs (Admin) - À implémenter plus tard
    # path('users/', user_list, name='user_list'),
    # path('users/create/', create_user, name='user_create'),
    # path('users/<int:user_id>/', user_detail, name='user_detail'),
    # path('users/<int:user_id>/edit/', edit_user, name='user_edit'),
    # path('users/<int:user_id>/delete/', delete_user, name='user_delete'),
    # path('users/<int:user_id>/toggle-status/', toggle_user_status, name='user_toggle_status'),
    # path('users/<int:user_id>/reset-password/', reset_user_password, name='user_reset_password'),
    # path('users/statistics/', user_statistics, name='user_statistics'),
    # path('users/my-profile/', my_profile, name='my_profile'),
    # path('users/change-password/', change_my_password, name='change_my_password'),
    
    # Gestion des centres (Admin) - À implémenter plus tard
    # path('centres/', centre_list, name='centre_list'),
    # path('centres/create/', create_centre, name='centre_create'),
    # path('centres/<int:centre_id>/', centre_detail, name='centre_detail'),
    # path('centres/<int:centre_id>/edit/', edit_centre, name='centre_edit'),
    # path('centres/<int:centre_id>/delete/', delete_centre, name='centre_delete'),
    # path('centres/<int:centre_id>/staff/', centre_staff, name='centre_staff'),
    # path('centres/<int:centre_id>/staff/add/', add_staff_to_centre, name='add_staff_to_centre'),
    # path('centres/<int:centre_id>/staff/<int:user_id>/remove/', remove_staff_from_centre, name='remove_staff_from_centre'),
    # path('centres/<int:centre_id>/patients/', centre_patients, name='centre_patients'),
    # path('centres/<int:centre_id>/statistics/', centre_statistics, name='centre_statistics'),
    # path('centres/<int:centre_id>/dashboard/', centre_dashboard, name='centre_dashboard'),
    
    # Vues partielles pour HTMX - À implémenter plus tard
    # path('patients/partial/', get_patients_partial, name='get_patients_partial'),
    # path('patients/search/', search_patients, name='search_patients'),
    # path('consultations/partial/', get_consultations_partial, name='get_consultations_partial'),
    # path('consultations/search/', search_consultations, name='search_consultations'),
    # path('hospitalisations/partial/', get_hospitalisations_partial, name='get_hospitalisations_partial'),
    # path('hospitalisations/search/', search_hospitalisations, name='search_hospitalisations'),
    # path('hospitalisations/active/', get_active_hospitalisations, name='get_active_hospitalisations'),
    # path('emergencies/partial/', get_emergencies_partial, name='get_emergencies_partial'),
    # path('emergencies/search/', search_emergencies, name='search_emergencies'),
    # path('emergencies/pending-triage/', get_pending_triage_emergencies, name='get_pending_triage_emergencies'),
    # path('appointments/partial/', get_appointments_partial, name='get_appointments_partial'),
    # path('appointments/search/', search_appointments, name='search_appointments'),
    # path('users/partial/', get_users_partial, name='get_users_partial'),
    # path('users/search/', search_users, name='search_users'),
    # path('centres/partial/', get_centres_partial, name='get_centres_partial'),
    # path('centres/search/', search_centres, name='search_centres'),
    
    # Page de statistiques
    path('statistics/', statistics_view, name='statistics'),
    
    # Dashboard Médecin Administrateur
    path('medical-admin-dashboard/', medical_admin_dashboard, name='medical_admin_dashboard'),
    
    # Exportations
    # path('export/hospitalisations/csv/', views.export_hospitalisations_csv, name='export_hospitalisations_csv'),
]