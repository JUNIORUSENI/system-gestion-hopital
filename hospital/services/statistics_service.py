"""
Service pour les statistiques et les rapports
"""
from django.db.models import Count, Q
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta, date
try:
    from dateutil.relativedelta import relativedelta
except ImportError:
    relativedelta = None
from ..models import Patient, Consultation, Hospitalisation, Emergency, Appointment, User, Centre


class StatisticsService:
    """Service pour les statistiques avec cache"""
    
    def __init__(self):
        self.cache_timeout = 3600  # 1 heure
    
    def get_dashboard_statistics(self, user, use_cache=True):
        """
        Récupérer les statistiques pour le dashboard selon le rôle de l'utilisateur
        """
        cache_key = f'dashboard_stats_{user.id}_{user.profile.role}'
        
        if use_cache:
            cached_stats = cache.get(cache_key)
            if cached_stats:
                return cached_stats
        
        role = user.profile.role
        
        # Statistiques de base selon le rôle
        if role in ['ADMIN', 'MEDICAL_ADMIN']:
            stats = self._get_admin_statistics()
        elif role == 'DOCTOR':
            stats = self._get_doctor_statistics(user)
        elif role == 'SECRETARY':
            stats = self._get_secretary_statistics(user)
        elif role == 'NURSE':
            stats = self._get_nurse_statistics(user)
        else:
            stats = {}
        
        if use_cache:
            cache.set(cache_key, stats, self.cache_timeout)
        
        return stats
    
    def get_patient_statistics(self, user, use_cache=True):
        """
        Récupérer les statistiques des patients
        """
        cache_key = f'patient_stats_{user.id}_{user.profile.role}'
        
        if use_cache:
            cached_stats = cache.get(cache_key)
            if cached_stats:
                return cached_stats
        
        role = user.profile.role
        
        # Définir le queryset de base selon le rôle
        if role in ['ADMIN', 'MEDICAL_ADMIN']:
            base_patient_qs = Patient.objects.all()
        elif role == 'DOCTOR':
            base_patient_qs = Patient.objects.filter(
                consultations__doctor=user
            ).distinct()
        elif role == 'SECRETARY':
            base_patient_qs = Patient.objects.filter(
                default_centre__in=user.profile.centres.all()
            )
        elif role == 'NURSE':
            # Les infirmiers voient les patients hospitalisés dans leurs centres
            patient_ids = Hospitalisation.objects.filter(
                centre__in=user.profile.centres.all()
            ).values_list('patient_id', flat=True).distinct()
            base_patient_qs = Patient.objects.filter(id__in=patient_ids)
        else:
            base_patient_qs = Patient.objects.none()
        
        # Calculer les statistiques
        stats = {
            'total_patients': base_patient_qs.count(),
            'patients_by_gender': self._get_patients_by_gender(base_patient_qs),
            'patients_by_age': self._get_patients_by_age(base_patient_qs),
            'patients_by_centre': self._get_patients_by_centre(base_patient_qs, user),
            'new_patients_this_month': self._get_new_patients_this_month(base_patient_qs),
        }
        
        if use_cache:
            cache.set(cache_key, stats, self.cache_timeout)
        
        return stats
    
    def get_consultation_statistics(self, user, use_cache=True):
        """
        Récupérer les statistiques des consultations
        """
        cache_key = f'consultation_stats_{user.id}_{user.profile.role}'
        
        if use_cache:
            cached_stats = cache.get(cache_key)
            if cached_stats:
                return cached_stats
        
        role = user.profile.role
        
        # Définir le queryset de base selon le rôle
        if role in ['ADMIN', 'MEDICAL_ADMIN']:
            base_consultation_qs = Consultation.objects.all()
        elif role == 'DOCTOR':
            base_consultation_qs = Consultation.objects.filter(doctor=user)
        elif role in ['SECRETARY', 'NURSE']:
            base_consultation_qs = Consultation.objects.filter(
                patient__default_centre__in=user.profile.centres.all()
            )
        else:
            base_consultation_qs = Consultation.objects.none()
        
        # Calculer les statistiques
        stats = {
            'total_consultations': base_consultation_qs.count(),
            'consultations_by_status': self._get_consultations_by_status(base_consultation_qs),
            'consultations_by_month': self._get_consultations_by_month(base_consultation_qs, 6),
            'consultations_this_month': self._get_consultations_this_month(base_consultation_qs),
            'consultations_by_doctor': self._get_consultations_by_doctor(base_consultation_qs, user),
        }
        
        if use_cache:
            cache.set(cache_key, stats, self.cache_timeout)
        
        return stats
    
    def get_hospitalisation_statistics(self, user, use_cache=True):
        """
        Récupérer les statistiques des hospitalisations
        """
        cache_key = f'hospitalisation_stats_{user.id}_{user.profile.role}'
        
        if use_cache:
            cached_stats = cache.get(cache_key)
            if cached_stats:
                return cached_stats
        
        role = user.profile.role
        
        # Définir le queryset de base selon le rôle
        if role in ['ADMIN', 'MEDICAL_ADMIN']:
            base_hospitalisation_qs = Hospitalisation.objects.all()
        elif role == 'DOCTOR':
            base_hospitalisation_qs = Hospitalisation.objects.filter(doctor=user)
        elif role in ['SECRETARY', 'NURSE']:
            base_hospitalisation_qs = Hospitalisation.objects.filter(
                centre__in=user.profile.centres.all()
            )
        else:
            base_hospitalisation_qs = Hospitalisation.objects.none()
        
        # Calculer les statistiques
        stats = {
            'total_hospitalisations': base_hospitalisation_qs.count(),
            'active_hospitalisations': base_hospitalisation_qs.filter(discharge_date__isnull=True).count(),
            'hospitalisations_by_service': self._get_hospitalisations_by_service(base_hospitalisation_qs),
            'average_stay_duration': self._get_average_stay_duration(base_hospitalisation_qs),
            'hospitalisations_this_month': self._get_hospitalisations_this_month(base_hospitalisation_qs),
        }
        
        if use_cache:
            cache.set(cache_key, stats, self.cache_timeout)
        
        return stats
    
    def get_emergency_statistics(self, user, use_cache=True):
        """
        Récupérer les statistiques des urgences
        """
        cache_key = f'emergency_stats_{user.id}_{user.profile.role}'
        
        if use_cache:
            cached_stats = cache.get(cache_key)
            if cached_stats:
                return cached_stats
        
        role = user.profile.role
        
        # Définir le queryset de base selon le rôle
        if role in ['ADMIN', 'MEDICAL_ADMIN']:
            base_emergency_qs = Emergency.objects.all()
        elif role == 'DOCTOR':
            base_emergency_qs = Emergency.objects.filter(doctor=user)
        elif role in ['SECRETARY', 'NURSE']:
            base_emergency_qs = Emergency.objects.filter(
                centre__in=user.profile.centres.all()
            )
        else:
            base_emergency_qs = Emergency.objects.none()
        
        # Calculer les statistiques
        stats = {
            'total_emergencies': base_emergency_qs.count(),
            'emergencies_by_level': self._get_emergencies_by_level(base_emergency_qs),
            'emergencies_by_orientation': self._get_emergencies_by_orientation(base_emergency_qs),
            'emergencies_this_month': self._get_emergencies_this_month(base_emergency_qs),
            'emergencies_by_hour': self._get_emergencies_by_hour(base_emergency_qs),
        }
        
        if use_cache:
            cache.set(cache_key, stats, self.cache_timeout)
        
        return stats
    
    def _get_admin_statistics(self):
        """Statistiques pour les administrateurs"""
        return {
            'total_patients': Patient.objects.count(),
            'total_consultations': Consultation.objects.count(),
            'total_hospitalisations': Hospitalisation.objects.count(),
            'total_emergencies': Emergency.objects.count(),
            'total_appointments': Appointment.objects.count(),
            'total_users': User.objects.count(),
            'total_centres': Centre.objects.count(),
            'total_doctors': User.objects.filter(profile__role='DOCTOR').count(),
            'total_nurses': User.objects.filter(profile__role='NURSE').count(),
            'total_secretaries': User.objects.filter(profile__role='SECRETARY').count(),
        }
    
    def _get_doctor_statistics(self, user):
        """Statistiques pour les médecins"""
        return {
            'total_patients': Patient.objects.filter(
                consultations__doctor=user
            ).distinct().count(),
            'total_consultations': Consultation.objects.filter(doctor=user).count(),
            'total_hospitalisations': Hospitalisation.objects.filter(doctor=user).count(),
            'total_emergencies': Emergency.objects.filter(doctor=user).count(),
            'total_appointments': Appointment.objects.filter(doctor=user).count(),
            'pending_consultations': Consultation.objects.filter(
                doctor=user, status='PENDING'
            ).count(),
            'upcoming_appointments': Appointment.objects.filter(
                doctor=user, 
                date__gte=timezone.now(),
                status__in=['SCHEDULED', 'CONFIRMED']
            ).count(),
        }
    
    def _get_secretary_statistics(self, user):
        """Statistiques pour les secrétaires"""
        centres = user.profile.centres.all()
        return {
            'total_patients': Patient.objects.filter(
                default_centre__in=centres
            ).count(),
            'total_consultations': Consultation.objects.filter(
                centre__in=centres
            ).count(),
            'total_hospitalisations': Hospitalisation.objects.filter(
                centre__in=centres
            ).count(),
            'total_emergencies': Emergency.objects.filter(
                centre__in=centres
            ).count(),
            'total_appointments': Appointment.objects.filter(
                centre__in=centres
            ).count(),
            'today_appointments': Appointment.objects.filter(
                centre__in=centres,
                date__date=timezone.now().date()
            ).count(),
        }
    
    def _get_nurse_statistics(self, user):
        """Statistiques pour les infirmiers"""
        centres = user.profile.centres.all()
        active_hospitalisations = Hospitalisation.objects.filter(
            centre__in=centres,
            discharge_date__isnull=True
        ).select_related('patient')
        
        return {
            'total_patients': active_hospitalisations.count(),
            'total_hospitalisations': Hospitalisation.objects.filter(
                centre__in=centres
            ).count(),
            'total_emergencies': Emergency.objects.filter(
                centre__in=centres
            ).count(),
            'active_hospitalisations': active_hospitalisations.count(),
            'patients_in_my_care': list(active_hospitalisations),
        }
    
    def _get_patients_by_gender(self, queryset):
        """Répartition des patients par genre"""
        genders = ['M', 'F']
        gender_counts = (
            queryset
            .filter(gender__in=genders)
            .values('gender')
            .annotate(count=Count('id'))
            .order_by()
        )
        gender_map = {item['gender']: item['count'] for item in gender_counts}
        return {gender: gender_map.get(gender, 0) for gender in genders}
    
    def _get_patients_by_age(self, queryset):
        """Répartition des patients par tranche d'âge"""
        today = timezone.now().date()
        age_ranges = [
            ('0-17', Q(date_of_birth__gt=today - relativedelta(years=18))),
            ('18-25', Q(date_of_birth__lte=today - relativedelta(years=18)) & Q(date_of_birth__gt=today - relativedelta(years=26))),
            ('26-40', Q(date_of_birth__lte=today - relativedelta(years=26)) & Q(date_of_birth__gt=today - relativedelta(years=41))),
            ('41-60', Q(date_of_birth__lte=today - relativedelta(years=41)) & Q(date_of_birth__gt=today - relativedelta(years=61))),
            ('60+', Q(date_of_birth__lte=today - relativedelta(years=61))),
        ]
        
        age_stats = {}
        for range_name, condition in age_ranges:
            age_stats[range_name] = queryset.filter(condition).count()
        
        return age_stats
    
    def _get_patients_by_centre(self, queryset, user):
        """Répartition des patients par centre"""
        if user.profile.role in ['ADMIN', 'MEDICAL_ADMIN']:
            centres = Centre.objects.all()
        else:
            centres = user.profile.centres.all()
        
        centre_stats = []
        for centre in centres:
            count = queryset.filter(default_centre=centre).count()
            if count > 0:
                centre_stats.append({
                    'centre': centre.name,
                    'count': count
                })
        
        return centre_stats
    
    def _get_new_patients_this_month(self, queryset):
        """Nouveaux patients ce mois"""
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return queryset.filter(created_at__gte=month_start).count()
    
    def _get_consultations_by_status(self, queryset):
        """Répartition des consultations par statut"""
        statuses = ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']
        status_counts = (
            queryset
            .filter(status__in=statuses)
            .values('status')
            .annotate(count=Count('id'))
            .order_by()
        )
        status_map = {item['status']: item['count'] for item in status_counts}
        return {status: status_map.get(status, 0) for status in statuses}
    
    def _get_consultations_by_month(self, queryset, months=6):
        """Consultations par mois"""
        consultations_by_month = []
        today = timezone.now().date()
        
        for i in range(months):
            month_start = (today.replace(day=1) - relativedelta(months=i))
            month_end = (today.replace(day=1) - relativedelta(months=i-1))
            
            count = queryset.filter(
                date__gte=month_start,
                date__lt=month_end
            ).count()
            
            consultations_by_month.append({
                'month': month_start.strftime('%b %Y'),
                'count': count
            })
        
        consultations_by_month.reverse()  # Ordre chronologique
        return consultations_by_month
    
    def _get_consultations_this_month(self, queryset):
        """Consultations ce mois"""
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return queryset.filter(date__gte=month_start).count()
    
    def _get_consultations_by_doctor(self, queryset, user):
        """Consultations par médecin (pour admin uniquement)"""
        if user.profile.role not in ['ADMIN', 'MEDICAL_ADMIN']:
            return []
        
        doctor_counts = (
            queryset
            .values('doctor__username', 'doctor__first_name', 'doctor__last_name')
            .annotate(count=Count('id'))
            .filter(count__gt=0)
            .order_by('-count')[:10]
        )
        
        result = []
        for item in doctor_counts:
            full_name = f"{item['doctor__first_name']} {item['doctor__last_name']}".strip()
            result.append({
                'doctor': full_name or item['doctor__username'],
                'count': item['count']
            })
        
        return result
    
    def _get_hospitalisations_by_service(self, queryset):
        """Hospitalisations par service"""
        service_counts = (
            queryset
            .exclude(service__isnull=True)
            .exclude(service__exact='')
            .values('service')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        
        return list(service_counts)
    
    def _get_average_stay_duration(self, queryset):
        """Durée moyenne d'hospitalisation"""
        completed_stays = queryset.filter(discharge_date__isnull=False)
        
        if not completed_stays.exists():
            return 0
        
        total_duration = timedelta()
        for hospitalisation in completed_stays:
            duration = hospitalisation.discharge_date - hospitalisation.admission_date
            total_duration += duration
        
        return total_duration.total_seconds() / (len(completed_stays) * 24 * 3600)  # En jours
    
    def _get_hospitalisations_this_month(self, queryset):
        """Hospitalisations ce mois"""
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return queryset.filter(admission_date__gte=month_start).count()
    
    def _get_emergencies_by_level(self, queryset):
        """Urgences par niveau"""
        levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        level_counts = (
            queryset
            .filter(triage_level__in=levels)
            .values('triage_level')
            .annotate(count=Count('id'))
            .order_by()
        )
        level_map = {item['triage_level']: item['count'] for item in level_counts}
        return {level: level_map.get(level, 0) for level in levels}
    
    def _get_emergencies_by_orientation(self, queryset):
        """Urgences par orientation"""
        orientations = ['DISCHARGED', 'HOSPITALISED', 'TRANSFERRED']
        orientation_counts = (
            queryset
            .filter(orientation__in=orientations)
            .values('orientation')
            .annotate(count=Count('id'))
            .order_by()
        )
        orientation_map = {item['orientation']: item['count'] for item in orientation_counts}
        return {orientation: orientation_map.get(orientation, 0) for orientation in orientations}
    
    def _get_emergencies_this_month(self, queryset):
        """Urgences ce mois"""
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return queryset.filter(admission_time__gte=month_start).count()
    
    def _get_emergencies_by_hour(self, queryset):
        """Urgences par heure de la journée"""
        hour_counts = (
            queryset
            .extra({'hour': "strftime('%%H', admission_time)"})
            .values('hour')
            .annotate(count=Count('id'))
            .order_by('hour')
        )
        
        return list(hour_counts)
    
    def invalidate_statistics_cache(self, user=None):
        """
        Invalider le cache des statistiques
        """
        if user:
            # Invalider le cache pour un utilisateur spécifique
            cache_keys = [
                f'dashboard_stats_{user.id}_{user.profile.role}',
                f'patient_stats_{user.id}_{user.profile.role}',
                f'consultation_stats_{user.id}_{user.profile.role}',
                f'hospitalisation_stats_{user.id}_{user.profile.role}',
                f'emergency_stats_{user.id}_{user.profile.role}',
            ]
            for key in cache_keys:
                cache.delete(key)
        else:
            # Invalider tout le cache des statistiques (pour les changements globaux)
            # Note: cette approche est simplifiée, une implémentation complète
            # nécessiterait de suivre toutes les clés de cache actives
            pass