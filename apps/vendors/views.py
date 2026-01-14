from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.db.models import Q, Case, When, IntegerField, Avg
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from .models import VendorProfile, VendorImage, Review
from .forms import VendorProfileForm
from apps.core.models import City, Quartier, Country
from apps.projects.models import Project
from apps.core.cache_utils import get_cached_service_types
from apps.core.validators import (
    validate_image_file,
    check_user_storage_quota,
    get_user_storage_info
)


@login_required
def vendor_list(request):
    """Liste des prestataires avec filtres - Réservé aux utilisateurs connectés"""

    # Filtres multiples (checkboxes)
    service_type_ids = request.GET.getlist('service_types')
    city_ids = request.GET.getlist('cities')
    quartier_ids = request.GET.getlist('quartiers')
    search = request.GET.get('search')

    # Vérifier si des filtres sont appliqués
    has_filters = bool(search or service_type_ids or city_ids or quartier_ids)

    # Calculer les statistiques réelles
    # Nombre de prestataires actifs
    total_vendors = VendorProfile.objects.filter(is_active=True).count()

    # Nombre de projets conclus
    completed_projects = Project.objects.filter(status='completed').count()

    # Calculer le taux de satisfaction basé sur les avis approuvés
    avg_rating = Review.objects.filter(status='approved').aggregate(avg=Avg('rating'))['avg']
    satisfaction_rate = round((avg_rating / 5 * 100), 1) if avg_rating else 0

    # Mode par catégories (affichage initial sans filtres)
    if not has_filters:
        service_types = get_cached_service_types(ordered=True)
        vendors_by_category = []

        for service_type in service_types:
            vendors = VendorProfile.objects.filter(
                is_active=True,
                subscription_tier__is_visible_in_list=True,
                service_types=service_type
            ).select_related('subscription_tier', 'city').prefetch_related(
                'service_types',
                'images'  # Précharger les images pour éviter N+1 queries
            ).annotate(
                tier_priority=Case(
                    When(subscription_tier__isnull=True, then=999),
                    default='subscription_tier__display_priority',
                    output_field=IntegerField()
                )
            ).order_by('tier_priority', '-created_at')[:6]  # 6 prestataires max par catégorie

            if vendors.exists():
                vendors_by_category.append({
                    'service_type': service_type,
                    'vendors': vendors
                })

        # Contexte pour mode catégories
        all_service_types = get_cached_service_types(ordered=True)
        all_countries = Country.objects.filter(is_active=True).order_by('display_order', 'name')
        all_cities = City.objects.filter(is_active=True).order_by('name')
        all_quartiers = Quartier.objects.filter(is_active=True).select_related('city').order_by('city__name', 'name')

        context = {
            'vendors_by_category': vendors_by_category,
            'service_types': all_service_types,
            'countries': all_countries,
            'cities': all_cities,
            'quartiers': all_quartiers,
            'selected_service_types': [],
            'selected_cities': [],
            'selected_quartiers': [],
            'search_query': search,
            'display_mode': 'categories',
            'total_vendors': total_vendors,
            'completed_projects': completed_projects,
            'satisfaction_rate': satisfaction_rate,
            'breadcrumbs': [
                {'title': 'Accueil', 'url': 'core:home'},
                {'title': 'Prestataires'},
            ],
        }
        return render(request, 'vendors/vendor_list.html', context)
    
    # Mode liste (avec filtres)
    vendors = VendorProfile.objects.filter(is_active=True)

    # Appliquer les filtres multiples
    if service_type_ids:
        vendors = vendors.filter(service_types__id__in=service_type_ids).distinct()

    if city_ids:
        vendors = vendors.filter(city__id__in=city_ids)
    
    if quartier_ids:
        vendors = vendors.filter(quartier__id__in=quartier_ids)

    if search:
        vendors = vendors.filter(
            Q(business_name__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Tri par priorité d'abonnement (Premium > Standard > Gratuit)
    vendors = vendors.select_related('subscription_tier', 'city').prefetch_related(
        'service_types',
        'images'  # Précharger les images pour éviter N+1 queries
    ).annotate(
        tier_priority=Case(
            When(subscription_tier__isnull=True, then=999),
            default='subscription_tier__display_priority',
            output_field=IntegerField()
        )
    ).order_by('tier_priority', '-created_at')

    # Pagination - 12 prestataires par page
    paginator = Paginator(vendors, 12)
    page_number = request.GET.get('page', '1')
    
    # Valider et limiter le numéro de page
    try:
        page_number = int(page_number)
        if page_number < 1:
            page_number = 1
        elif page_number > 10000:  # Limite maximale raisonnable
            page_number = paginator.num_pages
    except (ValueError, TypeError):
        page_number = 1
    
    vendors_page = paginator.get_page(page_number)

    # Données pour les filtres
    all_service_types = get_cached_service_types(ordered=True)
    all_countries = Country.objects.filter(is_active=True).order_by('display_order', 'name')
    all_cities = City.objects.filter(is_active=True).order_by('name')
    all_quartiers = Quartier.objects.filter(is_active=True).select_related('city').order_by('city__name', 'name')

    context = {
        'vendors': vendors_page,
        'service_types': all_service_types,
        'countries': all_countries,
        'cities': all_cities,
        'quartiers': all_quartiers,
        'selected_service_types': service_type_ids,
        'selected_cities': city_ids,
        'selected_quartiers': quartier_ids,
        'search_query': search,
        'display_mode': 'list',
        'total_vendors': total_vendors,
        'completed_projects': completed_projects,
        'satisfaction_rate': satisfaction_rate,
        'breadcrumbs': [
            {'title': 'Accueil', 'url': 'core:home'},
            {'title': 'Prestataires'},
        ],
    }
    return render(request, 'vendors/vendor_list.html', context)


@login_required
def vendor_detail(request, pk):
    """Détails d'un prestataire - Réservé aux utilisateurs connectés"""
    vendor = get_object_or_404(
        VendorProfile.objects.select_related(
            'subscription_tier',
            'city',
            'quartier'
        ).prefetch_related(
            'service_types',
            'countries',
            'images'  # Précharger toutes les images du portfolio
        ),
        pk=pk,
        is_active=True
    )
    
    # Récupérer uniquement les avis approuvés avec prefetch pour éviter N+1 queries
    reviews = vendor.reviews.filter(status='approved').select_related(
        'client', 'project'
    ).prefetch_related(
        'client__vendor_profile'  # Si besoin d'afficher si le client est aussi prestataire
    ).order_by('-created_at')[:10]

    context = {
        'vendor': vendor,
        'reviews': reviews,
        'breadcrumbs': [
            {'title': 'Accueil', 'url': 'core:home'},
            {'title': 'Prestataires', 'url': 'vendors:vendor_list'},
            {'title': vendor.business_name},
        ],
    }
    return render(request, 'vendors/vendor_detail.html', context)


@login_required
def dashboard(request):
    """Dashboard prestataire"""
    if not request.user.is_provider:
        messages.error(request, 'Accès réservé aux prestataires.')
        return redirect('core:home')

    vendor_profile = get_object_or_404(VendorProfile, user=request.user)
    recent_requests = vendor_profile.received_requests.select_related(
        'project__client',
        'project__event_type'
    ).order_by('-created_at')[:10]
    
    # Informations de stockage
    storage_info = get_user_storage_info(request.user)

    context = {
        'vendor_profile': vendor_profile,
        'recent_requests': recent_requests,
        'storage_info': storage_info,
        'breadcrumbs': [
            {'title': 'Accueil', 'url': 'core:home'},
            {'title': 'Tableau de bord'},
        ],
    }
    return render(request, 'vendors/dashboard.html', context)


@login_required
def profile_edit(request):
    """Édition du profil prestataire"""
    if not request.user.is_provider:
        messages.error(request, 'Accès réservé aux prestataires.')
        return redirect('core:home')

    try:
        vendor_profile = VendorProfile.objects.get(user=request.user)
    except VendorProfile.DoesNotExist:
        vendor_profile = VendorProfile.objects.create(
            user=request.user,
            business_name=f"{request.user.first_name} {request.user.last_name}",
            description='',
        )

    if request.method == 'POST':
        form = VendorProfileForm(request.POST, request.FILES, instance=vendor_profile)
        
        if form.is_valid():
            vendor_profile = form.save(commit=False)
            
            # Assigner le Togo par défaut si aucun pays sélectionné
            if not form.cleaned_data.get('countries'):
                default_country = Country.objects.filter(code='TG').first()
                if default_country:
                    vendor_profile.save()
                    vendor_profile.countries.set([default_country])
            
            vendor_profile.save()
            form.save_m2m()  # Sauvegarder les relations many-to-many

            # Gestion des images de galerie
            images = request.FILES.getlist('images')
            if images:
                # Utiliser une transaction pour éviter les race conditions sur le quota
                with transaction.atomic():
                    # Recharger le vendor_profile avec un verrou
                    vendor_profile = VendorProfile.objects.select_for_update().get(pk=vendor_profile.pk)
                    
                    # Vérifier le nombre max d'images
                    max_images = vendor_profile.subscription_tier.max_images if vendor_profile.subscription_tier else 10
                    current_count = vendor_profile.images.count()
                    available_slots = max_images - current_count
                    
                    if len(images) > available_slots:
                        messages.warning(
                            request,
                            f'Vous ne pouvez ajouter que {available_slots} image(s) supplémentaire(s). '
                            f'Limite de votre abonnement: {max_images} images.'
                        )
                        images = images[:available_slots]
                    
                    # Créer les images avec validation stricte
                    success_count = 0
                    for image in images:
                        try:
                            # Vérifier le quota de stockage global avant chaque image
                            check_user_storage_quota(request.user, image.size)
                            
                            # Validation complète (taille + MIME type + extension)
                            validate_image_file(image)
                            
                            vendor_image = VendorImage(vendor=vendor_profile, image=image)
                            vendor_image.full_clean()
                            vendor_image.save()
                            success_count += 1
                        except ValidationError:
                            messages.warning(request, f'Image "{image.name}": Fichier invalide.')
                        except Exception:
                            messages.warning(request, f'Impossible d\'ajouter "{image.name}".')
                    
                    if success_count > 0:
                        messages.success(request, f'{success_count} image(s) ajoutée(s) avec succès!')

            messages.success(request, 'Profil mis à jour avec succès!')
            return redirect('vendors:dashboard')
        else:
            # Formulaire invalide - les erreurs sont affichées dans le template
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = VendorProfileForm(instance=vendor_profile)

    context = {
        'vendor_profile': vendor_profile,
        'form': form,
        'breadcrumbs': [
            {'title': 'Accueil', 'url': 'core:home'},
            {'title': 'Tableau de bord', 'url': 'vendors:dashboard'},
            {'title': 'Modifier mon profil'},
        ],
    }
    return render(request, 'vendors/profile_edit.html', context)


@login_required
def portfolio_manage(request):
    """Gestion du portfolio d'images du prestataire"""
    if not hasattr(request.user, 'vendor_profile'):
        messages.error(request, 'Vous devez être un prestataire pour accéder à cette page.')
        return redirect('core:home')
    
    vendor_profile = request.user.vendor_profile
    images = vendor_profile.images.all().order_by('-is_cover', '-created_at')
    
    # Calculer les quotas
    max_images = vendor_profile.subscription_tier.max_images if vendor_profile.subscription_tier else 10
    current_count = images.count()
    remaining = max_images - current_count
    percentage = int((current_count / max_images * 100)) if max_images > 0 else 0
    
    context = {
        'vendor_profile': vendor_profile,
        'images': images,
        'max_images': max_images,
        'current_count': current_count,
        'remaining': remaining,
        'percentage': percentage,
        'breadcrumbs': [
            {'title': 'Accueil', 'url': 'core:home'},
            {'title': 'Tableau de bord', 'url': 'vendors:dashboard'},
            {'title': 'G\u00e9rer mon portfolio'},
        ],
    }
    return render(request, 'vendors/portfolio_manage.html', context)


@login_required
@require_POST
def portfolio_upload(request):
    """Upload d'images dans le portfolio via AJAX"""
    if not hasattr(request.user, 'vendor_profile'):
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'}, status=403)
    
    vendor_profile = request.user.vendor_profile
    
    # Vérifier le quota
    max_images = vendor_profile.subscription_tier.max_images if vendor_profile.subscription_tier else 10
    current_count = vendor_profile.images.count()
    remaining = max_images - current_count
    
    if remaining <= 0:
        return JsonResponse({
            'success': False,
            'error': f'Limite atteinte. Votre abonnement autorise {max_images} images maximum.'
        })
    
    # Récupérer les images uploadées
    images = request.FILES.getlist('images')
    if not images:
        return JsonResponse({'success': False, 'error': 'Aucune image sélectionnée'})
    
    # Limiter au nombre d'emplacements disponibles
    if len(images) > remaining:
        return JsonResponse({
            'success': False,
            'error': f'Vous ne pouvez ajouter que {remaining} image(s) supplémentaire(s).'
        })
    
    # Traiter les images
    uploaded = []
    errors = []
    
    for image in images:
        try:
            # Vérifier le quota de stockage
            check_user_storage_quota(request.user, image.size)
            
            # Validation complète (taille + MIME type + extension)
            validate_image_file(image)
            
            vendor_image = VendorImage(vendor=vendor_profile, image=image)
            vendor_image.full_clean()
            vendor_image.save()
            
            uploaded.append({
                'id': vendor_image.id,
                'url': vendor_image.image.url,
                'is_cover': vendor_image.is_cover,
            })
        except ValidationError:
            errors.append(f'{image.name}: Fichier invalide')
        except Exception:
            errors.append(f'{image.name}: Erreur lors du traitement')
    
    return JsonResponse({
        'success': len(uploaded) > 0,
        'uploaded': uploaded,
        'errors': errors,
        'remaining': max_images - (current_count + len(uploaded)),
    })


@login_required
@require_POST
def portfolio_delete(request, image_id):
    """Suppression d'une image du portfolio"""
    if not hasattr(request.user, 'vendor_profile'):
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'}, status=403)
    
    vendor_profile = request.user.vendor_profile
    
    try:
        image = VendorImage.objects.get(id=image_id, vendor=vendor_profile)
        image.delete()
        
        # Calculer le quota restant
        max_images = vendor_profile.subscription_tier.max_images if vendor_profile.subscription_tier else 10
        current_count = vendor_profile.images.count()
        
        return JsonResponse({
            'success': True,
            'remaining': max_images - current_count,
        })
    except VendorImage.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Image introuvable'}, status=404)


@login_required
@require_POST
def portfolio_set_cover(request, image_id):
    """Définir une image comme couverture"""
    if not hasattr(request.user, 'vendor_profile'):
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'}, status=403)
    
    vendor_profile = request.user.vendor_profile
    
    try:
        # Retirer le statut cover de toutes les images
        vendor_profile.images.update(is_cover=False)
        
        # Définir la nouvelle image de couverture
        image = VendorImage.objects.get(id=image_id, vendor=vendor_profile)
        image.is_cover = True
        image.save()
        
        return JsonResponse({'success': True})
    except VendorImage.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Image introuvable'}, status=404)


# ===============================================
# VUES POUR LES AVIS
# ===============================================

@login_required
def create_review(request, vendor_id):
    """Créer un avis pour un prestataire (clients uniquement)"""
    vendor = get_object_or_404(VendorProfile, id=vendor_id, is_active=True)
    
    # Vérifier que l'utilisateur n'est pas le prestataire lui-même
    if hasattr(request.user, 'vendor_profile') and request.user.vendor_profile == vendor:
        messages.error(request, "Vous ne pouvez pas vous auto-évaluer.")
        return redirect('vendors:vendor_detail', vendor_id=vendor.id)
    
    # Récupérer les projets du client avec ce prestataire (ayant une proposition acceptée)
    eligible_projects = Project.objects.filter(
        client=request.user,
        proposals__vendor=vendor,
        proposals__status='accepted'
    ).distinct()
    
    if request.method == 'POST':
        project_id = request.POST.get('project')
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()
        
        # Validation
        if not rating or not comment:
            messages.error(request, "Veuillez remplir tous les champs obligatoires.")
            return render(request, 'vendors/create_review.html', {
                'vendor': vendor,
                'eligible_projects': eligible_projects,
            })
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError("Note invalide")
        except (ValueError, TypeError):
            messages.error(request, "Note invalide. Veuillez choisir entre 1 et 5 étoiles.")
            return render(request, 'vendors/create_review.html', {
                'vendor': vendor,
                'eligible_projects': eligible_projects,
            })
        
        # Vérifier que le projet existe et appartient au client
        project = None
        if project_id:
            try:
                project = eligible_projects.get(id=project_id)
            except Project.DoesNotExist:
                messages.error(request, "Projet invalide.")
                return render(request, 'vendors/create_review.html', {
                    'vendor': vendor,
                    'eligible_projects': eligible_projects,
                })
        
        # Vérifier qu'un avis n'existe pas déjà pour ce projet
        if project and Review.objects.filter(vendor=vendor, project=project).exists():
            messages.error(request, "Vous avez déjà laissé un avis pour ce projet.")
            return redirect('vendors:vendor_detail', vendor_id=vendor.id)
        
        try:
            # Créer l'avis
            Review.objects.create(
                vendor=vendor,
                client=request.user,
                project=project,
                rating=rating,
                comment=comment,
                status='pending'  # En attente de modération
            )
            
            messages.success(request, "Votre avis a été soumis et sera publié après modération. Merci !")
            return redirect('vendors:vendor_detail', vendor_id=vendor.id)
            
        except Exception:
            messages.error(request, "Erreur lors de la création de l'avis. Veuillez réessayer.")
    
    return render(request, 'vendors/create_review.html', {
        'vendor': vendor,
        'eligible_projects': eligible_projects,
    })


@login_required
def vendor_response_review(request, review_id):
    """Ajouter une réponse du prestataire à un avis"""
    review = get_object_or_404(Review, id=review_id, status='approved')
    
    # Vérifier que l'utilisateur est le prestataire concerné
    if not hasattr(request.user, 'vendor_profile') or request.user.vendor_profile != review.vendor:
        messages.error(request, "Accès non autorisé.")
        return redirect('vendors:vendor_detail', vendor_id=review.vendor.id)
    
    if request.method == 'POST':
        response = request.POST.get('response', '').strip()
        
        if not response:
            messages.error(request, "Veuillez entrer une réponse.")
        else:
            review.add_vendor_response(response)
            messages.success(request, "Votre réponse a été publiée.")
        
        return redirect('vendors:vendor_detail', vendor_id=review.vendor.id)
    
    return render(request, 'vendors/vendor_response_review.html', {
        'review': review,
    })


@staff_member_required
def moderate_review(request, review_id):
    """Modérer un avis (admin uniquement)"""
    review = get_object_or_404(Review, id=review_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            review.approve(request.user)
            messages.success(request, f"Avis de {review.client.get_full_name()} approuvé.")
        
        elif action == 'reject':
            reason = request.POST.get('reason', '').strip()
            review.reject(request.user, reason)
            messages.success(request, f"Avis de {review.client.get_full_name()} rejeté.")
        
        else:
            messages.error(request, "Action invalide.")
        
        return redirect('accounts:admin_dashboard')
    
    return render(request, 'vendors/moderate_review.html', {
        'review': review,
    })


@login_required
def delete_review(request, review_id):
    """Supprimer son propre avis (client) ou n'importe quel avis (admin)"""
    review = get_object_or_404(Review, id=review_id)
    
    # Vérifier les permissions
    if review.client != request.user and not request.user.is_staff:
        messages.error(request, "Accès non autorisé.")
        return redirect('vendors:vendor_detail', vendor_id=review.vendor.id)
    
    if request.method == 'POST':
        vendor_id = review.vendor.id
        review.delete()
        messages.success(request, "Avis supprimé avec succès.")
        return redirect('vendors:vendor_detail', vendor_id=vendor_id)
    
    return render(request, 'vendors/delete_review.html', {
        'review': review,
    })
