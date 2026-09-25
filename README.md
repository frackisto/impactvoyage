# Plateforme Web Agence de Voyage — Phase 4

Backend Django + PostgreSQL + Redis + Celery, dockerisé : modèles métier et services métier.
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
- `celery` → worker Celery (tâches asynchrones : emails, taux de change)
- `celery-beat` → planificateur (expiration des réservations, taux de change quotidiens)

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

## Services métier (Phase 4)

La logique métier vit dans `services.py` (écritures, transitions de statut) et
`selectors.py` (lectures optimisées) de chaque app ; les vues de la Phase 6 ne
feront qu'appeler ces fonctions.

| Module | Rôle |
|---|---|
| `bookings.services` | Demande de réservation (prix calculé côté serveur, promotions), confirmation, refus, annulation, expiration ; réserve et libère le stock sous verrou |
| `inquiries.services` | Devis : création (consentement obligatoire), assignation, proposition, validation ou refus **par le client via son lien secret** ; messages de contact |
| `reviews.services` | Dépôt d'avis et modération |
| `notifications` | Canaux extensibles (tableau de bord + email agence), emails asynchrones |
| `core.services` | Conversion FCFA → EUR/USD/GBP (parité fixe 655,957 + taux BCE) |
| `*/selectors.py` | Catalogue filtré (moteur de recherche), disponibilité des véhicules et résidences, notes moyennes |

Erreurs métier : `core.exceptions` (`BusinessError`, `NotAvailable`, `InvalidTransition`,
`InvalidToken`), chacune avec un `code` stable pour le frontend.

## Ce qui a été validé (Phase 4)

- 63 tests passent sur PostgreSQL, dont un test de **concurrence** : deux confirmations
  simultanées pour la dernière place d'un départ, une seule aboutit.
- Tâches Celery enregistrées et planifiées par `celery-beat` ; récupération réelle des
  taux de change vérifiée (100 000 FCFA = 152,45 EUR).

## Prochaine étape

**Phase 5 : Création des serializers** — sérialisation DRF des modèles (lecture publique,
champs traduits, prix convertis) et validation des entrées (devis, réservations, avis).
