# 🔐 Identifiants de test - LysAngels

## Comptes administrateurs

### SuperUser Django Admin
- **URL** : http://127.0.0.1:8000/admin/
- **Username** : `admin`
- **Email** : admin@lysangels.tg
- **Password** : `admin123`

### Admin LysAngels (interface utilisateur)
- **Username** : `admin_test`
- **Email** : admin_test@lysangels.tg
- **Password** : `password123`
- **Type** : Administrateur LysAngels
- **Accès** : Dashboard admin + gestion complète

## Comptes de test

### Client
- **Username** : `client_test`
- **Email** : client@test.com
- **Password** : `password123`
- **Nom** : Marie Dupont
- **Ville** : Lomé
- **Fonctionnalités** :
  - Créer des projets
  - Explorer les prestataires
  - Envoyer des demandes de devis
  - Recevoir des propositions
  - Messagerie

### Prestataire
- **Username** : `provider_test`
- **Email** : provider@test.com
- **Password** : `password123`
- **Nom** : Jean Martin
- **Entreprise** : Photo & Vidéo Pro
- **Ville** : Lomé, Légbassito
- **Services** : Photographe, Vidéaste
- **Fonctionnalités** :
  - Profil prestataire
  - Recevoir des demandes
  - Envoyer des propositions
  - Messagerie

## Autres prestataires de test (50 au total)

Tous les prestataires créés automatiquement utilisent le même mot de passe :
- **Password** : `password123`
- **Username** : `vendor_1_[prenom]` à `vendor_50_[prenom]`
- **Exemples** :
  - `vendor_1_kofi` / `password123`
  - `vendor_2_ama` / `password123`
  - etc.

## Statistiques de la base de données

### Prestataires : 51 (1 manuel + 50 auto-générés)
Répartition par service :
- 📸 Photographe : 10 prestataires
- 🎨 Décoration : 9 prestataires
- 📦 Location matériel : 8 prestataires
- 🚗 Transport : 8 prestataires
- 🌺 Fleuriste : 7 prestataires
- 🍽️ Traiteur : 7 prestataires
- 🎉 Animation : 6 prestataires
- 💄 Maquillage/Coiffure : 5 prestataires
- 🏛️ Salle de réception : 5 prestataires
- 🎵 DJ/Musique : 4 prestataires
- 🎥 Vidéaste : 3 prestataires
- 🎂 Pâtisserie : 3 prestataires

### Villes couvertes : 9
- Lomé (avec 15 quartiers)
- Kara
- Sokodé
- Atakpamé
- Kpalimé
- Dapaong
- Tsévié
- Aného
- Bassar

### Types de services : 12
- Salle de réception
- Traiteur
- Décoration
- Photographe
- Vidéaste
- DJ / Musique
- Animation
- Maquillage / Coiffure
- Pâtisserie
- Location matériel
- Transport
- Fleuriste

### Types d'événements : 10
- Mariage
- Anniversaire
- Baptême
- Fiançailles
- Conférence
- Séminaire
- Gala
- Lancement de produit
- Retraite
- Autre

## Configuration du SuperUser initial

Si vous devez configurer le mot de passe pour l'admin Django :

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Définir le mot de passe
./venv/bin/python manage.py changepassword admin

# Ou créer un nouveau superuser
./venv/bin/python manage.py createsuperuser
```

## Notes de sécurité

⚠️ **IMPORTANT** : Ces identifiants sont pour le développement uniquement.

En production :
1. Changez tous les mots de passe
2. Utilisez des mots de passe forts
3. Supprimez les comptes de test
4. Configurez `DEBUG = False`
5. Définissez une `SECRET_KEY` sécurisée

## Accès rapide

### Interface utilisateur
- **Accueil** : http://127.0.0.1:8000/
- **Connexion** : http://127.0.0.1:8000/accounts/login/
- **Inscription** : http://127.0.0.1:8000/accounts/register/
- **Prestataires** : http://127.0.0.1:8000/vendors/

### Administration Django
- **Admin** : http://127.0.0.1:8000/admin/

---

*Document généré le 11 janvier 2025*
*LysAngels v1.0*
