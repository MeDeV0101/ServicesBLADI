# ServicesBLADI Admin Access Guide

Ce document explique comment accéder de manière sécurisée à la section administrative de l'application ServicesBLADI.

## Création d'un Utilisateur Administrateur

Pour créer un nouvel administrateur, vous avez deux options:

### Option 1: Via le script `create_admin.py`

Exécutez le script `create_admin.py` depuis la ligne de commande:

```powershell
# Naviguer vers le répertoire du projet
cd "c:\Users\Airzo\Desktop\My Website\ServiceBladiTest2\ServicesBLADI V6\ServicesBLADIV3"

# Exécuter le script (mode interactif)
python create_admin.py

# Ou spécifier tous les détails d'un coup
python create_admin.py admin@example.com MotDePasse123 NomAdmin PrénomAdmin
```

### Option 2: Via l'interface d'administration

Un administrateur existant peut créer un nouvel administrateur via l'interface:

1. Accédez à `/admin/users/`
2. Cliquez sur "Ajouter un utilisateur"
3. Remplissez le formulaire en spécifiant le type de compte "admin"
4. Cliquez sur "Créer utilisateur"

## Accès à l'Interface d'Administration

L'interface d'administration est accessible de deux manières:

### Méthode standard

1. Connectez-vous avec votre compte administrateur sur la page `/login/`
2. Vous serez automatiquement redirigé vers le tableau de bord administrateur

### Méthode sécurisée (URL directe)

L'interface d'administration est également accessible via une URL sécurisée qui n'est pas liée publiquement depuis le site principal:

```
http://127.0.0.1:8000/admin/login/
```

Pour vous connecter, vous aurez besoin de:

1. L'email de l'utilisateur administrateur
2. Le mot de passe de l'utilisateur administrateur

## Considérations de Sécurité

La connexion administrateur comporte plusieurs mesures de sécurité:
- L'URL d'administration n'est pas liée publiquement depuis le site principal
- Toutes les pages d'administration vérifient le type de compte (`account_type = 'admin'`)
- Les tentatives de connexion échouées sont enregistrées
- La connexion depuis des adresses IP inconnues est surveillée

## Bonnes Pratiques de Sécurité

- **Mots de passe**: Utilisez des mots de passe forts d'au moins 12 caractères avec des lettres majuscules, minuscules, chiffres et symboles
- **Déconnexion**: Toujours se déconnecter après utilisation, surtout sur un ordinateur partagé
- **Vigilance phishing**: Ne jamais partager vos identifiants par email ou messagerie
- **Connexion sécurisée**: Utilisez uniquement des connexions sécurisées (HTTPS) et évitez les réseaux Wi-Fi publics

## Fonctionnalités d'Administration

Une fois connecté, vous pouvez:
- Gérer les utilisateurs (création, modification, activation/désactivation)
- Superviser les demandes de service
- Vérifier et gérer les documents
- Gérer les rendez-vous (compléter, annuler, reprogrammer)
- Gérer les ressources et la documentation (public/privé)
- Surveiller les communications

## URLs d'Administration

L'interface d'administration comporte plusieurs sections:

- **Tableau de bord**: `/admin/dashboard/`
- **Utilisateurs**: `/admin/users/`
- **Documents**: `/admin/documents/`
- **Demandes**: `/admin/demandes/`
- **Rendez-vous**: `/admin/rendezvous/`
- **Ressources**: `/admin/ressources/`
- **Messages**: `/admin/messages/`

For enhanced security, periodically change the security code in `accounts/views.py`.

## Creating Additional Admin Users

Only existing admin users can create new admin accounts through:
```
http://127.0.0.1:8000/management/secure8765/create/
```

## Best Practices

1. Use a strong password for admin accounts
2. Don't share the admin URL or security code
3. Periodically change the security code
4. Log out when you're done using the admin panel
5. Access the admin panel only from secure networks
