from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Patient, Consultation, Hospitalisation, Emergency, Centre, Appointment


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            'first_name', 'postname', 'last_name', 'date_of_birth', 'gender',
            'phone', 'address', 'emergency_contact', 'is_subscriber',
            'default_centre', 'medical_history', 'allergies',
            'vaccinations', 'lifestyle'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'postname': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'default_centre': forms.Select(attrs={'class': 'form-select'}),
            'medical_history': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'allergies': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'vaccinations': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'lifestyle': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Si l'utilisateur n'a pas les permissions médicales, supprimer les champs médicaux
        if user and hasattr(user, 'profile'):
            from .permissions import can_manage_patient_medical_data
            if not can_manage_patient_medical_data(user):
                medical_fields = ['medical_history', 'allergies', 'vaccinations', 'lifestyle']
                for field in medical_fields:
                    if field in self.fields:
                        del self.fields[field]


class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = [
            'patient', 'centre', 'appointment_date', 'status', 'reason', 'clinical_exam', 
            'diagnosis', 'prescription', 'follow_up_date'
        ]
        widgets = {
            'appointment_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'follow_up_date': forms.DateInput(attrs={'type': 'date'}),
            'clinical_exam': forms.Textarea(attrs={'rows': 4}),
            'diagnosis': forms.Textarea(attrs={'rows': 3}),
            'prescription': forms.Textarea(attrs={'rows': 3}),
        }


class HospitalisationForm(forms.ModelForm):
    class Meta:
        model = Hospitalisation
        fields = [
            'patient', 'centre', 'service', 'room', 'bed', 
            'admission_reason', 'medical_notes', 'nurse_notes', 
            'interventions', 'discharge_summary'
        ]
        widgets = {
            'admission_reason': forms.Textarea(attrs={'rows': 3}),
            'medical_notes': forms.Textarea(attrs={'rows': 4}),
            'nurse_notes': forms.Textarea(attrs={'rows': 4}),
            'interventions': forms.Textarea(attrs={'rows': 4}),
            'discharge_summary': forms.Textarea(attrs={'rows': 4}),
        }


class EmergencyForm(forms.ModelForm):
    class Meta:
        model = Emergency
        fields = [
            'patient', 'centre', 'reason', 'triage_level', 
            'vital_signs', 'first_aid', 'initial_diagnosis', 
            'orientation'
        ]
        widgets = {
            'vital_signs': forms.Textarea(attrs={'rows': 3}),
            'first_aid': forms.Textarea(attrs={'rows': 3}),
            'initial_diagnosis': forms.Textarea(attrs={'rows': 3}),
        }


class CentreForm(forms.ModelForm):
    class Meta:
        model = Centre
        fields = ['name', 'address', 'phone']


class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['patient', 'doctor', 'centre', 'date', 'reason', 'duration', 'status', 'notes']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }