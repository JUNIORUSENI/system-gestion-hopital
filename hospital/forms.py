from datetime import date

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

from .models import Patient, Consultation, Hospitalisation, Emergency, Centre, Appointment


# Validateur pour numéro de téléphone congolais (même que dans models.py)
phone_validator = RegexValidator(
    regex=r'^\+?243[0-9]{9}$|^0[0-9]{9}$',
    message="Format congolais requis : +243XXXXXXXXX ou 0XXXXXXXXX"
)


class PatientForm(forms.ModelForm):
    # Redéfinir certains champs pour ajouter des validations
    phone = forms.CharField(
        max_length=20,
        required=False,
        validators=[phone_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+243XXXXXXXXX ou 0XXXXXXXXX'
        }),
        help_text="Format : +243XXXXXXXXX ou 0XXXXXXXXX"
    )
    
    emergency_contact = forms.CharField(
        max_length=20,
        required=False,
        validators=[phone_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+243XXXXXXXXX ou 0XXXXXXXXX'
        }),
        help_text="Format : +243XXXXXXXXX ou 0XXXXXXXXX"
    )
    
    class Meta:
        model = Patient
        fields = [
            'first_name', 'postname', 'last_name', 'date_of_birth', 'gender',
            'phone', 'address', 'emergency_contact', 'is_subscriber',
            'default_centre', 'medical_history', 'allergies',
            'vaccinations', 'lifestyle'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'max': date.today().isoformat()  # Ne pas permettre date future
            }),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'postname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optionnel'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'is_subscriber': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'default_centre': forms.Select(attrs={'class': 'form-select'}),
            'medical_history': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Antécédents médicaux du patient...'
            }),
            'allergies': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control',
                'placeholder': 'Allergies connues...'
            }),
            'vaccinations': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Historique vaccinal...'
            }),
            'lifestyle': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Mode de vie, habitudes...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Rendre certains champs obligatoires
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['date_of_birth'].required = True
        self.fields['gender'].required = True
        
        # Si l'utilisateur n'a pas les permissions médicales, supprimer les champs médicaux
        if user and hasattr(user, 'profile'):
            from .permissions import can_manage_patient_medical_data
            if not can_manage_patient_medical_data(user):
                medical_fields = ['medical_history', 'allergies', 'vaccinations', 'lifestyle']
                for field in medical_fields:
                    if field in self.fields:
                        del self.fields[field]
    
    def clean_date_of_birth(self):
        """Validation de la date de naissance"""
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            if dob > date.today():
                raise ValidationError("La date de naissance ne peut pas être dans le futur.")
            
            # Vérifier l'âge (max 120 ans)
            age = (date.today() - dob).days / 365.25
            if age > 120:
                raise ValidationError("La date de naissance n'est pas valide (âge > 120 ans).")
            if age < 0:
                raise ValidationError("La date de naissance n'est pas valide.")
        
        return dob
    
    def clean_phone(self):
        """Nettoyage et validation du téléphone"""
        phone = self.cleaned_data.get('phone')
        if phone:
            # Retirer les espaces
            phone = phone.strip().replace(' ', '')
        return phone
    
    def clean_emergency_contact(self):
        """Nettoyage et validation du contact d'urgence"""
        emergency = self.cleaned_data.get('emergency_contact')
        if emergency:
            # Retirer les espaces
            emergency = emergency.strip().replace(' ', '')
        return emergency


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