# Architecture complète — Plateforme Web Agence de Voyage
### Django REST Framework + Next.js

> Livrable de la **Phase 1** du cahier des charges (§ 44, § 46). Les renvois « CdC § n » pointent vers les sections du cahier des charges *Impact Voyage*.

---

## 1. Vue d'ensemble

```
                    ┌──────────────────────┐
                    │       Visiteur       │
                    └──────────┬───────────┘
                               │ HTTPS
                               ▼
                    ┌──────────────────────┐
                    │        Nginx         │  TLS, gzip/brotli, /media, /static
                    └─────┬──────────┬─────┘
                          │          │
                          ▼          ▼
          ┌──────────────────────┐  ┌──────────────────────┐
          │ Next.js (App Router) │  │    Django + DRF      │
          │ TypeScript / React   │─▶│  /api/v1/  /admin/   │
          └──────────────────────┘  └──────────┬───────────┘
            REST API / JWT (cookies httpOnly)  │
                ┌──────────────────────────────┼──────────────┐
                ▼                              ▼              ▼
           PostgreSQL                        Redis     Celery worker + beat
```

- **Backend** : Python 3.13, Django 5.2 LTS, Django REST Framework, PostgreSQL 16, JWT (simplejwt), django-filter, Pillow, Celery + Redis, OpenAPI/Swagger (drf-spectacular), variables d'environnement via `.env`.
- **Frontend** : Next.js (App Router) + TypeScript strict, Tailwind CSS, shadcn/ui, Lucide React, TanStack Query, React Hook Form + Zod, Axios, next/image, next/font, next-intl.
- **Communication** : API REST versionnée (`/api/v1/`), JWT access + refresh, stockés en cookies httpOnly côté Next.js (voir § 6.1).

---

## 2. Architecture Backend (Django)

### 2.1 Arborescence

```
backend/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   ├── prod.py
│   │   └── test.py
│   ├── urls.py
│   ├── api_urls.py          # point d'entrée unique /api/v1/
│   ├── asgi.py
│   ├── wsgi.py
│   └── celery.py
├── apps/
│   ├── core/                # Base models, mixins, Category, Tag, SiteSettings, ExchangeRate
│   ├── accounts/            # Utilisateurs, rôles, permissions, auth
│   ├── destinations/        # Destinations touristiques
│   ├── tours/               # Circuits nationaux/internationaux + départs
│   ├── accommodations/      # Hôtels, chambres, résidences meublées
│   ├── vehicles/            # Location de véhicules
│   ├── activities/          # Activités touristiques
│   ├── events/              # Événementiel
│   ├── media/               # Médiathèque (photos/vidéos/albums)
│   ├── bookings/            # Réservations
│   ├── services/            # Services de l'agence
│   ├── visas/               # Services visa
│   ├── transport/           # Services transport
│   ├── inquiries/           # Devis + contact
│   ├── notifications/       # Notifications (email, dashboard, WhatsApp/SMS futur)
│   ├── reviews/             # Avis clients
│   ├── offers/              # Offres promotionnelles
│   ├── blog/                # Blog / conseils voyage
│   ├── payments/            # Préparation paiement (futur)
│   ├── search/              # Recherche globale
│   └── dashboard/           # Statistiques du tableau de bord (Phase 19)
├── locale/                  # Fichiers de traduction (.po)
├── manage.py
├── requirements.txt
└── .env.example
```

> Le CdC § 2 liste 15 apps. `core`, `offers`, `blog`, `payments`, `search` et `dashboard` sont ajoutées parce que les § 17, 21, 26, 31 et 37 en ont besoin. `dashboard` a été créée en Phase 19 (sans modèles).

### 2.2 Découpage interne de chaque app

```
tours/
├── models.py            # ou models/ si plusieurs fichiers
├── serializers.py
├── views.py             # ViewSets DRF, fins
├── services.py          # logique métier (écritures, transitions d'état)
├── selectors.py         # lectures complexes (jointures, agrégations)
├── permissions.py
├── filters.py           # django-filter
├── validators.py
├── translation.py       # champs traduits (django-modeltranslation)
├── urls.py
├── admin.py
├── apps.py
├── signals.py
├── tasks.py             # tâches Celery
├── tests/
│   ├── factories.py     # factory_boy
│   ├── test_models.py
│   ├── test_serializers.py
│   ├── test_services.py
│   ├── test_views.py
│   └── test_permissions.py
└── migrations/
```

**Principe clé** : les Views et ViewSets restent fins : ils valident l'entrée puis appellent un service. Toute la logique métier vit dans `services.py`, et une logique n'est jamais dupliquée entre deux apps. Les lectures complexes vivent dans `selectors.py`.

### 2.3 Applications Django — rôle de chacune

| App | Responsabilité |
|---|---|
| `core` | `TimeStampedModel`, `SlugMixin`, `SoftDeleteModel`, `BookableMixin`, `Category`, `Tag`, `SiteSettings`, `ExchangeRate`, permissions et exceptions de base |
| `accounts` | Utilisateur custom, rôles, JWT, profils, vérification email |
| `destinations` | Destinations par continent/pays/ville, images, attractions, conseils |
| `tours` | Circuits nationaux/internationaux, programme jour par jour, départs datés |
| `accommodations` | Hôtels, appartements, partenaires, chambres, résidences meublées |
| `vehicles` | Catalogue véhicules (1 ligne = 1 véhicule physique) |
| `activities` | Activités touristiques |
| `events` | Événementiel réalisé par l'agence |
| `media` | Albums, photos, vidéos (médiathèque) |
| `bookings` | Demandes de réservation et réservations |
| `services` | Présentation des prestations de l'agence |
| `visas` | Services visa par pays/nationalité/motif |
| `transport` | Services de transport (hors véhicules de location) |
| `inquiries` | Demandes de devis + messages de contact |
| `notifications` | Notifications internes + emails, canaux extensibles |
| `reviews` | Avis clients avec modération |
| `offers` | Offres promotionnelles avec dates de validité |
| `blog` | Articles de conseils voyage |
| `payments` | Modèles préparatoires (non actifs en V1) |
| `search` | Endpoint de recherche transverse (multi-modèles) |
| `dashboard` | KPIs et séries statistiques pour l'administration |

---

## 3. Modèles Django et relations

### 3.1 Socle commun (`core`)

```
TimeStampedModel (abstrait)  → created_at, updated_at
SlugMixin (abstrait)         → slug unique
SoftDeleteModel (abstrait)   → deleted_at + managers objects / all_objects

BookableMixin (abstrait) — offres réservables : Tour, Room, Residence, Vehicle, Activity
├── booking_mode: INSTANT | ON_REQUEST
│     INSTANT    → réservation directe, stock contrôlé par la plateforme
│     ON_REQUEST → demande de réservation, confirmée manuellement par l'agence
├── base_price  (DecimalField max_digits=12, decimal_places=2)
└── currency    (ISO 4217, défaut "XOF")

Category                     → name, slug, kind, order ; unique (kind, slug)
    kind: TOUR_THEME | ACTIVITY | BLOG | MEDIA
Tag                          → name, slug

SiteSettings (singleton, éditable dans l'admin)        CdC § 5, § 6, § 19
├── agency_name, slogan, hero_subtitle, hero_media
├── phone, email, whatsapp, address, opening_hours
├── social_links (JSON : facebook, instagram, tiktok, linkedin, youtube…)
├── latitude, longitude          → carte OpenStreetMap
└── about_content                → page « À propos »

ExchangeRate                                          CdC § 36
├── currency (EUR | USD | GBP), rate_from_xof, fetched_at
```

> En V1 (CdC § 5 et § 37), les circuits, hôtels, résidences et véhicules passent par des **demandes de réservation**. Le mode `INSTANT` est prévu pour le jour où le paiement en ligne sera branché.

### 3.2 Utilisateurs & rôles (`accounts`)

```
User (AbstractUser étendu)
├── email (unique, identifiant de connexion)
├── role: SUPER_ADMIN | ADMIN | AGENT | COMMERCIAL | GESTIONNAIRE | CLIENT
├── phone, whatsapp, country
├── avatar, preferred_language, preferred_currency
└── is_verified
```

- **Le rôle est la seule source de vérité.** Les groupes Django et leurs permissions sont dérivés du rôle par un signal et une commande `sync_roles`, jamais édités à la main (voir § 6).
- `is_staff = True` pour tous les rôles sauf `CLIENT`, pour donner accès au backoffice.

### 3.3 Contenu voyage

Tous les contenus publics ont des champs **traduits** (FR/EN au départ), voir § 12.

```
Destination                                               CdC § 8
├── name, slug, continent, country_code (ISO 3166-1), city
│     continent: AFRIQUE | EUROPE | AMERIQUES | ASIE | MOYEN_ORIENT | OCEANIE
├── description, best_period, attractions, tips
├── cover_image, cover_alt, is_featured
├── DestinationImage (FK → Destination)  [1-N]           → galerie
├── tags (M2M → Tag)
└── reverse : tours, hotels, residences, activities       → « circuits / hôtels / activités disponibles »

Tour  (BookableMixin)                                     CdC § 9, § 10
├── title, slug, description, destination (FK)
├── scope: NATIONAL | INTERNATIONAL
├── theme (FK → Category kind=TOUR_THEME)
│     patrimoine, culturel, balnéaire, nature, gastronomique, aventure, familial…
├── is_custom (circuit sur mesure)
├── duration_days, base_price, currency
├── min_travelers, max_travelers
├── departure_points, transport_info, accommodation_info
├── inclusions, exclusions, conditions
├── activities (M2M → Activity)
├── cover_image, cover_alt, is_featured
├── TourImage (FK → Tour)  [1-N]
├── TourDay (FK → Tour)  [1-N]  → day_number, title, description ; unique (tour, day_number)
└── TourDeparture (FK → Tour, CASCADE)  [1-N]            → « disponibilité », « date de départ », « période »
    │     (un départ réservé est protégé par BookingItem → PROTECT : le circuit ne peut plus être supprimé)
    ├── start_date, end_date
    ├── capacity, seats_reserved
    ├── price_override (nullable → sinon Tour.base_price)
    ├── status: OPEN | FULL | CANCELLED
    └── contraintes : seats_reserved <= capacity ; unique (tour, start_date)

Hotel                                                     CdC § 14
├── name, slug, description, destination (FK), address
├── accommodation_type: HOTEL | APARTMENT | PARTNER
├── stars (catégorie 1–5), amenities (M2M → Amenity)
├── cover_image, cover_alt
├── HotelImage (FK → Hotel)  [1-N]
└── Room (FK → Hotel)  [1-N]  (BookableMixin, ON_REQUEST)
    ├── room_type, capacity, base_price (par nuit), quantity

Residence  (BookableMixin, ON_REQUEST)                    CdC § 13
├── name, slug, description, destination (FK), address
├── rooms_count, capacity, base_price (par nuit)
├── amenities (M2M → Amenity), services, conditions
├── cover_image, cover_alt
└── ResidenceImage (FK → Residence)  [1-N]

Amenity  → name, icon (Lucide), scope (HOTEL | RESIDENCE | BOTH)

Vehicle  (BookableMixin)  → 1 ligne = 1 véhicule physique   CdC § 12
├── brand, model, slug, category, year, plate_number (unique, non exposé publiquement)
├── seats, transmission (MANUELLE | AUTOMATIQUE), fuel, air_conditioning
├── base_price (par jour), features (JSON), is_published
├── cover_image, cover_alt
└── VehicleImage (FK → Vehicle)  [1-N]
    (disponibilité calculée à partir des BookingItem, voir § 3.8)

Activity  (BookableMixin)                                 CdC § 7
├── title, slug, description, destination (FK)
├── category (FK → Category kind=ACTIVITY)
├── duration_hours, base_price, max_participants
├── cover_image, cover_alt
└── ActivityImage (FK → Activity)  [1-N]

Event                                                     CdC § 15
├── title, slug, date, location, description
├── category: VOYAGE_GROUPE | EXCURSION | PROFESSIONNEL | CULTUREL | SPORTIF | TOURISTIQUE | PRIVE
├── participants_count, partners (JSON : nom, logo, url)
├── cover_image, cover_alt
└── EventImage (FK → Event)  [1-N]  → type PHOTO | VIDEO, file ou video_url

Service                                                   CdC § 11
├── title, slug, description, icon (Lucide), order, is_active
└── quote_service_type (pré-remplit le formulaire de devis au clic sur la carte)

VisaService                                               CdC § 7, § 27
├── destination_country (ISO), country_slug (index)       → /visa/france
├── nationality (ISO), visa_type
├── purpose: TOURISME | AFFAIRES | ETUDES | FAMILLE | TRANSIT
├── validity_duration, processing_time, fees, currency
├── required_documents, description
└── unique (destination_country, nationality, visa_type, purpose)

TransportService                                          CdC § 7
├── title, slug, description
├── transport_type: TRANSFERT_AEROPORT | BUS | NAVETTE | FERRY | TRAIN | CHAUFFEUR
├── origin, destination, max_passengers
└── price_from, currency, schedule_info                   → demande via devis (date, voyageurs)

Offer                                                     CdC § 17
├── title, slug, description, conditions
├── offer_type: VOYAGE | HOTEL | CIRCUIT | BILLET | LOCATION | PACKAGE
├── initial_price, promo_price, currency
│     discount_percent → calculé (annotation), jamais saisi
├── start_date, end_date, seats_available (nullable)
├── badge: NOUVEAU | PROMOTION | POPULAIRE | DERNIERES_PLACES
│     (DERNIERES_PLACES automatique si seats_available ≤ seuil)
├── destination (FK, nullable), cover_image, cover_alt, is_active
├── cible optionnelle, FK nullables : tour, hotel, residence, vehicle, activity
│     CheckConstraint : au plus UNE renseignée (aucune pour BILLET / PACKAGE)
└── contraintes : promo_price < initial_price ; end_date >= start_date
```

### 3.4 Médiathèque (`media`)

```
MediaAlbum                                                CdC § 16
├── title, slug, description, cover
├── category (FK → Category kind=MEDIA : événements, voyages, circuits…)
├── event (FK, nullable), tour (FK, nullable)             → liens explicites, pas de GenericFK
└── published_at

MediaItem
├── album (FK → MediaAlbum)
├── type: PHOTO | VIDEO
├── file (photo) ou video_url (YouTube/Vimeo)             → pas de vidéos lourdes hébergées
├── alt_text (obligatoire pour une photo), width, height (anti-CLS), order
```

### 3.5 Interactions client

```
QuoteRequest (devis)  (SoftDeleteModel)                   CdC § 18, § 38
├── reference (unique, ex. DV-2026-000042)
├── access_token (UUID secret)       → le client consulte et valide la proposition sans compte
├── first_name, last_name, email, phone, whatsapp, country
├── destination (texte libre + FK Destination nullable)
├── date_departure, date_return, adults, children
├── travel_type, budget, currency
├── accommodation_pref, transport_pref, activities (M2M → Activity)
├── services_requested (ArrayField) : VOL | HEBERGEMENT | VISA | ASSURANCE | TRANSPORT | LOCATION | ACTIVITES
├── comments
├── source_tour / source_offer (FK nullables)   → devis lancé depuis une fiche
├── assigned_to (FK → User, commercial)
├── proposal_amount, proposal_message, proposal_sent_at, proposal_valid_until
├── language, consent_at (consentement au traitement des données)
└── status: NOUVELLE | EN_COURS | DEVIS_ENVOYE | ACCEPTEE | REFUSEE | TERMINEE

Booking  (TimeStampedModel, SoftDeleteModel)              CdC § 12, § 13, § 22
├── reference (unique, ex. IV-2026-000123) → exposée dans l'API à la place de l'id
├── access_token (UUID secret)       → le client suit et annule sa réservation sans compte
├── user (FK, nullable si invité, SET_NULL)
├── contact_name, contact_email, contact_phone   (copie, obligatoire même pour un user)
├── quote (OneToOne → QuoteRequest, nullable)   → devis accepté à l'origine de la réservation
├── status: REQUESTED | PENDING | CONFIRMED | COMPLETED | CANCELLED | REJECTED | EXPIRED
├── expires_at (nullable)   → fin de blocage d'un PENDING
├── customer_comments, internal_notes, language, consent_at
├── total_amount, currency  (calculés par le service, jamais envoyés par le client)
└── BookingItem (FK → Booking, CASCADE)  [1-N]
    ├── tour_departure (FK → TourDeparture, PROTECT, nullable)
    ├── room           (FK → Room, PROTECT, nullable)
    ├── residence      (FK → Residence, PROTECT, nullable)
    ├── vehicle        (FK → Vehicle, PROTECT, nullable)
    ├── activity       (FK → Activity, PROTECT, nullable)
    │     └── CheckConstraint : exactement UNE de ces FK est renseignée
    ├── label, unit_price, quantity, line_total   → copie figée au moment de la réservation
    ├── start_date, end_date   (end_date exclusive : jour de restitution / de départ)
    ├── pickup_location, dropoff_location (nullable, véhicules)
    └── is_blocking (bool)     → True seulement si la réservation parente est PENDING ou CONFIRMED
                                 (dénormalisé pour la contrainte d'exclusion, voir § 3.8)

ContactMessage                                            CdC § 19
├── name, email, phone, subject, message
└── status: NOUVEAU | LU | TRAITE | ARCHIVE

Review                                                    CdC § 20
├── author_name, author_email (non public), rating (CheckConstraint 1–5), comment
├── destination / tour / hotel / activity (FK nullables)  → affichage sur les pages concernées
├── photo (optionnel)
├── is_featured (affichage accueil)
└── status: EN_ATTENTE | APPROUVE | REFUSE

Notification                                              CdC § 30
├── recipient (FK → User, staff)
├── event: QUOTE_CREATED | BOOKING_REQUESTED | CONTACT_RECEIVED | REVIEW_SUBMITTED | …
├── title, message, link (URL admin), is_read
└── related_object (GenericFK, seul usage toléré : aucune intégrité critique)

BlogPost                                                  CdC § 21
├── title, slug, excerpt, content, cover_image, cover_alt
├── author (FK → User), category (FK → Category kind=BLOG)
│     conseils voyage, visa, destinations, culture, sécurité, transport, bons plans, actualités
├── tags (M2M → Tag), seo_title, seo_description
├── status: BROUILLON | PUBLIE, published_at, reading_time
```

### 3.6 Paiement — préparation future (`payments`)

```
Payment                                                   CdC § 37
├── booking (FK → Booking), amount, currency, status, method

PaymentTransaction
├── payment (FK), provider, provider_reference (unique), status, raw_response (JSON), created_at

PaymentMethod  (enum : MOBILE_MONEY, ORANGE_MONEY, MTN_MOMO, WAVE, CARTE, STRIPE, AGENCE)
PaymentStatus  (enum : PENDING, PAID, FAILED, REFUNDED)
```

> Ces modèles sont créés dès la Phase 3 mais ne sont pas branchés à un flux de paiement en V1. Chaque prestataire sera un *adapter* (`payments/providers/<nom>.py`) derrière une interface commune. Les webhooks sont idempotents grâce à `provider_reference` unique.

### 3.7 Champs et pratiques communes

- `SlugField(unique=True)` sur toutes les entités publiques (URLs SEO-friendly). En V1, le slug est commun à toutes les langues (`/en/destinations/cote-divoire`) ; des slugs traduits pourront être ajoutés sans casser les URLs existantes.
- Pays et nationalités stockés en **codes ISO 3166-1** ; le frontend affiche leur nom dans la langue du visiteur (`Intl.DisplayNames`), sans traduction à maintenir.
- `TimeStampedModel` hérité partout, `SoftDeleteModel` pour Booking et QuoteRequest.
- Index sur les champs de filtre fréquents : `destination`, `status`, `scope`, `continent`, `start_date`, `category`, `is_featured`.
- Montants : toujours `DecimalField(max_digits=12, decimal_places=2)` + `currency` ISO 4217, jamais de `FloatField`.
- Relations explicites (FK) préférées aux `GenericForeignKey`, qui ne permettent ni intégrité référentielle, ni contrainte, ni jointure efficace. Seule exception : `Notification.related_object`.
- Chaque image a son `alt_text`, avec `width` et `height` stockés pour éviter le CLS.

### 3.8 Réservation et disponibilité

Objectif : rendre la **double réservation impossible**, y compris en cas de requêtes concurrentes ou de bug applicatif.

**Cycle de vie d'une réservation**

```
 Demande (ON_REQUEST, V1)
 (visiteur) ──▶ REQUESTED ──accept_request()──▶ CONFIRMED ──(date passée)──▶ COMPLETED
                   │                               │
                   │ reject_request()              │ cancel_booking()
                   ▼                               ▼
                REJECTED                       CANCELLED

 Réservation directe (INSTANT, futur paiement en ligne)
 (client) ──▶ PENDING ──confirm_booking()──▶ CONFIRMED ──▶ …
                 │ expires_at dépassé
                 ▼
              EXPIRED
```

- Une **demande** (`REQUESTED`) ne bloque pas le stock. Deux visiteurs peuvent demander le même véhicule aux mêmes dates ; c'est la **confirmation** qui réserve, et la base refuse la seconde confirmation.
- Un `PENDING` bloque le stock jusqu'à `expires_at` : 30 min en paiement direct, 48 h après acceptation d'un devis.
- Toute transition passe par `bookings/services.py`, jamais de `booking.status = ...` dans une view ou un serializer. Le service met à jour `is_blocking` et le stock (`seats_reserved`) dans la même transaction, puis déclenche les notifications.

**Garanties par type d'offre**

| Offre | Mécanisme anti-surréservation |
|---|---|
| Circuit (`TourDeparture`) | `transaction.atomic()` + `select_for_update()` sur le départ, vérification puis incrément de `seats_reserved`. Filet de sécurité en base : `CheckConstraint(seats_reserved <= capacity)`. |
| Véhicule | `ExclusionConstraint` PostgreSQL sur `BookingItem` : `(vehicle =, daterange(start_date, end_date, '[)') &&)` avec `condition = Q(is_blocking=True)`. Deux locations actives qui se chevauchent sont refusées par la base. |
| Activité | Contrôle de `max_participants` dans le service. Le même principe que les circuits s'appliquera si une notion de session est ajoutée. |
| Hôtel / Résidence | `ON_REQUEST` en V1 : pas de stock nuit par nuit, confirmation manuelle par l'agence. |

**Parcours devis → réservation (CdC § 38)**

```
Visiteur ──▶ QuoteRequest NOUVELLE ──▶ EN_COURS (commercial assigné)
                                           │ send_proposal()  → email avec lien /devis/{reference}?token=…
                                           ▼
                                      DEVIS_ENVOYE
                                           │ le client valide via le lien (access_token)
                                           ▼
                                      ACCEPTEE ──▶ crée Booking(status=PENDING, quote=…, expires_at=+48h)
                                                   avec les BookingItem chiffrés par le commercial
```

**Règles de prix**

- Le prix est **toujours recalculé côté serveur** (`TourDeparture.price_override` ou `base_price`, promotions `Offer` actives) puis copié dans `BookingItem.unit_price`. Le client n'envoie que l'offre, les dates et les quantités.
- Une modification ultérieure du catalogue ne modifie jamais une réservation existante.

---

## 4. Architecture Frontend (Next.js)

### 4.1 Arborescence

```
frontend/
├── app/
│   ├── [locale]/                          # fr (défaut, sans préfixe) | en → /en/...
│   │   ├── layout.tsx                     # <html lang dir> (dir="rtl" prêt pour l'arabe)
│   │   ├── page.tsx                       # Accueil
│   │   ├── not-found.tsx
│   │   ├── error.tsx
│   │   ├── destinations/
│   │   │   ├── page.tsx
│   │   │   └── [slug]/page.tsx
│   │   ├── circuits/
│   │   │   ├── nationaux/page.tsx
│   │   │   ├── internationaux/page.tsx
│   │   │   └── [slug]/page.tsx
│   │   ├── services/page.tsx
│   │   ├── offres/
│   │   │   ├── page.tsx
│   │   │   └── [slug]/page.tsx
│   │   ├── hotels/                        # hôtels, appartements, partenaires + résidences
│   │   │   ├── page.tsx
│   │   │   └── [slug]/page.tsx
│   │   ├── residences/
│   │   │   ├── page.tsx
│   │   │   └── [slug]/page.tsx
│   │   ├── vehicules/
│   │   │   ├── page.tsx
│   │   │   └── [slug]/page.tsx
│   │   ├── activites/
│   │   │   ├── page.tsx
│   │   │   └── [slug]/page.tsx
│   │   ├── transport/page.tsx
│   │   ├── visa/
│   │   │   ├── page.tsx
│   │   │   └── [country]/page.tsx         # /visa/france
│   │   ├── evenements/
│   │   │   ├── page.tsx
│   │   │   └── [slug]/page.tsx
│   │   ├── mediatheque/page.tsx
│   │   ├── blog/
│   │   │   ├── page.tsx
│   │   │   └── [slug]/page.tsx
│   │   ├── recherche/page.tsx             # résultats de la recherche globale
│   │   ├── a-propos/page.tsx
│   │   ├── contact/page.tsx
│   │   ├── devis/
│   │   │   ├── page.tsx                   # formulaire
│   │   │   └── [reference]/page.tsx       # proposition + validation client (token)
│   │   ├── reservation/
│   │   │   ├── page.tsx                   # demande préremplie depuis une fiche
│   │   │   └── [reference]/page.tsx       # suivi + annulation client (token)
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   ├── register/page.tsx
│   │   │   ├── forgot-password/page.tsx
│   │   │   └── reset-password/page.tsx
│   │   ├── (compte)/
│   │   │   └── profile/page.tsx           # /profile (CdC § 24)
│   │   ├── mentions-legales/page.tsx
│   │   ├── confidentialite/page.tsx
│   │   └── conditions-generales/page.tsx
│   ├── api/auth/[...action]/route.ts      # BFF : pose/lit les cookies httpOnly JWT
│   ├── sitemap.ts
│   └── robots.ts
├── components/
│   ├── ui/                  # composants shadcn/ui de base
│   ├── layout/              # Header sticky, Footer, MobileMenu, LanguageSwitcher, CurrencySwitcher
│   ├── common/              # EmptyState, ErrorState, Skeletons, Price, Badge, Rating, Pagination
│   ├── home/                # HeroSection, SearchWidget (onglets), Highlights, Testimonials
│   ├── search/              # Formulaires par onglet, filtres, tri, résultats
│   ├── destinations/
│   ├── tours/
│   ├── hotels/
│   ├── vehicles/
│   ├── offers/
│   ├── events/
│   ├── media/               # Galerie masonry, Lightbox
│   ├── reviews/
│   ├── booking/             # Formulaires de demande de réservation / devis
│   └── seo/                 # JsonLd (TouristTrip, Hotel, Event…)
├── services/                # Clients API (Axios) par domaine
│   ├── destinations.service.ts
│   ├── tours.service.ts
│   └── ...
├── hooks/                   # useDestinations, useSearch, useAuth, useCurrency...
├── lib/                     # instance axios, utils, constantes, formatage prix/dates
├── i18n/                    # config next-intl + messages/{fr,en}.json
├── types/
│   └── api.d.ts             # GÉNÉRÉ depuis /api/v1/schema/ (openapi-typescript)
├── proxy.ts                 # (ex-middleware, Next 16) locale + routes privées + refresh JWT
└── public/
```

### 4.2 Principes d'architecture frontend

- **Server Components par défaut** pour afficher le contenu (SEO, performance). **Client Components** uniquement pour l'interactivité : formulaires, filtres, carrousel, lightbox, sélecteurs de langue et de devise.
- **TanStack Query** pour le cache et la synchronisation côté client (recherche instantanée, pagination, filtres dynamiques).
- **React Hook Form + Zod** pour tous les formulaires, avec double validation : le frontend pour l'UX, le backend pour la sécurité.
- **Services API** centralisés dans `services/`, jamais d'appel Axios direct dans un composant.
- **Types générés** : `npm run api:types` régénère `types/api.d.ts` depuis le schéma OpenAPI de drf-spectacular. Aucun type d'API n'est écrit à la main, `any` est interdit.
- **États systématiques** : `loading.tsx` avec skeletons, `error.tsx`, état vide (« aucun résultat ») pour chaque liste (CdC § 4, § 7).
- **Aucun secret dans le frontend** : seules les variables `NEXT_PUBLIC_*` non sensibles (URL publique de l'API) sont exposées.

### 4.3 Charte graphique

Couleurs du logo *Impact Voyage et Logistique* : bleu `#1F8FC4` (palette `ocean`) et orange `#F89832` (palette `sunset`), déclinées en nuances OKLCH dans `frontend/app/globals.css`. Rôles : `primary` = `ocean-600` (texte blanc, 4,7:1), `cta` = orange du logo avec texte bleu nuit `ocean-950` (7,2:1), texte courant `ocean-950`. Typographies : Fredoka (titres, arrondis comme le logo), Nunito (texte), Dancing Script (slogan « Voyagez, Rêvez, Explorez. »). L'emblème du logo (personnage et avion) sert d'icône et de logo compact ; le logo complet est réservé aux grands formats. Référence visuelle interne : `/charte-graphique` (non indexée).

### 4.4 Responsive et accessibilité (CdC § 34, § 35)

- Conception *mobile-first* : menu hamburger, cartes sur une colonne, formulaires simplifiés, boutons d'au moins 44 × 44 px, galerie optimisée.
- Objectif **WCAG 2.2 niveau AA** : navigation clavier complète, `focus-visible` apparent, labels sur tous les champs, messages d'erreur reliés aux champs (`aria-describedby`), contrastes ≥ 4,5:1, textes alternatifs obligatoires, `aria-label` sur les boutons-icônes.
- Propriétés CSS *logiques* uniquement (`ms-*`/`me-*`, `ps-*`/`pe-*` de Tailwind) pour que l'arabe (RTL) fonctionne sans réécriture.
- Contrôle automatique : `eslint-plugin-jsx-a11y` et `@axe-core/playwright` dans les tests E2E.

---

## 5. Architecture API REST

### 5.1 Conventions

```
/api/v1/<ressource>/
/api/v1/<ressource>/{slug}/
```

- **Pagination** : `{ "count", "next", "previous", "results" }` (PageNumberPagination, 12 par page, `?page_size=` plafonné à 48).
- **Erreurs** : format unique, produit par un `EXCEPTION_HANDLER` custom dans `core` :
  `{ "error": { "code": "validation_error", "message": "…", "details": { "champ": ["…"] } } }`
- **Langue** : `Accept-Language` (ou `?lang=`) ; les champs traduits sont renvoyés dans la langue demandée.
- **Filtres, recherche, tri** : `django-filter`, `SearchFilter`, `OrderingFilter` sur chaque liste ; permissions par action.

### 5.2 Endpoints

```
/api/v1/auth/register/  login/  refresh/  logout/
/api/v1/auth/verify-email/  verify-email/resend/
/api/v1/auth/password-reset/  password-reset/confirm/  password/change/
/api/v1/auth/me/                                   # profil (GET/PATCH)

/api/v1/site-settings/                             # coordonnées agence, réseaux, hero
/api/v1/currencies/                                # taux XOF → EUR/USD/GBP
/api/v1/categories/?kind=

/api/v1/destinations/          /{slug}/
/api/v1/tours/                 /{slug}/   /{slug}/departures/
/api/v1/hotels/                /{slug}/
/api/v1/residences/            /{slug}/
/api/v1/vehicles/              /{slug}/   /{slug}/availability/?start=&end=
/api/v1/activities/            /{slug}/
/api/v1/events/                /{slug}/
/api/v1/offers/                /{slug}/
/api/v1/services/
/api/v1/visas/                 /{country_slug}/
/api/v1/transport/             /{slug}/
/api/v1/blog/                  /{slug}/
/api/v1/media/albums/          /{slug}/

/api/v1/quotes/                                    # POST public (throttle "quotes") ; GET staff
/api/v1/quotes/{reference}/?token=                 # client (jeton) ou staff (fiche complète)
/api/v1/quotes/{reference}/accept/  decline/       # client, jeton dans le corps
/api/v1/quotes/{reference}/send-proposal/  assign/  status/   # staff
/api/v1/bookings/                                  # POST public : demande ; GET : les siennes / toutes (staff)
/api/v1/bookings/{reference}/?token=              # lookup par référence, jamais par id ; client (jeton), propriétaire ou staff
/api/v1/bookings/{reference}/confirm/  reject/     # staff
/api/v1/bookings/{reference}/cancel/               # client (jeton ou compte, avant confirmation) ou staff
/api/v1/contact/                                   # POST public (throttle "contact")
/api/v1/reviews/?target_type=&target_slug=&featured=   # GET avis validés ; POST (throttle "reviews")
/api/v1/notifications/  {id}/read/  read-all/  unread-count/   # staff

/api/v1/search/?q=&type=&destination=&category=&min_price=&max_price=&date=&tags=
/api/v1/dashboard/stats/                           # staff
/api/v1/schema/   /api/v1/docs/   /api/v1/redoc/   # OpenAPI
```

---

## 6. Authentification et permissions

### 6.1 Authentification (CdC § 24)

- JWT via `djangorestframework-simplejwt` : access 15 min, refresh 7 jours, **rotation + blacklist** (déjà configurés en Phase 2).
- Clé de signature dédiée `JWT_SIGNING_KEY`, distincte de `SECRET_KEY` (CdC § 29 : « JWT_SECRET »).
- **Stockage des jetons** : jamais dans `localStorage`. Les Route Handlers Next.js (`app/api/auth/…`) servent de *BFF* : ils appellent Django et posent les jetons en cookies `httpOnly; Secure; SameSite=Lax`. Les Server Components lisent le cookie, et le navigateur n'a jamais accès au jeton.
- Vérification de l'email à l'inscription (`is_verified`), réinitialisation du mot de passe par lien signé à durée limitée.
- Routes privées protégées côté Next.js (`proxy.ts`) **et** côté Django (permissions DRF). Seul Django fait autorité.

### 6.2 Rôles (CdC § 23)

```
SUPER_ADMIN   → accès total, paramètres système
ADMIN         → gestion complète sauf paramètres système critiques
AGENT         → contenu : destinations, circuits, hôtels, activités, blog, médiathèque
COMMERCIAL    → devis, réservations, contacts
GESTIONNAIRE  → opérationnel : véhicules, résidences, événements, offres, avis
CLIENT        → son compte, ses devis et réservations uniquement
```

### 6.3 Permissions granulaires

```
destinations.view / .create / .update / .delete
tours.view / .create / .update / .delete
bookings.view / .update
quotes.view / .update
…
```

- Le mapping rôle → permissions est défini **dans le code** (`accounts/roles.py`), versionné et testé ; `SUPER_ADMIN` est superutilisateur Django, `ADMIN` a tout sauf l'écriture des paramètres du site et des paiements. La commande `sync_roles` crée ou met à jour un groupe Django par rôle, et un signal réaffecte le groupe quand le rôle change.
- Côté DRF : une classe `HasPermission("tours.update")` par action. Côté admin : les permissions Django natives, dérivées des mêmes groupes.
- Un CLIENT ne voit que ses objets (filtrage du queryset par `user`, jamais seulement une vérification après coup).

---

## 7. PostgreSQL, Redis, Celery

### 7.1 PostgreSQL

- Une base unique en V1, indexée sur les champs de recherche et de filtre fréquents.
- `select_related` (FK) et `prefetch_related` (M2M, reverse FK) systématiques dans les selectors. Les tests vérifient le nombre de requêtes (`assertNumQueries`) sur les listes.
- Extensions activées par migration : `btree_gist` (contrainte d'exclusion véhicules), `pg_trgm` et `unaccent` (recherche tolérante aux fautes et aux accents : « cote divoire » trouve « Côte d'Ivoire »). `django.contrib.postgres` ajouté à `INSTALLED_APPS`.
- Recherche globale : `SearchVector` pondéré (titre > description) + similarité trigramme, avec index GIN.
- Les contraintes métier critiques (stock, chevauchement, cohérence des FK, notes 1–5, prix promo) sont portées **par la base**.
- Sauvegarde quotidienne (`pg_dump`), conservée 30 jours, avec un test de restauration mensuel.

### 7.2 Redis

| Base | Usage |
|---|---|
| 0 | Broker Celery |
| 1 | Résultats Celery |
| 2 | Cache Django : listes publiques, taux de change, compteurs du rate limiting DRF (déjà configuré) |

- Invalidation du cache par signal `post_save` / `post_delete` sur les modèles publics.
- Compteurs de vues (`view_count`) incrémentés dans Redis puis agrégés en base par une tâche Celery : on évite une écriture SQL par visite.

### 7.3 Celery — tâches asynchrones

```
send_quote_confirmation_email        # client
send_quote_notification_to_agency    # agence (email + Notification dashboard)
send_quote_proposal_email            # lien de validation /devis/{reference}?token=
send_booking_request_notification
send_booking_status_email            # confirmée / refusée / annulée
send_contact_notification
send_review_notification
generate_image_variants              # thumbnails + WebP à l'upload
```

Tâches périodiques (Celery Beat) :

```
expire_pending_bookings      # toutes les 5 min : PENDING dont expires_at est dépassé → EXPIRED
complete_past_bookings       # quotidienne : CONFIRMED dont la date de fin est passée → COMPLETED
update_exchange_rates        # quotidienne : taux XOF → EUR/USD/GBP (le XOF est arrimé à l'EUR : 655,957)
flush_view_counters          # toutes les 15 min : compteurs Redis → base
```

**Canaux de notification extensibles (CdC § 30)** : `notifications/channels.py` définit une interface `send(alert)` (une `StaffAlert` : événement, titre, message, récapitulatif, lien vers l'admin, Reply-To) implémentée par `DashboardChannel` et `AgencyEmailChannel`, actifs par défaut. `WhatsAppChannel` et `SmsChannel` sont prêts (Phase 20) : on les active dans le réglage `STAFF_NOTIFICATION_CHANNELS` et on branche un prestataire dans `SHORT_MESSAGE_BACKEND` (une classe `send(channel, to, text)`), sans toucher aux apps métier.

**Emails (Phase 20)** : les apps construisent un objet `Email` (titre, paragraphes, récapitulatif, bouton) dans la langue du client (`bookings/emails.py`, `inquiries/emails.py`, `accounts/emails.py`) ; `notifications/emails.py` le met en page (`templates/emails/message.{html,txt}`) et l'envoie en multipart par Celery après validation de la transaction. En développement, Mailpit capture les emails ; `manage.py preview_emails` écrit un aperçu de chacun.

---

## 8. Stratégie de stockage des médias

```
media/
├── destinations/
├── tours/
├── hotels/
├── residences/
├── vehicles/
├── activities/
├── events/
├── offers/
├── blog/
└── mediatheque/
```

- Image principale + galerie par entité, `alt_text` obligatoire (SEO + accessibilité).
- Fichiers renommés en UUID à l'upload : pas de nom fourni par l'utilisateur, pas d'énumération.
- Variantes générées par Celery : 400, 800 et 1600 px, en WebP + original compressé. `next/image` sert la taille adaptée.
- **Limites** : images JPEG, PNG ou WebP de 5 Mo maximum, avec contrôle de l'extension **et** du contenu réel (Pillow `verify()`). Les vidéos passent par un lien YouTube/Vimeo, pas par un upload.
- Nginx sert `/media/` sans exécution de script, avec l'en-tête `X-Content-Type-Options: nosniff`.
- Évolution possible : stockage S3-compatible via `django-storages`, sans changer les modèles.

---

## 9. Stratégie SEO (CdC § 27)

- Metadata dynamiques par page (`generateMetadata`) : title, description, Open Graph, Twitter Cards, canonical, **hreflang** FR/EN.
- `sitemap.xml` (un par langue) et `robots.txt` générés dynamiquement.
- JSON-LD Schema.org via `components/seo/` : `TouristTrip`, `TouristDestination`, `Hotel`, `LocalBusiness` (alimenté par `SiteSettings`), `Organization`, `Article`, `Event`, `BreadcrumbList`, `AggregateRating` pour les avis approuvés.
- URLs SEO-friendly : `/destinations/cote-divoire`, `/circuits/decouverte-de-la-cote-divoire`, `/hotels/abidjan`, `/visa/france`, et leurs équivalents `/en/...`.
- Pages statiques régénérées à la demande (ISR) : un signal Django appelle un webhook Next.js (`revalidateTag`) quand un contenu est publié ou modifié.

---

## 10. Performance (CdC § 28)

- Objectifs Core Web Vitals (75ᵉ percentile mobile) : **LCP < 2,5 s, CLS < 0,1, INP < 200 ms**.
- Server Components + ISR, `next/image` (tailles et `priority` sur l'image hero), `next/font` (pas de décalage de police), lazy loading des galeries.
- Cache Redis côté API, en-têtes `Cache-Control` sur les listes publiques, compression gzip/brotli par Nginx.
- Requêtes Django optimisées (§ 7.1), pagination partout.
- Lighthouse CI sur les pages clés à chaque build.

---

## 11. Stratégie de sécurité (OWASP, CdC § 29)

- HTTPS obligatoire (HSTS), `SECURE_PROXY_SSL_HEADER` derrière Nginx, CORS limité au domaine du frontend, `CSRF_TRUSTED_ORIGINS` en production.
- Protection CSRF, XSS (échappement React, contenu blog nettoyé avec `nh3`), injection SQL (ORM, aucun SQL brut non paramétré).
- En-têtes : `Content-Security-Policy`, `Referrer-Policy`, `Permissions-Policy` (posés par Next.js et Nginx).
- **Rate limiting** DRF (déjà configuré en Phase 2) : anon 120/min, user 300/min, auth 10/min, devis 5/h, contact 5/h, avis 3/h. Les pages étant rendues par Next.js, le serveur Next.js s'identifie auprès de Django par un secret partagé (`FRONTEND_SHARED_SECRET`) et transmet l'adresse réelle du visiteur (`X-Client-IP`) : les limites s'appliquent à chaque visiteur, les lectures publiques mises en cache par Next.js ne sont pas limitées par Django (limitation des pages par Nginx), les écritures le sont toujours. `X-Forwarded-For` n'est lu que derrière un proxy déclaré (`NUM_PROXIES`). Voir `apps/core/throttling.py` (Phase 15).
- **Anti-spam** des formulaires publics (devis, contact, avis, inscription) : champ *honeypot* + **Cloudflare Turnstile**, vérifié côté Django.
- Validation systématique côté backend, permissions strictes par action (§ 6.3).
- Uploads contrôlés : extension, MIME réel, taille, renommage (§ 8).
- Secrets exclusivement dans `.env`, jamais commités (`SECRET_KEY`, `DATABASE_PASSWORD`, `JWT_SIGNING_KEY`, clés API), avec un `.env.example` fourni. `SECRET_KEY` sans valeur par défaut en production.
- Admin Django sur une URL non standard, avec 2FA pour le staff (`django-otp`).
- **Données personnelles** : consentement explicite sur les formulaires, page confidentialité, durée de conservation définie, suppression sur demande. Conformité à la loi ivoirienne n° 2013-450 (ARTCI) et au RGPD pour les visiteurs européens.

---

## 12. Internationalisation et devises (CdC § 36)

- **Langues initiales FR/EN**, architecture prête pour ES, PT et AR.
  - Backend : `LANGUAGES` et `LocaleMiddleware` (configurés en Phase 2). Contenus traduits avec **django-modeltranslation** : une colonne par langue (`title_fr`, `title_en`…), déclarée dans `translation.py`. Ajouter une langue = une ligne dans `LANGUAGES` + une migration.
  - Frontend : **next-intl**, segment `[locale]` ; le français est la langue par défaut, sans préfixe.
  - Arabe : `dir="rtl"` sur `<html>` + propriétés CSS logiques dès le départ (§ 4.3).
- **Devises** : les prix sont saisis et stockés en **FCFA (XOF)**. EUR, USD et GBP servent à l'affichage, convertis avec `ExchangeRate` (mis à jour chaque jour) et arrondis. Le choix de devise est mémorisé dans un cookie. Les montants contractuels (devis, réservation) restent dans la devise de référence.

---

## 13. Backoffice et tableau de bord (CdC § 22, § 31)

- **Django admin** thémé avec `django-unfold` (interface moderne, responsive) : CRUD complet de tous les contenus, inlines pour les galeries, le programme jour par jour et les départs, filtres par statut, actions groupées (approuver/refuser des avis, changer le statut d'un devis).
- **Tableau de bord** (page d'accueil de l'admin), alimenté par `dashboard/selectors.py` et mis en cache 5 min :
  - KPIs : demandes de devis, réservations, circuits, destinations, hôtels, véhicules, offres actives, messages non lus, avis en attente ;
  - graphiques (Chart.js) : devis par mois, réservations par mois, destinations et circuits populaires (`view_count` + réservations), chiffre d'affaires quand le paiement existera.
- **Nombre de visiteurs** : **Umami** auto-hébergé (open source, sans cookie, compatible RGPD, stocke ses données dans PostgreSQL). Le dashboard lit son API. Django ne journalise pas lui-même les visites.

Mise en œuvre (Phase 19) :

- `apps/core/admin.py` porte le socle : classes de base unfold + modeltranslation (un champ par langue), aperçus d'image, publication groupée, suppression logique, et les **pages de décision** : toute action qui change un statut passe par un formulaire POST puis par le service métier ; une `BusinessError` s'affiche sur la page. Les fiches pilotées par les services (réservation, devis, message, avis) n'enregistrent que les champs modifiés, pour ne jamais écraser un statut changé entre-temps.
- Les actions de détail ne sont proposées que si le rôle a le droit de modification **et** si le statut permet la transition (`ALLOWED_TRANSITIONS`, `QUOTE_TRANSITIONS`).
- `apps/dashboard/` : `selectors.py` (statistiques en cache, listes « à traiter » sans cache), `navigation.py` (menu filtré par les permissions du rôle, pastilles de travail en attente), `umami.py` (lecture facultative de l'API Umami), `views.py` (contexte de `templates/admin/index.html`).
- Comptes : les groupes Django sont retirés de l'admin (dérivés du rôle) ; seul un `SUPER_ADMIN` attribue ce rôle ou modifie un tel compte.

---

## 14. Données de démonstration et tests (CdC § 39, § 40)

- **Seeders** : `python manage.py seed_demo [--reset]`, idempotent. Il crée des destinations africaines et internationales, des circuits avec leurs départs, des hôtels, résidences, véhicules, activités, offres, événements, les 10 services du CdC § 11, des avis et des comptes pour chaque rôle. Les données sont fictives mais cohérentes (prix en FCFA, villes réelles). Il est interdit en production.
- **Tests backend** : `pytest` + `pytest-django` + `factory_boy`, couvrant modèles, serializers, API, authentification, permissions (matrice rôle × action) et services métier. Les tests de concurrence des réservations passent par `TransactionTestCase` sur PostgreSQL. Objectif de couverture : ≥ 80 % sur `services.py` et `permissions.py`.
- **Tests frontend** : Vitest + Testing Library pour les composants critiques (formulaires, filtres, pagination), Playwright pour les parcours E2E (inscription, connexion, recherche, devis, demande de réservation) avec contrôle d'accessibilité axe.
- CI : lint (ruff, eslint), types (mypy léger, `tsc --noEmit`), tests, build.

---

## 15. Stratégie de déploiement (CdC § 42)

```
Backend  : Django + Gunicorn + Nginx + PostgreSQL + Redis + Celery (worker + beat)
Frontend : Next.js (build standalone)
Analytics: Umami
```

- `docker-compose.yml` (dev) + `docker-compose.prod.yml` : `frontend`, `backend`, `postgres`, `redis`, `celery`, `celery-beat`, `nginx`, `umami`.
- En production : seuls les ports 80 et 443 de Nginx sont exposés (PostgreSQL et Redis restent sur le réseau interne), Gunicorn sans `--reload`, TLS Let's Encrypt, `restart: unless-stopped`, healthchecks.
- Variables d'environnement séparées par environnement (`dev`, `prod`, `test`).
- Au déploiement : `migrate`, `collectstatic`, `sync_roles`. `seed_demo` uniquement en recette.

---

## 16. Documentation (CdC § 41)

README, `.env.example` (backend, frontend, racine), `requirements.txt`, `package.json`, documentation API (Swagger `/api/v1/docs/`, ReDoc), ce document d'architecture, guide d'installation (Django, Next.js, PostgreSQL, Redis, Celery, variables d'environnement, migrations, seeders, lancement local) et guide de déploiement.

---

## 17. Plan de développement (CdC § 44)

| Phase | Contenu | État |
|---|---|---|
| 1 | Architecture générale du projet | ✅ ce document |
| 2 | Initialisation Django + PostgreSQL | ✅ |
| 3 | Création des modèles et migrations | ✅ |
| 4 | Création des services métier | ✅ |
| 5 | Création des serializers | ✅ |
| 6 | Création des API REST | ✅ |
| 7 | Authentification JWT et permissions | ✅ |
| 8 | Initialisation Next.js | ✅ |
| 9 | Création du design system | ✅ |
| 10 | Création de la page d'accueil | ✅ |
| 11 | Création des destinations | ✅ |
| 12 | Création des circuits | ✅ |
| 13 | Création des hôtels et résidences | ✅ |
| 14 | Création des véhicules | ✅ |
| 15 | Création des activités et événements | ✅ |
| 16 | Création du moteur de recherche | ✅ |
| 17 | Création du système de devis | ✅ |
| 18 | Création des réservations | ✅ |
| 19 | Création du backoffice | ✅ |
| 20 | Notifications | ✅ |
| 21 | SEO | ⏭ prochaine étape |
| 22 | Tests | |
| 23 | Sécurité | |
| 24 | Dockerisation et déploiement | |

Chaque phase comprend : l'objectif, l'arborescence concernée, les fichiers complets, leur emplacement, les commandes à exécuter, la méthode de test et la correction des erreurs. On ne passe pas à la phase suivante avant que la précédente soit validée.
