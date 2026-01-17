"""
Formulaires Django pour les prestataires avec validation complète
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import VendorProfile, ServiceType, Review
from apps.core.models import City, Quartier, Country
from apps.core.validators import validate_image_file


class VendorProfileForm(forms.ModelForm):
    """Formulaire d'édition du profil prestataire avec validation complète"""
    
    business_name = forms.CharField(
        max_length=200,
        required=True,
        error_messages={
            'required': 'Le nom de l\'entreprise est obligatoire.',
            'max_length': 'Le nom ne peut pas dépasser 200 caractères.',
        },
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lily-purple focus:border-transparent',
            'placeholder': 'Ex: Studio Photo LysAngels'
        })
    )
    
    description = forms.CharField(
        required=True,
        error_messages={
            'required': 'La description de votre activité est obligatoire.',
        },
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lily-purple focus:border-transparent',
            'rows': 6,
            'placeholder': 'Décrivez votre activité, vos services, votre expérience...'
        })
    )
    
    service_types = forms.ModelMultipleChoiceField(
        queryset=ServiceType.objects.all().order_by('name'),
        required=True,
        error_messages={
            'required': 'Veuillez sélectionner au moins un type de service.',
        },
        widget=forms.CheckboxSelectMultiple()
    )
    
    countries = forms.ModelMultipleChoiceField(
        queryset=Country.objects.filter(is_active=True).order_by('display_order', 'name'),
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )
    
    city = forms.ModelChoiceField(
        queryset=City.objects.filter(is_active=True).order_by('name'),
        required=False,
        empty_label="Sélectionnez une ville",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lily-purple focus:border-transparent',
            'id': 'id_city'
        })
    )
    
    quartier = forms.ModelChoiceField(
        queryset=Quartier.objects.filter(is_active=True).select_related('city').order_by('name'),
        required=False,
        empty_label="Sélectionnez un quartier",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lily-purple focus:border-transparent',
            'id': 'id_quartier'
        })
    )
    
    address = forms.CharField(
        max_length=300,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            'placeholder': 'Ex: Avenue de la Paix, Immeuble xyz'
        })
    )
    
    google_maps_link = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            'placeholder': 'https://maps.app.goo.gl/...'
        })
    )
    
    whatsapp = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            'placeholder': '+228 XX XX XX XX'
        })
    )
    
    website = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            'placeholder': 'https://www.votre-site.com'
        })
    )
    
    facebook = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            'placeholder': 'https://www.facebook.com/votre-page'
        })
    )
    
    instagram = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            'placeholder': '@votre_compte'
        })
    )
    
    min_budget = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        min_value=0,
        error_messages={
            'invalid': 'Veuillez saisir un montant valide.',
            'min_value': 'Le budget ne peut pas être négatif.',
        },
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            'placeholder': '50000',
            'min': '0',
            'step': '0.01'
        })
    )
    
    max_budget = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        min_value=0,
        error_messages={
            'invalid': 'Veuillez saisir un montant valide.',
            'min_value': 'Le budget ne peut pas être négatif.',
        },
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg',
            'placeholder': '500000',
            'min': '0',
            'step': '0.01'
        })
    )
    
    # Le champ logo est maintenant un ImageField natif du modèle
    
    class Meta:
        model = VendorProfile
        fields = [
            'business_name', 'description', 'service_types', 'countries',
            'city', 'quartier', 'address', 'google_maps_link',
            'whatsapp', 'website', 'facebook', 'instagram',
            'min_budget', 'max_budget', 'logo'
        ]
    
    def clean_description(self):
        """Validation de la description"""
        description = self.cleaned_data.get('description')
        
        if description and len(description.strip()) < 50:
            raise ValidationError(
                'La description doit contenir au moins 50 caractères pour être informative.'
            )
        
        return description
    
    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()
        
        city = cleaned_data.get('city')
        quartier = cleaned_data.get('quartier')
        min_budget = cleaned_data.get('min_budget')
        max_budget = cleaned_data.get('max_budget')
        
        # Vérifier que le quartier appartient à la ville sélectionnée
        if quartier and city and quartier.city != city:
            raise ValidationError(
                'Le quartier sélectionné n\'appartient pas à la ville choisie.'
            )
        
        # Vérifier que max_budget > min_budget si les deux sont renseignés
        if min_budget and max_budget and max_budget < min_budget:
            raise ValidationError(
                'Le budget maximum doit être supérieur ou égal au budget minimum.'
            )

        return cleaned_data




class ReviewForm(forms.ModelForm):
    """Formulaire de création d'avis avec validation"""
    
    rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        required=True,
        error_messages={
            'required': 'Veuillez donner une note.',
            'min_value': 'La note doit être entre 1 et 5.',
            'max_value': 'La note doit être entre 1 et 5.',
        },
        widget=forms.NumberInput(attrs={
            'class': 'hidden',
            'min': '1',
            'max': '5'
        })
    )
    
    comment = forms.CharField(
        required=True,
        error_messages={
            'required': 'Veuillez rédiger un commentaire.',
        },
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lily-purple focus:border-transparent',
            'rows': 5,
            'placeholder': 'Partagez votre expérience avec ce prestataire...'
        })
    )
    
    class Meta:
        model = Review
        fields = ['rating', 'comment']
    
    def clean_comment(self):
        """Validation du commentaire"""
        comment = self.cleaned_data.get('comment')
        
        if comment:
            comment = comment.strip()
            if len(comment) < 20:
                raise ValidationError(
                    'Votre commentaire doit contenir au moins 20 caractères.'
                )
            if len(comment) > 1000:
                raise ValidationError(
                    'Votre commentaire ne peut pas dépasser 1000 caractères.'
                )
        
        return comment
