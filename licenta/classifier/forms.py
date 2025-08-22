from django import forms
from .models import PatientSession

class PatientSessionForm(forms.ModelForm):
    class Meta:
        model = PatientSession
        fields = ['name']
        labels = {
            'name': 'Nume Pacient',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nume Pacient'}),
        }
