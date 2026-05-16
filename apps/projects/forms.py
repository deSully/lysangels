from django import forms
from django.core.exceptions import ValidationError
from apps.projects.models import Project, EventType
from apps.vendors.models import ServiceType
from apps.core.models import Country, City
import datetime

INPUT_CLASS = 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-lily-purple focus:border-transparent transition'


class ProjectCreateForm(forms.ModelForm):
    contact_name = forms.CharField(
        max_length=200,
        required=True,
        label='Votre nom complet',
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Ex: Marie Dupont'})
    )
    contact_email = forms.EmailField(
        required=True,
        label='Votre email',
        widget=forms.EmailInput(attrs={'class': INPUT_CLASS, 'placeholder': 'marie@exemple.com'})
    )
    contact_phone = forms.CharField(
        max_length=30,
        required=False,
        label='Votre téléphone (optionnel)',
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': '+228 90 00 00 00'})
    )
    event_type = forms.ModelChoiceField(
        queryset=EventType.objects.all(),
        required=False,
        empty_label="Sélectionnez un type d'événement",
        widget=forms.Select(attrs={'class': INPUT_CLASS})
    )
    description = forms.CharField(
        required=True,
        label='Décrivez votre projet',
        widget=forms.Textarea(attrs={
            'class': INPUT_CLASS,
            'rows': 6,
            'placeholder': 'Décrivez votre événement, vos attentes, vos préférences...'
        })
    )
    country = forms.ModelChoiceField(
        queryset=Country.objects.filter(is_active=True).order_by('display_order', 'name'),
        required=False,
        empty_label='— Sélectionner un pays —',
        label='Pays',
        widget=forms.Select(attrs={'class': INPUT_CLASS, 'id': 'id_country'}),
    )
    city = forms.ModelChoiceField(
        queryset=City.objects.filter(is_active=True).select_related('country').order_by('name'),
        required=False,
        empty_label='— Sélectionner une ville —',
        label='Ville',
        widget=forms.Select(attrs={'class': INPUT_CLASS, 'id': 'id_city'}),
    )
    event_date = forms.DateField(
        required=False,
        label="Date de l'événement (optionnel)",
        widget=forms.DateInput(attrs={'type': 'date', 'class': INPUT_CLASS})
    )
    event_time = forms.TimeField(
        required=False,
        label="Heure de l'événement (optionnel)",
        widget=forms.TimeInput(attrs={'type': 'time', 'class': INPUT_CLASS})
    )
    location = forms.CharField(
        max_length=300,
        required=False,
        label='Lieu précis (optionnel)',
        widget=forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Ex: Hôtel Sarakawa'})
    )
    guest_count = forms.IntegerField(
        required=False,
        min_value=1,
        label="Nombre d'invités estimé (optionnel)",
        widget=forms.NumberInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Ex: 100', 'min': '1'})
    )
    budget_min = forms.IntegerField(
        required=False,
        min_value=0,
        label='Budget minimum (FCFA)',
        widget=forms.NumberInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Ex: 500 000', 'min': '0'})
    )
    budget_max = forms.IntegerField(
        required=False,
        min_value=0,
        label='Budget maximum (FCFA)',
        widget=forms.NumberInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Ex: 2 000 000', 'min': '0'})
    )
    services_needed = forms.ModelMultipleChoiceField(
        queryset=ServiceType.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )

    class Meta:
        model = Project
        fields = [
            'contact_name', 'contact_email', 'contact_phone',
            'event_type', 'country', 'city', 'location',
            'event_date', 'event_time', 'guest_count',
            'budget_min', 'budget_max', 'services_needed',
        ]

    def clean_event_date(self):
        event_date = self.cleaned_data.get('event_date')
        if event_date:
            if event_date < datetime.date.today():
                raise ValidationError("La date de l'événement ne peut pas être dans le passé.")
            max_date = datetime.date.today() + datetime.timedelta(days=730)
            if event_date > max_date:
                raise ValidationError("La date de l'événement ne peut pas être au-delà de 2 ans.")
        return event_date

    def clean(self):
        cleaned_data = super().clean()
        country = cleaned_data.get('country')
        city = cleaned_data.get('city')
        if city and country and city.country != country:
            self.add_error('city', "Cette ville n'appartient pas au pays sélectionné.")
        budget_min = cleaned_data.get('budget_min') or 0
        budget_max = cleaned_data.get('budget_max') or 0
        cleaned_data['budget_min'] = budget_min
        cleaned_data['budget_max'] = budget_max
        if budget_min and budget_max and budget_max < budget_min:
            raise ValidationError('Le budget maximum doit être supérieur ou égal au budget minimum.')
        return cleaned_data
