# Guide de l'Interface Administrateur - ServicesBLADI

Ce guide explique le fonctionnement de l'interface d'administration sécurisée qui a été implémentée pour le projet ServicesBLADI.

## Fonctionnalités

L'interface administrateur offre les fonctionnalités suivantes:

1. **Tableau de bord administrateur**:
   - Vue d'ensemble des statistiques du site
   - Graphiques et indicateurs de performance

2. **Gestion des utilisateurs**:
   - Liste de tous les utilisateurs (clients, experts, administrateurs)
   - Ajout de nouveaux utilisateurs
   - Modification des informations utilisateur
   - Activation/désactivation de comptes
   - Suppression d'utilisateurs

3. **Gestion des demandes**:
   - Liste de toutes les demandes de service
   - Filtrage par statut, catégorie, période
   - Recherche de demandes

4. **Gestion des documents**:
   - Liste de tous les documents soumis
   - Vérification et rejet des documents
   - Suppression de documents

5. **Gestion des rendez-vous**:
   - Liste de tous les rendez-vous
   - Marquage des rendez-vous comme complétés
   - Annulation de rendez-vous
   - Replanification de rendez-vous

6. **Gestion des ressources**:
   - Ajout de nouvelles ressources
   - Modification des ressources existantes
   - Changement de visibilité (publique/privée)
   - Suppression de ressources

7. **Gestion des messages**:
   - Suivi des conversations entre clients et experts

## Accès à l'Administration

Pour accéder à l'interface d'administration:

1. Connectez-vous avec un compte administrateur à l'URL: `/login/`
2. Entrez vos identifiants et le code de sécurité
3. Vous serez redirigé vers le tableau de bord administrateur à l'URL: `/admin/dashboard/`

## Sécurité

L'interface administrateur est protégée par:

1. **Authentification à deux facteurs simplifiée**:
   - Mot de passe régulier
   - Code de sécurité supplémentaire

2. **Contrôle d'accès**:
   - Toutes les pages administrateur vérifient que l'utilisateur est bien administrateur
   - Redirection vers la page d'accueil si accès non autorisé

3. **Interface isolée**:
   - L'interface d'administration utilise une mise en page distincte
   - Header et footer du site principal supprimés pour une meilleure sécurité

## Structure technique

L'interface d'administration est construite avec:

1. **Vues dynamiques**:
   - Toutes les pages administrateur utilisent des vues Django
   - Chaque vue vérifie les permissions administrateur
   - Les vues utilisent le système de pagination de Django

2. **Templates**:
   - Base template: `admin/base.html`
   - Pages spécifiques étendant cette base:
     - `admin/dashboard.html` - Tableau de bord principal
     - `admin/users.html` - Gestion des utilisateurs
     - `admin/documents.html` - Gestion des documents
     - `admin/rendezvous.html` - Gestion des rendez-vous
     - `admin/ressources.html` - Gestion des ressources
     - `admin/messages.html` - Gestion des messages

3. **URLs**:
   - Toutes les URLs administrateur sont définies dans `frontend_urls.py`
   - Format: `/admin/[section]/[action]/`

4. **Pagination**:
   - Toutes les pages de gestion incluent une pagination
   - Par défaut, 10 éléments sont affichés par page (9 pour les ressources)
   - Les filtres et paramètres de recherche sont préservés lors du changement de page

## Routes d'API pour AJAX

Des routes d'API sont disponibles pour les actions administrateur côté client:

1. **Utilisateurs**:
   - `/admin/users/add/` - Ajouter un utilisateur
   - `/admin/users/<user_id>/toggle-status/` - Activer/désactiver un utilisateur
   - `/admin/users/<user_id>/edit/` - Modifier un utilisateur
   - `/admin/users/<user_id>/delete/` - Supprimer un utilisateur

2. **Documents**:
   - `/admin/documents/<document_id>/verify/` - Vérifier un document
   - `/admin/documents/<document_id>/reject/` - Rejeter un document
   - `/admin/documents/<document_id>/delete/` - Supprimer un document

3. **Rendez-vous**:
   - `/admin/rendezvous/<appointment_id>/complete/` - Marquer comme complété
   - `/admin/rendezvous/<appointment_id>/cancel/` - Annuler un rendez-vous
   - `/admin/rendezvous/<appointment_id>/reschedule/` - Replanifier

4. **Ressources**:
   - `/admin/ressources/add/` - Ajouter une ressource
   - `/admin/ressources/<resource_id>/edit/` - Modifier une ressource
   - `/admin/ressources/<resource_id>/delete/` - Supprimer une ressource
   - `/admin/ressources/<resource_id>/toggle-visibility/` - Changer la visibilité

## Personnalisation

Pour personnaliser davantage l'interface administrateur:

1. Modifiez le template `admin/base.html` pour changer la structure générale
2. Ajoutez du CSS dans la section `{% block extra_css %}` des templates
3. Ajoutez du JavaScript dans la section `{% block extra_js %}` des templates

## Fonctionnalités avancées

### Pagination

Toutes les vues de liste dans l'interface d'administration incluent une pagination pour améliorer les performances et l'expérience utilisateur:

1. **Pagination standard**:
   - Navigation par numéro de page
   - Boutons "Première page", "Page précédente", "Page suivante", "Dernière page"
   - Affichage intelligent des numéros de page autour de la page courante

2. **Préservation des filtres**:
   - Lors de la navigation entre les pages, tous les filtres appliqués sont préservés
   - Les paramètres de recherche sont également conservés
   - Cela permet une expérience de filtrage cohérente

3. **Indication visuelle**:
   - La page courante est clairement indiquée
   - Les boutons de navigation sont désactivés lorsqu'ils ne sont pas applicables

### Filtrage et recherche

Chaque vue dispose de filtres spécifiques pour faciliter la recherche:

1. **Utilisateurs**: Filtrage par type de compte, statut et recherche textuelle
2. **Documents**: Filtrage par statut, type, client et recherche textuelle
3. **Rendez-vous**: Filtrage par date, statut, client, expert et recherche textuelle
4. **Ressources**: Filtrage par catégorie, visibilité et recherche textuelle
5. **Messages**: Filtrage par statut, période et recherche textuelle

## Dépannage

En cas de problème avec l'interface administrateur:

1. Vérifiez que l'utilisateur a bien le type de compte `admin`
2. Assurez-vous que les permissions sont correctement configurées
3. Consultez les logs pour identifier d'éventuelles erreurs
4. Vérifiez que les templates utilisent correctement la structure d'héritage de `base.html`
5. Assurez-vous que les contextes transmis aux templates contiennent les données requises
