from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib import messages
from django.db import transaction
from .models import User
from .forms import LoginForm, RegisterForm, ProfileEditForm
from apps.vendors.models import VendorProfile
from apps.core.models import TermsOfService, UserTermsAcceptance


def get_client_ip(request):
    """Récupérer l'adresse IP du client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@require_http_methods(["GET", "POST"])
def register(request):
    """Inscription d'un nouvel utilisateur"""
    # Récupérer les CGU actives
    active_terms = TermsOfService.objects.filter(is_active=True).first()
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Sauvegarder l'utilisateur
                    user = form.save()

                    # Enregistrer l'acceptation des CGU
                    if active_terms:
                        UserTermsAcceptance.objects.create(
                            user=user,
                            terms=active_terms,
                            ip_address=get_client_ip(request)
                        )

                    # Si c'est un prestataire, créer le profil prestataire
                    if user.user_type == 'provider':
                        business_name = form.cleaned_data.get('business_name', f"{user.first_name} {user.last_name}")
                        VendorProfile.objects.create(
                            user=user,
                            business_name=business_name,
                            city=user.city,
                            description='',
                            is_active=False  # Inactif jusqu'à validation par l'admin
                        )

                    login(request, user)
                    
                    if user.user_type == 'provider':
                        messages.success(
                            request, 
                            '✅ Compte créé avec succès ! Complétez maintenant votre profil avec vos services, '
                            'photos et informations de contact. Votre profil sera validé par notre équipe avant publication.'
                        )
                        return redirect('vendors:profile_edit')
                    else:
                        messages.success(request, 'Votre compte a été créé avec succès!')
                        return redirect('core:home')

            except Exception as e:
                messages.error(request, f'Une erreur est survenue: {str(e)}')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = RegisterForm()

    context = {
        'form': form,
        'active_terms': active_terms,
        'breadcrumbs': [
            {'title': 'Accueil', 'url': 'core:home'},
            {'title': 'S\'inscrire'},
        ],
    }
    return render(request, 'accounts/register.html', context)


@require_http_methods(["GET", "POST"])
def user_login(request):
    """Connexion utilisateur"""
    if request.method == 'POST':
        form = LoginForm(request.POST, request=request)
        
        if form.is_valid():
            user = form.get_user()
            
            # Gérer "Se souvenir de moi"
            remember = form.cleaned_data.get('remember_me', False)
            if not remember:
                request.session.set_expiry(0)  # Expire à la fermeture du navigateur
            
            login(request, user)
            messages.success(request, f'Bienvenue {user.get_full_name() or user.username}!')

            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)

            if user.is_provider:
                return redirect('vendors:dashboard')
            elif user.is_susy_admin:
                return redirect('accounts:admin_dashboard')
            else:
                return redirect('accounts:dashboard')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = LoginForm()

    context = {
        'form': form,
        'breadcrumbs': [
            {'title': 'Accueil', 'url': 'core:home'},
            {'title': 'Connexion'},
        ],
    }
    return render(request, 'accounts/login.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def user_logout(request):
    """Déconnexion utilisateur"""
    logout(request)
    messages.success(request, 'Vous êtes déconnecté.')
    return redirect('core:home')


@login_required
def dashboard(request):
    """Dashboard client"""
    if request.user.is_provider:
        return redirect('vendors:dashboard')
    elif request.user.is_susy_admin:
        return redirect('accounts:admin_dashboard')

    projects = request.user.projects.select_related('event_type').order_by('-created_at')[:5]

    context = {
        'projects': projects,
        'breadcrumbs': [
            {'title': 'Accueil', 'url': 'core:home'},
            {'title': 'Mon espace'},
        ],
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def profile(request):
    """Profil utilisateur"""
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil mis à jour avec succès!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = ProfileEditForm(instance=request.user)

    context = {
        'form': form,
        'breadcrumbs': [
            {'title': 'Accueil', 'url': 'core:home'},
            {'title': 'Mon espace', 'url': 'accounts:dashboard'},
            {'title': 'Mon profil'},
        ],
    }
    return render(request, 'accounts/profile.html', context)
