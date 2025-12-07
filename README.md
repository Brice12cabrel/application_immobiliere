# MonApp — Plateforme immobilière complète (Django + JWT + Super Admin)

Application web fullstack de location et gestion immobilière avec hiérarchie complète :

### Fonctionnalités
- Inscription & connexion sécurisée avec OTP par terminal
- Système de rôles : Locataire → Bailleur (validation admin) → Admin → Super Admin
- Dashboard locataire/bailleur + Dashboard Admin + Super Admin Dashboard isolé (port séparé)
- Devenir bailleur avec upload CNI + Titre foncier
- Gestion totale des utilisateurs (créer, modifier rôle, supprimer) par le Super Admin
- Authentification JWT enrichie (role + is_superuser dans le token)


### Stack
- Backend : Django REST Framework + SimpleJWT
- Frontend : HTML/CSS/JS vanilla (design neumorphic)
- Base de données : SQLite (prêt pour PostgreSQL en prod)

