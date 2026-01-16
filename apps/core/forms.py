from django import forms
from .models import ContactMessage


class ContactForm(forms.ModelForm):
    """Formulaire de contact"""

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-lily-purple focus:border-transparent transition',
                'placeholder': 'Votre nom complet'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-lily-purple focus:border-transparent transition',
                'placeholder': 'votre@email.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-lily-purple focus:border-transparent transition',
                'placeholder': '+228 XX XX XX XX (optionnel)'
            }),
            'subject': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-lily-purple focus:border-transparent transition bg-white'
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-lily-purple focus:border-transparent transition',
                'placeholder': 'Décrivez votre demande en détail...',
                'rows': 5
            }),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        if phone:
            # Nettoyer le numéro (garder uniquement chiffres et +)
            cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
            return cleaned
        return phone
