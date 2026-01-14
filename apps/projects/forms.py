"""
Formulaires Django pour LysAngels avec validation complète
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from apps.projects.models import Project, EventType
from apps.vendors.models import ServiceType
from apps.core.models import City
import datetime


class ProjectCreateForm(forms.ModelForm):
    """Formulaire de création de projet avec validation complète"""
    
    event_type = forms.ModelChoiceField(
        queryset=EventType.objects.all(),
        required=True,
        empty_label="Sélectionnez un type d'événement",
        error_messages={
            'required': 'Veuillez sélectionner un type d\'événement.',
            'invalid_choice': 'Type d\'événement invalide.',
        },
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lily-purple focus:border-transparent transition'
        })
    )
    
    services_needed = forms.ModelMultipleChoiceField(
        queryset=ServiceType.objects.all(),
        required=True,
        error_messages={
            'required': 'Veuillez sélectionner au moins un service.',
        },
        widget=forms.CheckboxSelectMultiple()
    )
    
    title = forms.CharField(
        max_length=200,
        required=True,
        error_messages={
            'required': 'Le titre du projet est obligatoire.',
            'max_length': 'Le titre ne peut pas dépasser 200 caractères.',
        },
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lily-purple focus:border-transparent transition',
            'placeholder': 'Ex: Mariage de Marie et Jean'
        })
    )
    
    description = forms.CharField(
        required=True,
        error_messages={
            'required': 'La description est obligatoire.',
        },
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lily-purple focus:border-transparent transition',
            'rows': 6,
            'placeholder': 'Décrivez votre événement, vos attentes, vos préférences...'
        })
    )
    
    city = forms.CharField(
        max_length=100,
        required=True,
        error_messages={
            'required': 'La ville est obligatoire.',
            'max_length': 'Le nom de la ville ne peut pas dépasser 100 caractères.',
        },
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lily-purple focus:border-transparent transition',
            'placeholder': 'Ex: Lomé'
        })
    )
    
    event_date = forms.DateField(
        required=True,
        error_messages={
            'required': 'La date de l\'événement est obligatoire.',
            'invalid': 'Veuillez saisir une date valide (JJ/MM/AAAA).',
        },
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lily-purple focus:border-transparent transition'
        })
    )
    
    event_time = forms.TimeField(
        required=False,
        error_messages={
            'invalid': 'Veuillez saisir une heure valide (HH:MM).',
        },
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lily-purple focus:border-transparent transition'
        })
    )
    
    location = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lily-purple focus:border-transparent transition',
            'placeholder': 'Ex: Hôtel Sarakawa, Salle des fêtes...'
        })
    )
    
    expected_attendees = forms.IntegerField(
        required=False,
        min_value=1,
        error_messages={
            'invalid': 'Veuillez saisir un nombre valide.',
            'min_value': 'Le nombre d\'invités doit être au moins 1.',
        },
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lily-purple focus:border-transparent transition',
            'placeholder': 'Ex: 100',
            'min': '1'
        })
    )
    
    budget_min = forms.IntegerField(
        required=False,
        min_value=0,
        error_messages={
            'invalid': 'Veuillez saisir un montant valide.',
            'min_value': 'Le budget ne peut pas être négatif.',
        },
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lily-purple focus:border-transparent transition',
            'placeholder': 'Ex: 500000',
            'min': '0'
        })
    )
    
    budget_max = forms.IntegerField(
        required=False,
        min_value=0,
        error_messages={
            'invalid': 'Veuillez saisir un montant valide.',
            'min_value': 'Le budget ne peut pas être négatif.',
        },
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lily-purple focus:border-transparent transition',
            'placeholder': 'Ex: 2000000',
            'min': '0'
        })
    )
    
    class Meta:
        model = Project
        fields = [
            'title', 'event_type', 'description', 'city', 'location',
            'event_date', 'event_time', 'expected_attendees',
            'budget_min', 'budget_max', 'services_needed'
        ]
    
    def clean_event_date(self):
        """Validation de la date de l'événement"""
        event_date = self.cleaned_data.get('event_date')
        
        if event_date:
            # La date ne peut pas être dans le passé
            if event_date < datetime.date.today():
                raise ValidationError(
                    'La date de l\'événement ne peut pas être dans le passé.'
                )
            
            # La date ne peut pas être trop loin dans le futur (2 ans max)
            max_date = datetime.date.today() + datetime.timedelta(days=730)
            if event_date > max_date:
                raise ValidationError(
                    'La date de l\'événement ne peut pas être au-delà de 2 ans.'
                )
        
        return event_date
    
    def clean_description(self):
        """Validation de la description"""
        description = self.cleaned_data.get('description')
        
        if description:
            # Description minimale de 20 caractères
            if len(description.strip()) < 20:
                raise ValidationError(
                    'La description doit contenir au moins 20 caractères pour être pertinente.'
                )
        
        return description
    
    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()
        budget_min = cleaned_data.get('budget_min')
        budget_max = cleaned_data.get('budget_max')
        
        # Vérifier que budget_max > budget_min si les deux sont renseignés
        if budget_min and budget_max:
            if budget_max < budget_min:
                raise ValidationError(
                    'Le budget maximum doit être supérieur ou égal au budget minimum.'
                )
        
        return cleaned_data


class ContactForm(forms.Form):
    """Formulaire de contact avec validation complète"""
    
    name = forms.CharField(
        max_length=100,
        required=True,
        label='Nom complet',
        error_messages={
            'required': 'Votre nom est obligatoire.',
            'max_length': 'Le nom ne peut pas dépasser 100 caractères.',
        },
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lily-purple focus:border-transparent transition',
            'placeholder': 'Jean Dupont'
        })
    )
    
    email = forms.EmailField(
        required=True,
        label='Adresse email',
        error_messages={
            'required': 'Votre adresse email est obligatoire.',
            'invalid': 'Veuillez saisir une adresse email valide.',
        },
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lily-purple focus:border-transparent transition',
            'placeholder': 'jean.dupont@example.com'
        })
    )
    
    subject = forms.CharField(
        max_length=200,
        required=True,
        label='Sujet',
        error_messages={
            'required': 'Le sujet est obligatoire.',
            'max_length': 'Le sujet ne peut pas dépasser 200 caractères.',
        },
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lily-purple focus:border-transparent transition',
            'placeholder': 'De quoi souhaitez-vous nous parler ?'
        })
    )
    
    message = forms.CharField(
        required=True,
        label='Message',
        error_messages={
            'required': 'Le message est obligatoire.',
        },
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lily-purple focus:border-transparent transition',
            'rows': 6,
            'placeholder': 'Votre message...'
        })
    )
    
    def clean_message(self):
        """Validation du message"""
        message = self.cleaned_data.get('message')
        
        if message and len(message.strip()) < 10:
            raise ValidationError(
                'Le message doit contenir au moins 10 caractères.'
            )
        
        return message


class ProjectEditForm(forms.ModelForm):
    """Formulaire d'édition de projet (réutilise la logique de ProjectCreateForm)"""
    
    event_type = forms.ModelChoiceField(
        queryset=EventType.objects.all(),
        required=True,
        empty_label="Sélectionnez un type d'événement",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lily-purple focus:border-transparent'
        })
    )
    
    services_needed = forms.ModelMultipleChoiceField(
        queryset=ServiceType.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )
    
    title = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            'placeholder': 'Titre du projet'
        })
    )
    
    description = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            'rows': 6
        })
    )
    
    city = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'
        })
    )
    
    event_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'
        })
    )
    
    event_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'
        })
    )
    
    location = forms.CharField(
        max_length=300,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'
        })
    )
    
    guest_count = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            'min': '1'
        })
    )
    
    budget_min = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            'min': '0',
            'step': '0.01'
        })
    )
    
    budget_max = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            'min': '0',
            'step': '0.01'
        })
    )
    
    class Meta:
        model = Project
        fields = [
            'title', 'event_type', 'description', 'city', 'location',
            'event_date', 'event_time', 'guest_count',
            'budget_min', 'budget_max', 'services_needed'
        ]
    
    def clean(self):
        """Validation globale"""
        cleaned_data = super().clean()
        budget_min = cleaned_data.get('budget_min')
        budget_max = cleaned_data.get('budget_max')
        
        if budget_min and budget_max and budget_max < budget_min:
            raise ValidationError(
                'Le budget maximum doit être supérieur ou égal au budget minimum.'
            )
        
        return cleaned_data
