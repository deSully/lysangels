"""
Formulaires Django pour les propositions avec validation complète
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import Proposal, ProposalRequest
from apps.projects.models import Project
from apps.core.validators import validate_attachment_file


class ProposalForm(forms.ModelForm):
    """Formulaire de création de proposition avec validation complète"""
    
    title = forms.CharField(
        max_length=200,
        required=True,
        error_messages={
            'required': 'Le titre de la proposition est obligatoire.',
            'max_length': 'Le titre ne peut pas dépasser 200 caractères.',
        },
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lily-purple focus:border-transparent',
            'placeholder': 'Ex: Forfait Premium - Couverture complète de votre événement'
        })
    )
    
    message = forms.CharField(
        required=True,
        error_messages={
            'required': 'Le message est obligatoire.',
        },
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lily-purple focus:border-transparent',
            'rows': 4,
            'placeholder': 'Message personnel pour le client...'
        })
    )
    
    description = forms.CharField(
        required=True,
        error_messages={
            'required': 'La description détaillée est obligatoire.',
        },
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lily-purple focus:border-transparent',
            'rows': 8,
            'placeholder': 'Décrivez en détail votre offre, ce qui est inclus, les prestations proposées...'
        })
    )
    
    price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        min_value=0,
        error_messages={
            'required': 'Le prix est obligatoire.',
            'invalid': 'Veuillez saisir un montant valide.',
            'min_value': 'Le prix ne peut pas être négatif.',
        },
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lily-purple focus:border-transparent',
            'placeholder': '150000',
            'min': '0',
            'step': '0.01'
        })
    )
    
    deposit_required = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        min_value=0,
        error_messages={
            'invalid': 'Veuillez saisir un montant valide.',
            'min_value': 'Le dépôt ne peut pas être négatif.',
        },
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lily-purple focus:border-transparent',
            'placeholder': '50000',
            'min': '0',
            'step': '0.01'
        })
    )
    
    terms_and_conditions = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lily-purple focus:border-transparent',
            'rows': 5,
            'placeholder': 'Conditions de paiement, annulation, garanties...'
        })
    )
    
    validity_days = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=90,
        initial=30,
        error_messages={
            'invalid': 'Veuillez saisir un nombre de jours valide.',
            'min_value': 'La durée de validité doit être d\'au moins 1 jour.',
            'max_value': 'La durée de validité ne peut pas dépasser 90 jours.',
        },
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            'placeholder': '30',
            'min': '1',
            'max': '90'
        })
    )
    
    attachment = forms.FileField(
        required=False,
        validators=[validate_attachment_file],
        error_messages={
            'invalid': 'Fichier joint invalide.',
        },
        widget=forms.FileInput(attrs={
            'class': 'w-full',
            'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
        })
    )
    
    class Meta:
        model = Proposal
        fields = [
            'title', 'message', 'description', 'price', 'deposit_required',
            'terms_and_conditions', 'validity_days', 'attachment'
        ]
    
    def clean_description(self):
        """Validation de la description"""
        description = self.cleaned_data.get('description')
        
        if description and len(description.strip()) < 50:
            raise ValidationError(
                'La description doit contenir au moins 50 caractères pour être informative.'
            )
        
        return description
    
    def clean_message(self):
        """Validation du message"""
        message = self.cleaned_data.get('message')
        
        if message and len(message.strip()) < 20:
            raise ValidationError(
                'Le message doit contenir au moins 20 caractères.'
            )
        
        return message
    
    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()
        
        price = cleaned_data.get('price')
        deposit_required = cleaned_data.get('deposit_required')
        
        # Vérifier que le dépôt ne dépasse pas le prix total
        if price and deposit_required and deposit_required > price:
            raise ValidationError(
                'Le dépôt requis ne peut pas dépasser le prix total.'
            )
        
        return cleaned_data


class ProposalRequestForm(forms.ModelForm):
    """Formulaire d'envoi de demande de devis"""
    
    message = forms.CharField(
        required=True,
        error_messages={
            'required': 'Veuillez décrire votre demande.',
        },
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lily-purple focus:border-transparent',
            'rows': 6,
            'placeholder': 'Décrivez votre demande, vos attentes, questions spécifiques...'
        })
    )
    
    class Meta:
        model = ProposalRequest
        fields = ['message']
    
    def clean_message(self):
        """Validation du message"""
        message = self.cleaned_data.get('message')
        
        if message:
            message = message.strip()
            if len(message) < 30:
                raise ValidationError(
                    'Votre message doit contenir au moins 30 caractères pour être pertinent.'
                )
        
        return message
