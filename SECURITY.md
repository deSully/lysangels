# Sécurité LysAngels - Guide de référence

## ✅ Protections implémentées

### 1. Rate Limiting (Anti-spam)
**Middleware:** `apps.core.middleware.RateLimitMiddleware`

**Limites configurées:**
- **Login:** 5 tentatives / 5 minutes
- **Register:** 3 inscriptions / heure  
- **Password Reset:** 3 demandes / heure

**Comportement:**
- Basé sur l'IP du client
- Utilise le cache Django
- Page d'erreur 429 personnalisée

**Tester:**
```bash
# Essayer de se connecter 6 fois rapidement
# → Blocage à la 6ème tentative
```

### 2. Protection CSRF
**Décorateurs utilisés:**
- `@require_http_methods(["GET", "POST"])` - Vues mixtes
- `@require_POST` - Vues POST uniquement (logout, etc.)

**Vues protégées:**
- `register()` - Inscription
- `user_login()` - Connexion
- `user_logout()` - Déconnexion (POST only)
- `profile()` - Mise à jour profil
- `conversation_detail()` - Envoi messages

**Configuration:**
```python
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True  # Production
CSRF_COOKIE_SAMESITE = 'Lax'
```

### 3. Validation stricte des uploads

**Validateurs:** `apps.core.validators.py`

**Protections images:**
- Taille max: 5MB
- MIME types: JPEG, PNG, WebP uniquement
- Vérification via magic bytes (python-magic)
- Extensions whitelist

**Protections pièces jointes:**
- Taille max: 10MB
- MIME types: Images + PDF + Office
- Validation extension + contenu réel
- Quota utilisateur: 100MB total

**Fonctions:**
```python
validate_image_file(image)           # Images
validate_attachment_file(attachment) # Pièces jointes
check_user_storage_quota(user, size) # Quota
```

### 4. Sécurité des sessions

**Configuration:**
```python
SESSION_COOKIE_HTTPONLY = True      # Pas d'accès JavaScript
SESSION_COOKIE_SECURE = True        # HTTPS only (prod)
SESSION_COOKIE_SAMESITE = 'Lax'     # Protection CSRF
SESSION_COOKIE_AGE = 1209600        # 2 semaines
```

### 5. Headers de sécurité

```python
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

**Production (à activer avec HTTPS):**
```python
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

## 📋 Checklist avant production

### Obligatoire
- [ ] Changer `SECRET_KEY` en production
- [ ] `DEBUG = False`
- [ ] Configurer `ALLOWED_HOSTS`
- [ ] Activer HTTPS
- [ ] Configurer vrai serveur email (pas console)
- [ ] Tester rate limiting
- [ ] Vérifier uploads avec fichiers malveillants

### Recommandé
- [ ] Ajouter monitoring (Sentry, etc.)
- [ ] Logs d'erreurs en production
- [ ] Backup automatique DB
- [ ] CDN pour fichiers statiques
- [ ] Scanner de vulnérabilités

## 🔧 Maintenance

### Ajuster les limites rate limiting

Éditer `apps/core/middleware.py`:
```python
self.limits = {
    'login': {'max_attempts': 5, 'window': 300},     # Modifier ici
    'register': {'max_attempts': 3, 'window': 3600},
}
```

### Ajouter validation upload personnalisée

Ajouter dans `apps/core/validators.py`:
```python
def validate_custom_file(file):
    # Votre logique
    pass
```

Puis utiliser dans le model:
```python
file = models.FileField(validators=[validate_custom_file])
```

## 🚨 En cas d'attaque

### Rate limiting déclenché
- Utilisateur bloqué 5-60 minutes selon l'action
- Se débloque automatiquement
- Aucune action manuelle requise

### Upload malveillant détecté
- Fichier rejeté
- Erreur 400 retournée
- Aucun fichier stocké

### Tentative CSRF
- Requête bloquée par Django
- Erreur 403 retournée
- User averti

## 📊 Monitoring recommandé

### Métriques à surveiller
- Taux d'échec login (> 10% = suspect)
- Uploads rejetés par jour
- Rate limiting déclenchés/jour
- Taille totale uploads/utilisateur

### Logs à activer en production
```python
LOGGING = {
    'handlers': {
        'security': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': 'logs/security.log',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['security'],
            'level': 'WARNING',
        },
    },
}
```

## 🔗 Ressources

- [Django Security Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [python-magic docs](https://github.com/ahupp/python-magic)
