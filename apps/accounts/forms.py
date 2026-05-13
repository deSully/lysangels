"""Formulaires pour l'application accounts avec validation complète"""
from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import User


class LoginForm(forms.Form):
    """Formulaire de connexion"""
    username = forms.CharField(
        max_length=150,
        required=True,
        label="Nom d'utilisateur ou email",
        widget=forms.TextInput(attrs={
            'placeholder': "Votre nom d'utilisateur ou email",
            'class': 'form-control',
            'autocomplete': 'username'
        }),
        error_messages={
            'required': 'Le nom d\'utilisateur est requis.',
            'max_length': 'Le nom d\'utilisateur ne peut pas dépasser 150 caractères.'
        }
    )
    
    password = forms.CharField(
        required=True,
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'placeholder': "Votre mot de passe",
            'class': 'form-control',
            'autocomplete': 'current-password'
        }),
        error_messages={
            'required': 'Le mot de passe est requis.'
        }
    )
    
    remember_me = forms.BooleanField(
        required=False,
        label="Se souvenir de moi",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        """Validation globale - vérifier les identifiants"""
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            # Essayer d'authentifier avec le username
            user = authenticate(username=username, password=password)
            
            # Si ça ne marche pas, essayer avec l'email
            if not user:
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass
            
            if not user:
                raise ValidationError(
                    'Identifiants incorrects. Veuillez vérifier votre nom d\'utilisateur/email et votre mot de passe.'
                )
            
            if not user.is_active:
                raise ValidationError(
                    'Ce compte est désactivé. Veuillez contacter l\'administrateur.'
                )
            
            self.user = user
        
        return cleaned_data

    def get_user(self):
        """Retourner l'utilisateur authentifié"""
        return self.user


