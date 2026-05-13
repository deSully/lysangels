from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .models import User
from .forms import LoginForm


@require_http_methods(["GET", "POST"])
def user_login(request):
    """Connexion utilisateur (admin uniquement)"""
    if request.method == 'POST':
        form = LoginForm(request.POST, request=request)
        if form.is_valid():
            user = form.get_user()
            remember = form.cleaned_data.get('remember_me', False)
            if not remember:
                request.session.set_expiry(0)
            login(request, user)
            messages.success(request, f'Bienvenue {user.get_full_name() or user.username}!')
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            if user.is_admin_event:
                return redirect('accounts:admin_dashboard')
            return redirect('core:home')
        else:
            messages.error(request, 'Identifiants incorrects.')
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
