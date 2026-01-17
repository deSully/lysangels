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
    
    # Le champ logo est maintenant un URLField dans le modèle
    # On utilise un ImageField dans le formulaire pour l'upload,
    # mais on le gère manuellement dans save()
    logo = forms.ImageField(
        required=False,
        validators=[validate_image_file],
        error_messages={
            'invalid': 'Fichier image invalide.',
        },
        widget=forms.FileInput(attrs={
            'class': 'w-full',
            'accept': 'image/*'
        })
    )
    
    class Meta:
        model = VendorProfile
        fields = [
            'business_name', 'description', 'service_types', 'countries',
            'city', 'quartier', 'address', 'google_maps_link',
            'whatsapp', 'website', 'facebook', 'instagram',
            'min_budget', 'max_budget'
        ]
        # Note: 'logo' est géré manuellement dans save() car c'est un URLField
        # dans le modèle mais un ImageField dans le formulaire pour l'upload
    
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

    def save(self, commit=True):
        """Sauvegarde le profil et upload le logo vers Cloudinary si présent"""
        instance = super().save(commit=False)

        # Gérer l'upload du logo vers Cloudinary
        logo_file = self.cleaned_data.get('logo')
        if logo_file:
            logo_url = self._upload_logo_to_cloudinary(logo_file, instance)
            if logo_url:
                instance.logo = logo_url

        if commit:
            instance.save()
            self.save_m2m()

        return instance

    def _upload_logo_to_cloudinary(self, logo_file, instance):
        """Upload le logo vers Cloudinary et retourne l'URL"""
        import os
        from django.conf import settings

        # Récupérer la config Cloudinary
        cloudinary_config = getattr(settings, 'CLOUDINARY_STORAGE', None)

        # Si pas de config dans settings, essayer les variables d'environnement
        if not cloudinary_config:
            cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME', '')
            api_key = os.environ.get('CLOUDINARY_API_KEY', '')
            api_secret = os.environ.get('CLOUDINARY_API_SECRET', '')

            if cloud_name and api_key and api_secret:
                cloudinary_config = {
                    'CLOUD_NAME': cloud_name,
                    'API_KEY': api_key,
                    'API_SECRET': api_secret,
                }

        if not cloudinary_config or not cloudinary_config.get('CLOUD_NAME'):
            # Pas de Cloudinary configuré, on ne peut pas uploader
            return None

        try:
            import cloudinary
            import cloudinary.uploader

            cloudinary.config(
                cloud_name=cloudinary_config.get('CLOUD_NAME'),
                api_key=cloudinary_config.get('API_KEY'),
                api_secret=cloudinary_config.get('API_SECRET'),
            )

            # Générer un public_id unique
            public_id = f"vendor_{instance.user.id}_logo"

            # Upload vers Cloudinary
            result = cloudinary.uploader.upload(
                logo_file,
                folder='vendors/logos',
                public_id=public_id,
                overwrite=True,
                resource_type='image',
                transformation=[
                    {'width': 800, 'height': 800, 'crop': 'limit'},
                    {'quality': 'auto:good'}
                ]
            )

            return result.get('secure_url', '')

        except Exception:
            return None


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
