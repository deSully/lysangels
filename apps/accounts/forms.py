"""Formulaires pour l'application accounts avec validation complète"""
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
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


class RegisterForm(forms.ModelForm):
    """Formulaire d'inscription"""
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'placeholder': "Minimum 8 caractères",
            'class': 'form-control',
            'autocomplete': 'new-password'
        }),
        help_text="Au moins 8 caractères avec lettres et chiffres",
        error_messages={
            'required': 'Le mot de passe est requis.'
        }
    )
    
    password_confirm = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={
            'placeholder': "Confirmer votre mot de passe",
            'class': 'form-control',
            'autocomplete': 'new-password'
        }),
        error_messages={
            'required': 'La confirmation du mot de passe est requise.'
        }
    )
    
    user_type = forms.ChoiceField(
        choices=[('client', 'Client'), ('provider', 'Prestataire')],
        initial='client',
        label="Type de compte",
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        error_messages={
            'required': 'Vous devez choisir un type de compte.',
            'invalid_choice': 'Type de compte invalide.'
        }
    )
    
    accept_terms = forms.BooleanField(
        required=True,
        label="J'accepte les conditions générales d'utilisation",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        error_messages={
            'required': 'Vous devez accepter les conditions générales d\'utilisation pour vous inscrire.'
        }
    )
    
    # Champs supplémentaires pour les prestataires
    business_name = forms.CharField(
        max_length=200,
        required=False,
        label="Nom de l'entreprise",
        widget=forms.TextInput(attrs={
            'placeholder': "Nom de votre entreprise",
            'class': 'form-control'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'city', 'user_type']
        widgets = {
            'username': forms.TextInput(attrs={
                'placeholder': "Nom d'utilisateur unique",
                'class': 'form-control',
                'autocomplete': 'username'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': "votre@email.com",
                'class': 'form-control',
                'autocomplete': 'email'
            }),
            'first_name': forms.TextInput(attrs={
                'placeholder': "Prénom",
                'class': 'form-control',
                'autocomplete': 'given-name'
            }),
            'last_name': forms.TextInput(attrs={
                'placeholder': "Nom",
                'class': 'form-control',
                'autocomplete': 'family-name'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': "06 12 34 56 78",
                'class': 'form-control',
                'autocomplete': 'tel'
            }),
            'city': forms.TextInput(attrs={
                'placeholder': "Ville",
                'class': 'form-control',
                'autocomplete': 'address-level2'
            }),
        }
        error_messages = {
            'username': {
                'required': 'Le nom d\'utilisateur est requis.',
                'max_length': 'Le nom d\'utilisateur ne peut pas dépasser 150 caractères.',
                'unique': 'Ce nom d\'utilisateur existe déjà.'
            },
            'email': {
                'required': 'L\'email est requis.',
                'invalid': 'L\'email n\'est pas valide.',
                'unique': 'Cet email est déjà utilisé.'
            },
            'first_name': {
                'required': 'Le prénom est requis.',
                'max_length': 'Le prénom ne peut pas dépasser 150 caractères.'
            },
            'last_name': {
                'required': 'Le nom est requis.',
                'max_length': 'Le nom ne peut pas dépasser 150 caractères.'
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre certains champs obligatoires
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True

    def clean_username(self):
        """Valider le nom d'utilisateur"""
        username = self.cleaned_data.get('username')
        
        if not username:
            raise ValidationError('Le nom d\'utilisateur est requis.')
        
        # Vérifier la longueur minimale
        if len(username) < 3:
            raise ValidationError('Le nom d\'utilisateur doit contenir au moins 3 caractères.')
        
        # Vérifier les caractères autorisés
        if not username.replace('_', '').replace('.', '').replace('-', '').isalnum():
            raise ValidationError(
                'Le nom d\'utilisateur ne peut contenir que des lettres, chiffres, tirets, underscores et points.'
            )
        
        # Vérifier l'unicité
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('Ce nom d\'utilisateur existe déjà.')
        
        return username

    def clean_email(self):
        """Valider l'email"""
        email = self.cleaned_data.get('email')
        
        if not email:
            raise ValidationError('L\'email est requis.')
        
        # Normaliser l'email
        email = email.lower().strip()
        
        # Vérifier l'unicité
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Cet email est déjà utilisé.')
        
        return email

    def clean_phone(self):
        """Valider le numéro de téléphone"""
        phone = self.cleaned_data.get('phone')
        
        if phone:
            # Retirer les espaces et caractères spéciaux
            phone_clean = ''.join(filter(str.isdigit, phone))
            
            # Vérifier la longueur (10 chiffres pour la France)
            if len(phone_clean) != 10:
                raise ValidationError('Le numéro de téléphone doit contenir 10 chiffres.')
            
            # Vérifier que ça commence par 0
            if not phone_clean.startswith('0'):
                raise ValidationError('Le numéro de téléphone doit commencer par 0.')
        
        return phone

    def clean_password(self):
        """Valider le mot de passe avec les validateurs Django"""
        password = self.cleaned_data.get('password')
        
        if not password:
            raise ValidationError('Le mot de passe est requis.')
        
        # Utiliser les validateurs Django
        try:
            validate_password(password)
        except ValidationError as e:
            raise ValidationError(e.messages)
        
        return password

    def clean(self):
        """Validation globale"""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        user_type = cleaned_data.get('user_type')
        business_name = cleaned_data.get('business_name')

        # Vérifier que les mots de passe correspondent
        if password and password_confirm:
            if password != password_confirm:
                raise ValidationError({
                    'password_confirm': 'Les mots de passe ne correspondent pas.'
                })

        # Si prestataire, business_name requis
        if user_type == 'provider' and not business_name:
            # Utiliser le nom complet par défaut
            first_name = cleaned_data.get('first_name', '')
            last_name = cleaned_data.get('last_name', '')
            cleaned_data['business_name'] = f"{first_name} {last_name}".strip()

        return cleaned_data

    def save(self, commit=True):
        """Sauvegarder l'utilisateur avec le mot de passe hashé"""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        
        if commit:
            user.save()
        
        return user


class ProfileEditForm(forms.ModelForm):
    """Formulaire de modification du profil utilisateur"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'city', 'profile_image']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'placeholder': "Prénom",
                'class': 'form-control'
            }),
            'last_name': forms.TextInput(attrs={
                'placeholder': "Nom",
                'class': 'form-control'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': "votre@email.com",
                'class': 'form-control'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': "06 12 34 56 78",
                'class': 'form-control'
            }),
            'city': forms.TextInput(attrs={
                'placeholder': "Ville",
                'class': 'form-control'
            }),
            'profile_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
        error_messages = {
            'first_name': {
                'required': 'Le prénom est requis.',
            },
            'last_name': {
                'required': 'Le nom est requis.',
            },
            'email': {
                'required': 'L\'email est requis.',
                'invalid': 'L\'email n\'est pas valide.',
            },
        }

    def __init__(self, *args, **kwargs):
        self.user_instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True

    def clean_email(self):
        """Valider l'email (ne pas vérifier l'unicité si c'est le même)"""
        email = self.cleaned_data.get('email')
        
        if not email:
            raise ValidationError('L\'email est requis.')
        
        email = email.lower().strip()
        
        # Vérifier l'unicité seulement si l'email a changé
        if self.user_instance and email != self.user_instance.email:
            if User.objects.filter(email__iexact=email).exists():
                raise ValidationError('Cet email est déjà utilisé.')
        
        return email

    def clean_phone(self):
        """Valider le numéro de téléphone"""
        phone = self.cleaned_data.get('phone')
        
        if phone:
            phone_clean = ''.join(filter(str.isdigit, phone))
            
            if len(phone_clean) != 10:
                raise ValidationError('Le numéro de téléphone doit contenir 10 chiffres.')
            
            if not phone_clean.startswith('0'):
                raise ValidationError('Le numéro de téléphone doit commencer par 0.')
        
        return phone

    def clean_profile_image(self):
        """Valider l'image de profil"""
        image = self.cleaned_data.get('profile_image')
        
        if image:
            # Vérifier la taille (max 5MB)
            if image.size > 5 * 1024 * 1024:
                raise ValidationError('L\'image ne peut pas dépasser 5 MB.')
            
            # Vérifier le format
            if not image.content_type.startswith('image/'):
                raise ValidationError('Le fichier doit être une image.')
        
        return image
