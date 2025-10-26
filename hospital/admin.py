from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Patient, Consultation, Hospitalisation, Emergency, Centre, Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profils'


class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)


class PatientAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'date_of_birth', 'gender', 'phone', 'default_centre')
    list_filter = ('gender', 'default_centre')
    search_fields = ('last_name', 'first_name', 'phone')
    ordering = ('last_name', 'first_name')


class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'date', 'centre', 'reason')
    list_filter = ('date', 'centre', 'doctor')
    search_fields = ('patient__last_name', 'patient__first_name', 'reason')
    ordering = ('-date',)


class HospitalisationAdmin(admin.ModelAdmin):
    list_display = ('patient', 'admission_date', 'service', 'room', 'doctor')
    list_filter = ('admission_date', 'service', 'doctor')
    search_fields = ('patient__last_name', 'patient__first_name', 'service')
    ordering = ('-admission_date',)


class EmergencyAdmin(admin.ModelAdmin):
    list_display = ('patient', 'admission_time', 'triage_level', 'doctor', 'orientation')
    list_filter = ('triage_level', 'admission_time', 'doctor', 'orientation')
    search_fields = ('patient__last_name', 'patient__first_name')
    ordering = ('-admission_time',)


class CentreAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'address')
    search_fields = ('name', 'address')
    ordering = ('name',)


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name')


# Enregistrement des modèles
admin.site.register(Patient, PatientAdmin)
admin.site.register(Consultation, ConsultationAdmin)
admin.site.register(Hospitalisation, HospitalisationAdmin)
admin.site.register(Emergency, EmergencyAdmin)
admin.site.register(Centre, CentreAdmin)
admin.site.register(Profile, ProfileAdmin)

# Désenregistrement de l'admin par défaut et enregistrement du nôtre
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)