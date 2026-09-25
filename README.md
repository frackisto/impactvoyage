# Plateforme Web Agence de Voyage — Phase 6

Backend Django + PostgreSQL + Redis + Celery, dockerisé : modèles, services métier et API REST `/api/v1/`.
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

## Serializers (Phase 5)

Chaque app a un `serializers.py` : serializers de **lecture** (cartes de liste,
pages détail) et serializers d'**entrée** qui valident les formulaires avant
l'appel au service (`serializer.validated_data` → `services.xxx(**data)`).

- **Traductions** : les champs sont renvoyés dans la langue de la requête
  (`Accept-Language`), avec repli sur le français.
- **Prix** : `{"amount": "150000.00", "currency": "XOF"}`, plus `"display"` converti
  quand le visiteur demande une autre devise (`?currency=EUR` ou en-tête `X-Currency`).
- **Aucun prix accepté en entrée** : une demande de réservation ne contient que
  l'offre, les dates et les quantités.
- **Données jamais exposées** : immatriculations, emails des auteurs d'avis et
  d'articles, jeton d'accès des devis (hors lien client).
- **Anti-spam** : champ piège `website` sur les formulaires publics.

## API REST (Phase 6)

Documentation interactive : http://localhost:8000/api/v1/docs/ (Swagger) et
`/api/v1/redoc/` ; schéma OpenAPI brut : `/api/v1/schema/`.

- **Lecture publique** du catalogue : `/destinations`, `/tours` (+ `/departures`),
  `/hotels`, `/residences`, `/vehicles` (+ `/availability`), `/activities`, `/events`,
  `/offers`, `/services`, `/visas`, `/transport`, `/blog`, `/media/albums`,
  `/categories`, `/site-settings`, `/currencies`.
- **Formulaires** : `POST /quotes/`, `/bookings/`, `/contact/`, `/reviews/`
  (débit limité par IP : 5 devis/h, 10 réservations/h, 5 messages/h, 3 avis/h).
- **Parcours client** : consultation et validation d'un devis avec le jeton reçu
  par email ; réservations du compte connecté.
- **Équipe** : devis (assignation, proposition, statut), réservations
  (confirmation, refus, annulation), notifications.
- **Paramètres** : pagination `?page=`, `?page_size=` (max 48), recherche `?search=`,
  tri `?ordering=`, filtres propres à chaque liste (documentés dans Swagger),
  langue `Accept-Language` ou `?lang=en`, devise `?currency=EUR` ou `X-Currency`.
- **Erreurs** : toujours `{"error": {"code", "message", "details"}}` — 400
  `validation_error`, 404 `not_found`, 409 `not_available` / `invalid_transition`,
  429 `throttled`…

Les droits sont pour l'instant « équipe » (tout rôle sauf client) / « client » ;
la Phase 7 les affine par rôle et ajoute l'authentification JWT (`/auth/...`).

## Ce qui a été validé (Phase 6)

- 100 tests passent, dont 19 tests d'API (parcours devis et réservation complets,
  droits, prix envoyés par le client ignorés, format d'erreur, limitation de débit).
- Schéma OpenAPI généré **sans aucun avertissement** (`spectacular --validate
  --fail-on-warn`, vérifié par un test) : il servira à générer les types TypeScript
  du frontend (Phase 8).

## Prochaine étape

**Phase 7 : Authentification JWT et permissions** — inscription, connexion,
rafraîchissement et révocation des jetons, mot de passe oublié, vérification de
l'email, permissions par rôle (commercial, gestionnaire, agent…).
