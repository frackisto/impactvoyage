# Plateforme Web Agence de Voyage — Phase 3

Backend Django + PostgreSQL + Redis + Celery, dockerisé, avec l'ensemble des modèles métier.
Voir [architecture-plateforme-voyage.md](architecture-plateforme-voyage.md) pour l'architecture complète.

## Démarrage avec Docker (recommandé)

```bash
# 1. Copier les fichiers d'environnement
cp .env.example .env
cp backend/.env.example backend/.env
# ⚠️ Éditer les deux fichiers .env et définir le même mot de passe
#    pour DATABASE_PASSWORD, ainsi qu'une SECRET_KEY forte.

# 2. Construire et démarrer les services
docker compose up --build

# Le backend applique automatiquement les migrations au démarrage
# (voir la commande du service "backend" dans docker-compose.yml).
```

Services démarrés :
- `backend` → http://localhost:8000
- `db` → PostgreSQL sur le port 5432
- `redis` → Redis sur le port 6379
- `celery` → worker Celery (tâches asynchrones)

## Vérifier que tout fonctionne

```bash
curl http://localhost:8000/api/v1/health/
# → {"status": "ok", "service": "voyage-api"}

# Documentation Swagger
open http://localhost:8000/api/v1/docs/

# Admin Django
open http://localhost:8000/admin/
```

Créer un compte administrateur (la connexion se fait **par email**) :

```bash
docker compose exec backend python manage.py createsuperuser
```

> Depuis la Phase 3, les comptes existants se connectent avec leur **email** : le nom
> d'utilisateur a été supprimé (il est conservé dans le prénom) et les superutilisateurs
> ont reçu le rôle `SUPER_ADMIN`.

## Démarrage sans Docker (alternative)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # adapter DATABASE_HOST=localhost
python manage.py migrate
python manage.py runserver
```

Nécessite une instance PostgreSQL et Redis locales déjà démarrées.

## Lancer les tests

Les tests tournent sur PostgreSQL (contraintes d'exclusion, extensions) : la base Docker
doit être démarrée.

```bash
cd backend
pip install -r requirements-dev.txt
DATABASE_HOST=localhost pytest
```

## Structure du backend

```
backend/
├── config/
│   ├── settings/{base,dev,prod,test}.py
│   ├── urls.py, api_urls.py
│   └── wsgi.py, asgi.py, celery.py
├── apps/
│   ├── core/            # mixins (TimeStamped, Slug, SoftDelete, Publishable, Bookable,
│   │                    # Reference), Category, Tag, SiteSettings, ExchangeRate
│   ├── accounts/        # User (connexion par email, rôles)
│   ├── destinations/    # Destination + galerie
│   ├── tours/           # Tour, TourDay, TourDeparture + galerie
│   ├── accommodations/  # Hotel, Room, Residence, Amenity + galeries
│   ├── vehicles/        # Vehicle + galerie
│   ├── activities/      # Activity + galerie
│   ├── events/          # Event + photos/vidéos
│   ├── media/           # MediaAlbum, MediaItem (médiathèque)
│   ├── services/ visas/ transport/ offers/ blog/
│   ├── inquiries/       # QuoteRequest (devis), ContactMessage
│   ├── bookings/        # Booking, BookingItem (anti-surréservation en base)
│   ├── reviews/ notifications/ payments/
│   └── search/          # sans modèle (recherche transverse, Phase 16)
├── requirements.txt, requirements-dev.txt, pytest.ini
└── Dockerfile
```

Chaque app de contenu a un `translation.py` (champs traduits FR/EN via
django-modeltranslation : `title_fr`, `title_en`…).

## Ce qui a été validé (Phase 3)

- `python manage.py check` : aucune erreur ; `makemigrations --check` : aucune migration manquante.
- Migrations appliquées sur PostgreSQL 16, extensions `btree_gist`, `pg_trgm`, `unaccent` actives.
- 32 tests de modèles : capacité des départs, chevauchement des locations de véhicules,
  cible unique des lignes de réservation, références `IV-`/`DV-`, contraintes des offres,
  avis, blog, médias, traductions avec repli sur le français, connexion par email et rôles.

## Prochaine étape

**Phase 4 : Création des services métier** — `services.py` et `selectors.py` de chaque app :
cycle de vie des réservations et des devis, calcul des prix, notifications.
