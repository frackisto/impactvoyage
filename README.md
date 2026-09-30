# Plateforme Web Agence de Voyage — Phase 23

Backend Django + PostgreSQL + Redis + Celery et frontend Next.js, dockerisés.
Voir [architecture-plateforme-voyage.md](architecture-plateforme-voyage.md) pour l'architecture complète.

## Démarrage avec Docker (recommandé)

```bash
# 1. Copier les fichiers d'environnement
cp .env.example .env
cp backend/.env.example backend/.env
# ⚠️ Éditer les deux fichiers .env et définir le même mot de passe
#    pour DATABASE_PASSWORD, ainsi qu'une SECRET_KEY forte.
#    Dans le .env racine, remplacer FRONTEND_SHARED_SECRET par une valeur aléatoire
#    (secret partagé backend / serveur Next.js, voir « Limitation de débit » ci-dessous).

# 2. Construire et démarrer les services
docker compose up --build

# Le backend applique automatiquement les migrations au démarrage
# (voir la commande du service "backend" dans docker-compose.yml).

# 3. Charger le contenu réel de l'agence (coordonnées, services et tarifs,
#    destinations, visas, studio meublé, événements, photos)
docker compose exec backend python manage.py load_agency_content

# 4. (Développement uniquement) Ajouter les données de démonstration :
#    circuits, hébergements, véhicules, activités, événements, avis, comptes de l'équipe
#    (voir « Backoffice ») — fictifs, interdits en production
docker compose exec backend python manage.py seed_demo
# ... et pour les retirer : python manage.py seed_demo --reset
```

> Les tests Playwright s'appuient sur ces deux commandes.

Services démarrés :
- `frontend` → http://localhost:3000 (site Next.js, voir [frontend/README.md](frontend/README.md))
- `backend` → http://localhost:8000
- `db` → PostgreSQL sur le port 5432
- `redis` → Redis sur le port 6379
- `celery` → worker Celery (tâches asynchrones : emails, taux de change)
- `celery-beat` → planificateur (expiration des réservations, taux de change quotidiens,
  purge des notifications lues, durées de conservation des données personnelles)
- `mailpit` → capture des emails en développement : http://localhost:8025

## Vérifier que tout fonctionne

```bash
curl http://localhost:8000/api/v1/health/
# → {"status": "ok", "service": "voyage-api"}

# Documentation Swagger
open http://localhost:8000/api/v1/docs/

# Admin Django (en production : adresse ADMIN_URL_PATH, voir « Sécurité »)
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

> Dans le conteneur `backend`, `DJANGO_SETTINGS_MODULE` vaut `config.settings.dev` et
> prime sur `pytest.ini` : forcer les réglages de test, sinon les tests d'emails échouent.
> L'image ne contient pas les outils de test : les installer d'abord.
>
> ```bash
> docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test backend \
>   sh -c "pip install -q -r requirements-dev.txt && pytest"
> ```

Qualité du backend (mêmes commandes que l'intégration continue) :

```bash
ruff check .                      # lint (configuration : backend/pyproject.toml)
mypy apps config                  # types, vérification légère
pytest --cov --cov-report=term    # tests + couverture (≥ 90 % au global)
coverage report --fail-under=80 \
  --include="apps/*/services.py,apps/core/api.py,apps/accounts/roles.py,apps/accounts/permissions_sync.py"
```

- **Données de test** : fabriques factory_boy dans `apps/core/tests/factories.py`
  (`TourFactory`, `BookingItemFactory`, `UserFactory(role="COMMERCIAL")`…) ; un test ne
  précise que ce qui compte pour lui, les dates sont relatives à aujourd'hui.
- **Frontend** : `npm run lint`, `npm run typecheck` (après `npx next typegen`),
  `npm test` (Vitest : utilitaires et composants — formulaires, filtres, pagination),
  `npm run build` puis `npm run test:e2e` (Playwright, backend démarré avec la
  démonstration).

### Intégration continue

`.github/workflows/ci.yml` s'exécute à chaque push sur `main` et `developpement` et à
chaque pull request :

| Job | Contenu |
|---|---|
| backend | ruff, mypy, migrations à jour, schéma OpenAPI, pytest, seuils de couverture |
| frontend | ESLint, TypeScript, Vitest, build de production |
| e2e | Django (migrations, contenu de l'agence, démonstration) puis Playwright sur le build |

En cas d'échec des tests de bout en bout, les traces Playwright et le journal de Django
sont joints à l'exécution (artefact `playwright`, 7 jours).

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
  d'articles, jetons d'accès des devis et des réservations (hors lien client).
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
- **Parcours client** : consultation et validation d'un devis, suivi et annulation
  d'une réservation avec le jeton reçu par email ; réservations du compte connecté.
- **Équipe** : devis (assignation, proposition, statut), réservations
  (confirmation, refus, annulation), notifications.
- **Paramètres** : pagination `?page=`, `?page_size=` (max 48), recherche `?search=`,
  tri `?ordering=`, filtres propres à chaque liste (documentés dans Swagger),
  langue `Accept-Language` ou `?lang=en`, devise `?currency=EUR` ou `X-Currency`.
- **Erreurs** : toujours `{"error": {"code", "message", "details"}}` — 400
  `validation_error`, 404 `not_found`, 409 `not_available` / `invalid_transition`,
  429 `throttled`…


## Authentification et rôles (Phase 7)

- **JWT** : `/auth/register/`, `/auth/login/` (email + mot de passe), `/auth/refresh/`
  (rotation : l'ancien refresh est révoqué), `/auth/logout/`, `/auth/me/`.
  Le jeton d'accès (15 min) porte le rôle et le nom de l'utilisateur.
- **Emails** : vérification de l'adresse (lien valable 3 jours), mot de passe oublié
  (lien à usage unique, 2 h, sans révéler si le compte existe).
- **Sécurité** : 10 tentatives/min par IP sur ces routes ; changer ou réinitialiser
  son mot de passe déconnecte tous les appareils.
- **Rôles** : la matrice `backend/apps/accounts/roles.py` est la seule source des droits.
  Chaque rôle a un groupe Django, synchronisé après chaque `migrate` ou par
  `python manage.py sync_roles` ; les utilisateurs rejoignent le groupe de leur rôle
  automatiquement.

| Rôle | Droits principaux |
|---|---|
| Super administrateur | Tout |
| Administrateur | Tout le contenu, devis, réservations, avis, utilisateurs ; paramètres du site et paiements en lecture |
| Agent | Destinations, circuits, hôtels, activités, blog, médiathèque, services, visas, transport |
| Commercial | Devis, réservations, messages de contact |
| Gestionnaire | Véhicules, résidences, événements, offres, modération des avis ; réservations en lecture |
| Client | Son compte, ses devis et réservations |

> ⚠️ **Clés secrètes dans `.env`** : entourez-les de guillemets. Sans guillemets,
> django-environ ignore tout ce qui suit un `#`, et une clé générée par Django peut
> se retrouver réduite à quelques caractères. `manage.py check` le signale
> (`core.W001`) et la configuration de production refuse de démarrer avec une clé trop courte.

## Frontend (Phase 8)

Projet Next.js 16 dans [frontend/](frontend/README.md) : FR/EN (`/` et `/en/`), charte aux
couleurs du logo (bleu `#1F8FC4`, orange `#F89832`), types TypeScript générés depuis le
schéma OpenAPI, authentification par cookies httpOnly (le navigateur ne voit jamais les
jetons), pages privées protégées par `proxy.ts`.

## Design system (Phase 9)

Composants réutilisables aux couleurs du logo, en-tête complet (barre de contact, menu
du CdC § 5, « Plus », recherche, sélecteurs de langue et de devise, menu mobile), pied de
page avec les coordonnées de l'agence. Aperçu : http://localhost:3000/charte-graphique

> Les coordonnées (téléphone, email, WhatsApp, adresse, horaires) sont chargées par
> `load_agency_content` ; les liens des réseaux sociaux restent à saisir dans les
> paramètres du site (back-office, Phase 19).

## Page d'accueil (Phase 10)

- **Hero** : photo, slogan et sous-titre modifiables dans les paramètres du site.
- **Moteur de recherche à onglets** (Circuits, Hôtels, Visa, Activités, Transport) : les
  champs portent les noms des filtres de l'API et sont transmis dans l'URL des pages de
  résultats (Phases 11 à 16). Un pays de visa connu ouvre directement sa page
  (`/visa/france`).
- **Sections** : services, destinations mises en avant, prochains départs, offres, visas
  avec les tarifs des formalités et de l'assurance voyage, présentation de l'agence,
  « Pourquoi nous choisir », résidences, événements, avis, bandeau de contact. Une section
  sans contenu publié (ou dont l'API ne répond pas) est masquée.
- **Tarifs des services** (`ServicePrice`) : nouvelle table traduite FR/EN, exposée dans
  `/api/v1/services/` ; elle sera modifiable dans le back-office (Phase 19).
- **Contenu réel de l'agence** (`python manage.py load_agency_content`, idempotent,
  `--force` pour remplacer les photos) : repris de l'ancien site impact-voyage.com.
  Les véhicules, incomplets, restent non publiés ; les textes marqués « À COMPLÉTER » et les
  descriptions de Chine, Abidjan, Grand-Lahou et Mondoukou sont à relire par l'agence.
- **Photos Django** : servies au navigateur par le relais `/media/*` de Next.js (plus besoin
  de `NEXT_PUBLIC_MEDIA_URL`) ; en production, Nginx les servira directement.

## Destinations (Phase 11)

- **Liste** `/destinations` : filtres par continent (en un clic, avec le nombre de
  destinations), pays (limité au continent choisi) et nom ; les filtres sont dans l'URL
  (partageable), la pagination fonctionne par liens. Seules la liste complète et les pages
  par continent sont indexées.
- **Fiche** `/destinations/{slug}` : en-tête immersif, description, attractions, conseils,
  encadré « Préparer votre voyage » (pays, meilleure période, lien vers le visa du pays,
  devis prérempli `/devis?destination=…`, WhatsApp), galerie avec visionneuse au clavier,
  circuits, hôtels, résidences et activités publiés, avis, destinations proches. Sans offre
  publiée, un bandeau « sur mesure » invite à demander un devis.
- **SEO** : titre, description, URL canonique, hreflang FR/EN, Open Graph et JSON-LD
  (`TouristDestination`, `BreadcrumbList`).
- **API** : filtre `?country=CI` sur `/api/v1/destinations/` ; la fiche expose aussi
  `residences` et `rating` (note moyenne des avis validés).
- **Drapeaux** : Chrome et Edge sous Windows n'affichent pas les drapeaux emoji ; une police
  de drapeaux (Twemoji, 77 ko, auto-hébergée) n'est chargée que dans ce cas.

> Une page introuvable renvoie le statut HTTP 200 (avec `noindex`) et non 404 : le
> `loading.tsx` commun à toutes les pages démarre l'envoi avant que la page ne sache que
> le contenu n'existe pas. C'est le comportement documenté de Next.js, sans effet sur
> l'indexation.

## Circuits (Phase 12)

- **Listes** `/circuits/nationaux` et `/circuits/internationaux` : filtres par destination,
  type de circuit, dates de départ, durée, nombre de voyageurs et budget (seules les
  destinations et les types réellement proposés sont listés), tri par prochain départ,
  prix ou durée. Les paramètres sont ceux de l'API : le moteur de recherche de l'accueil
  y mène directement. Filtres repliables sur mobile.
- **Fiche** `/circuits/{slug}` : en-tête immersif (durée, type, sur mesure), description et
  informations clés (départ, groupe, transport, hébergement), programme jour par jour,
  inclus / non inclus, conditions, galerie, activités incluses, avis, circuits proches.
  L'encadré « Réserver ce circuit » liste les départs ouverts avec les places restantes
  (« Plus que 3 places ! ») et les prix spécifiques ; chaque départ ouvre une demande de
  devis préremplie (`/devis?tour=…&departure=…`, formulaire en Phase 17). Sur mobile, une
  barre fixe garde le prix et l'accès aux dates visibles.
- **SEO** : JSON-LD `TouristTrip` (programme, un `Offer` par départ, note) et
  `BreadcrumbList` ; seules les listes sans filtre sont indexées.
- **Données de démonstration** : `seed_demo` (voir « Démarrage ») crée 6 circuits fictifs
  (3 nationaux, 3 internationaux dont un sur mesure), leurs programmes, départs et avis.
- **Traductions** : un test vérifie que chaque message FR/EN est valide (syntaxe ICU) et que
  les deux langues ont les mêmes clés.

## Hôtels et résidences (Phase 13)

- **Hébergements** `/hotels` : hôtels, appartements et hébergements partenaires, filtrés
  par destination, dates, voyageurs, nombre de chambres, type, catégorie, équipements et
  budget par nuit ; tri par prix, catégorie ou nom. Le prix « à partir de » est celui de
  la chambre la moins chère **qui convient** (capacité, nombre de chambres, disponibilité
  aux dates choisies) ; un hôtel sans chambre adaptée disparaît des résultats. Le moteur
  de recherche de l'accueil y mène directement.
- **Fiche hôtel** `/hotels/{slug}` : équipements, chambres et tarifs. Avec des dates, chaque
  chambre indique « Disponible : N chambres libres », « Complet à ces dates » ou
  « Capacité insuffisante », le total indicatif du séjour et une demande de devis
  préremplie (`/devis?hotel=…&room=…&start=…&end=…`). Galerie, avis, hébergements proches,
  JSON-LD `Hotel`.
- **Résidences meublées** `/residences` et `/residences/{slug}` : filtres (dates, voyageurs,
  chambres, équipements, budget), services inclus, conditions, vérification de
  disponibilité avec les périodes déjà réservées et le total du séjour.
- **API** : `/hotels/` accepte `available_from`, `available_to` et `rooms` (paramètres du
  moteur de recherche) ; nouvelles actions `/hotels/{slug}/availability/` (chambres libres
  par type) et `/residences/{slug}/availability/` ; `/amenities/?kind=hotel|residence`
  liste les équipements utilisés, pour les filtres.
- **Démonstration** : `seed_demo` ajoute 5 hébergements (chambres, équipements), une villa
  et des avis.
- **Frontend** : `FilterPanel`, `SortSelect`, `CatalogLayout` et `SegmentedNav` sont communs
  aux circuits et aux hébergements (et serviront aux véhicules et activités). La galerie
  choisit sa disposition pour ne jamais laisser de case vide.

## Location de véhicules (Phase 14)

- **Liste** `/vehicules` : filtres par période de location (seuls les véhicules libres sur
  toute la période sont affichés), catégorie, nombre de places, boîte de vitesses et budget
  par jour ; tri par prix, places ou année. La période est transmise à la fiche.
- **Fiche** `/vehicules/{slug}` : caractéristiques (catégorie, année, places, boîte,
  carburant, climatisation), équipements, vérification de disponibilité avec le total de la
  location, la réservation en ligne et une demande de devis préremplies, **calendrier de disponibilité** sur deux mois (jours réservés
  barrés, annoncés aux lecteurs d'écran), galerie, véhicules proches, JSON-LD `Car` avec
  prix par jour.
- **Résidences** : la fiche affiche aussi le calendrier ; l'encadré de disponibilité est
  commun aux résidences et aux véhicules.
- **Démonstration** : `seed_demo` ajoute 6 véhicules et une réservation confirmée fictive
  (Suzuki Vitara, de J+5 à J+9) pour le calendrier. Les 4 véhicules réels de l'agence
  restent non publiés tant que leurs fiches (année, prix, immatriculation) ne sont pas
  complétées.
- **Tests E2E** : 4 workers au plus (la moitié des cœurs par défaut saturait le serveur de
  test et faisait échouer des tests au hasard) ; un test de défilement horizontal par page.

## Activités et événements (Phase 15)

- **Activités** `/activites` : filtres par destination, date, nombre de participants, type,
  durée et budget. Avec une date, seules les activités qui ont encore assez de places ce
  jour-là sont proposées, avec les places restantes sur chaque carte. Le moteur de
  recherche de l'accueil (onglet Activités) y mène directement.
- **Fiche activité** : informations clés, vérification des places à une date pour N
  participants (« Plus que 2 places le mardi 6 octobre », total indicatif, demande
  préremplie `/devis?activity=…&date=…&participants=…`), galerie, activités proches. Les
  activités incluses dans un circuit s'affichent sur la fiche du circuit.
- **Événementiel** `/evenements` : réalisations de l'agence filtrables par type et par
  année ; fiche avec période, lieu, participants, partenaires, photos (visionneuse),
  vidéos (lien vers YouTube/Vimeo) et invitation à organiser son événement. JSON-LD `Event`.
- **API** : filtre `date` (+ `participants`) et `places_left` sur `/activities/`, action
  `/activities/{slug}/availability/?date=` ; partenaires d'événement typés.
- **Démonstration** : 6 activités (dont 3 incluses dans le circuit Dubaï), une inscription
  fictive (18 places sur 20 à J+10) et 2 événements passés.

> La **médiathèque** (albums, CdC § 16) n'a pas encore de page : les photos et vidéos des
> événements s'affichent sur leur fiche.

### Limitation de débit (correction importante)

Toutes les pages sont rendues par le serveur Next.js : Django voyait donc **une seule
adresse IP pour tous les visiteurs**, et les limites (120 lectures/min, 10 connexions/min)
s'appliquaient au site entier — sous trafic modéré, les pages se seraient affichées vides
et les connexions bloquées pour tout le monde. De plus, l'en-tête `X-Forwarded-For` était
pris tel quel et permettait de contourner les limites.

- Le serveur Next.js s'identifie avec `FRONTEND_SHARED_SECRET` (même valeur des deux côtés,
  fichier `.env` racine avec Docker, `frontend/.env.local` hors Docker ; obligatoire en
  production). Il transmet l'adresse réelle du visiteur (`X-Client-IP`) pour les requêtes
  qui lui sont propres : connexion, formulaires, disponibilités.
- Les lectures publiques mises en cache par Next.js ne sont pas limitées par Django (le
  trafic des pages sera limité par Nginx, Phase 24) ; les écritures le sont toujours.
- `X-Forwarded-For` n'est plus pris en compte par défaut (`NUM_PROXIES=0` ; 1 derrière
  Nginx, qui devra poser `X-Real-IP`).

## Moteur de recherche (Phase 16)

- **API** `/api/v1/search/?q=&type=&destination=&limit=` : destinations, circuits, hôtels,
  résidences, véhicules, activités et événements publiés, fusionnés et triés par
  pertinence, avec le nombre de résultats par type. PostgreSQL `pg_trgm` + `unaccent`,
  sans table dédiée : fautes de frappe (« dubay ») et accents tolérés ; chaque mot doit
  correspondre (titre, accroche, destination, thème… en français et en anglais), les mots
  vides sont ignorés, le titre compte davantage dans le score.
- **Recherche instantanée** : la loupe de l'en-tête ouvre une fenêtre qui affiche les
  6 meilleurs résultats pendant la frappe (requêtes espacées de 250 ms, via le relais
  Next.js) ; Entrée ou « Voir les N résultats » ouvre la page complète.
- **Page** `/recherche?q=…&type=…` : onglets par type avec compteurs, vignette, contexte
  (destination ou pays), accroche et prix ; invitation sans requête, suggestions et devis
  sans résultat. Jamais indexée.
- **SEO** : JSON-LD `WebSite` + `SearchAction` sur l'accueil (zone de recherche dans Google).

## Système de devis (Phase 17)

- **Demande** `/devis` : projet (destination du catalogue ou saisie libre, dates, adultes,
  enfants, type de voyage, prestations souhaitées, hébergement, transport, budget,
  précisions) puis coordonnées (téléphone, WhatsApp, pays de résidence) et consentement.
  Contrôles immédiats dans le navigateur, puis erreurs de Django affichées sous les champs
  concernés ; message dédié si la limite de 5 demandes par heure est atteinte. Champ piège
  à robots (*honeypot*) ; Turnstile viendra en Phase 23.
- **Préremplissage** depuis les fiches : circuit et départ (`?tour=…&departure=…`), hôtel
  et chambre (`?hotel=…&room=…&start=…&end=…&travelers=…&rooms=…`), résidence, véhicule et
  période, activité (`?activity=…&date=…&participants=…`), destination, ou prestation
  (`?service=VISA`). Un encadré rappelle l'objet d'origine (photo, dates, voyageurs). Un
  paramètre inconnu ou un contenu introuvable est ignoré ; seule la page sans paramètre
  est indexée.
- **Suivi client sans compte** `/devis/{reference}?token=…` : lien envoyé dans l'email de
  confirmation, puis avec la proposition. Étapes (reçue, en cours, proposition envoyée,
  acceptée ou déclinée), proposition de l'agence (montant, message, validité),
  récapitulatif. Le client **accepte** (réservation `PENDING` créée, bloquée 48 h) ou
  **décline** avec un motif facultatif, après confirmation. Proposition expirée ou lien
  invalide : message dédié. Jamais indexée.
- **Réponse de l'agence** : par l'API en attendant le backoffice (Phase 19) —
  `POST /quotes/{reference}/assign/`, `send-proposal/` (email avec le lien de suivi) et
  `status/`, réservés à l'équipe (voir Swagger).
- **Démonstration** : `seed_demo` ajoute deux devis à lien fixe, rétablis à chaque
  chargement :
  - `/devis/DV-DEMO-000001?token=7e57d3a0-0000-4000-8000-000000000001` (proposition envoyée) ;
  - `/devis/DV-DEMO-000002?token=7e57d3a0-0000-4000-8000-000000000002` (en cours d'étude).
- **Correctif** : relancer `seed_demo` un autre jour ajoutait de nouveaux départs de
  circuit (dates relatives) au lieu de remplacer les précédents ; les anciens départs sans
  réservation sont désormais supprimés.

## Ce qui a été validé (Phase 17)

- Backend : `manage.py check`, aucune migration manquante, 142 tests pytest dont le
  parcours complet du devis (création, lien de suivi dans l'email, proposition, acceptation,
  jeton invalide, double réponse refusée) et la démonstration rechargée un autre jour.
- Frontend : TypeScript, ESLint, 32 tests Vitest ; 166 tests Playwright sur ordinateur et
  mobile, stables sur deux passages : audit axe (WCAG 2.2 AA) de 20 pages sans violation
  grave, préremplissage (circuit, hôtel et dates), erreurs du navigateur et de Django,
  envoi, suivi en français et en anglais, acceptation, lien invalide.
- Parcours réel via le relais Next.js sur l'application Docker : création, erreurs de
  validation, piège à robots, acceptation (réservation `PENDING`), seconde acceptation
  refusée.

## Rubriques hors plan de développement

Pages liées depuis le menu, le pied de page, le moteur de recherche ou les fiches, mais
absentes des phases du plan. Toutes s'appuient sur les API existantes.

- **Services** `/services` : les prestations de l'agence (ordre de l'administration),
  tarifs éventuels, lien vers le devis prérempli (`quote_service_type`) et vers la rubrique
  du catalogue ; sommaire par ancres (`/services#visa-et-formalites`).
- **Offres** `/offres` (filtre par type) et `/offres/{slug}` : prix barré, réduction,
  validité, places (« Dernières places » dès 5 places), conditions, lien vers la fiche
  visée, JSON-LD `Offer`. « Profiter de l'offre » ouvre `/devis?offer=…` : l'offre est
  enregistrée dans la demande (`source_offer`) et la prestation correspondante cochée.
  La carte d'offre est partagée avec l'accueil.
- **Visas** `/visa` (filtres pays et motif, cible de l'onglet Visa de l'accueil) et
  `/visa/{pays}` : formules, validité, délai, frais, pièces à fournir, avertissement sur la
  décision consulaire.
- **Transport** `/transport` : transferts, navettes, véhicules avec chauffeur, filtrés par
  type, départ, arrivée (texte libre) et passagers — cible de l'onglet Transport de
  l'accueil, dont la date et le nombre de voyageurs passent dans le devis. `FilterPanel`
  accepte désormais des champs texte.
- **Médiathèque** `/mediatheque` (catégories) et `/mediatheque/{slug}` : galerie avec
  visionneuse, liens vidéo, JSON-LD `ImageGallery`.
- **Blog** `/blog` (catégories, mots-clés) et `/blog/{slug}` : article, temps de lecture,
  mots-clés, articles liés, JSON-LD `BlogPosting`. Le contenu est du **texte structuré**
  (paragraphes séparés par une ligne vide, `## ` intertitre, `- ` liste), affiché sans
  interpréter de HTML ; un éditeur riche (HTML nettoyé par `nh3`) pourra venir avec le
  backoffice.
- **À propos** `/a-propos` : texte « À propos » de l'administration, équipe, engagements,
  services, coordonnées ; **Contact** `/contact` : formulaire (`POST /contact/`, objet au
  choix, piège à robots, limite de débit), coordonnées, horaires, lien carte, JSON-LD
  `TravelAgency`.
- **Pages légales** `/mentions-legales`, `/confidentialite`, `/conditions-generales` :
  sommaire, sections traduites (espace `Legal`), coordonnées reprises des paramètres du
  site. **À faire valider par un juriste** ; les informations inconnues sont marquées
  `[à compléter]` (RCCM, capital, compte contribuable, directeur de la publication,
  hébergeur, durée de conservation des demandes sans suite).
- **Pied de page** : liens ajoutés vers Visas, Transport et Blog.
- **Démonstration** : `seed_demo` ajoute 3 offres en cours (dont une sur le week-end à
  Mondoukou), 4 services de transport, 3 albums photo et 3 articles de blog.

Validé : 142 tests pytest ; TypeScript, ESLint, 34 tests Vitest ; 248 tests Playwright
sur ordinateur et mobile, stables sur deux passages, dont l'audit axe (WCAG 2.2 AA) de
35 pages.

## Réservations en ligne (Phase 18)

- **Depuis les fiches** : « Réserver » sur chaque départ de circuit, sur une chambre
  d'hôtel libre aux dates choisies, et dans le résultat de disponibilité d'une résidence,
  d'un véhicule ou d'une activité. « Réserver en ligne » devient l'action principale de
  l'encadré latéral ; la demande de devis reste proposée à côté (sur mesure, groupes).
- **Demande** `/reservation?…` (mêmes paramètres que `/devis` : `tour` + `departure`,
  `hotel` + `room`, `residence`, `vehicle`, `activity`, `start`/`end`/`date`,
  `travelers`/`rooms`/`participants`) : rappel de la prestation (photo, dates, nuits ou
  jours, places restantes), nombre de voyageurs, de chambres ou de participants borné
  par la disponibilité, lieux de prise en charge et de restitution pour un véhicule,
  coordonnées, consentement, total estimé mis à jour pendant la saisie. Aucun prix
  n'est envoyé : Django recalcule tout. Dates absentes, période déjà prise ou lien sans
  prestation : message dédié avec retour à la fiche ou devis. Jamais indexée.
- **Erreurs** : contrôles dans le navigateur, puis erreurs de Django sous les champs ;
  prestation prise entre-temps (`not_available`), offre modifiée, limite de 10 demandes
  par heure : message clair et retour à la fiche. Piège à robots.
- **Suivi sans compte** `/reservation/{reference}?token=…` : ouvert juste après l'envoi
  (« Demande envoyée ! ») et par le lien de chaque email. Étapes (demande reçue,
  confirmée, voyage effectué, ou annulée / refusée / expirée), explication du statut,
  prestations avec lien vers leur fiche, total, récapitulatif. **Annulation** par le
  client, avec motif facultatif, tant que l'agence n'a pas confirmé. Lien invalide :
  message dédié. Jamais indexée.
- **Backend** : jeton `access_token` (UUID) et date de consentement sur `Booking`
  (migration qui attribue un jeton distinct aux réservations existantes) ;
  `GET /bookings/{reference}/?token=` et `POST /bookings/{reference}/cancel/` avec
  `{"token"}` ouverts sans compte ; la création renvoie le jeton ; consentement
  obligatoire ; `target_slug` et `can_cancel` dans la réponse. L'annulation par le
  client est contrôlée **sous verrou** : une confirmation simultanée de l'agence
  l'emporte (409 `contact_agency`). Le lien de suivi figure dans tous les emails au
  client, y compris celui de l'acceptation d'un devis ; la page de suivi du devis
  renvoie vers la réservation créée.
- **Réponse de l'agence** : par l'API en attendant le backoffice (Phase 19) —
  `POST /bookings/{reference}/confirm/`, `reject/` et `cancel/`, réservés à l'équipe.
- **Démonstration** : `seed_demo` ajoute une demande à lien fixe, rétablie à chaque
  chargement : `/reservation/IV-DEMO-000001?token=7e57d3a0-0000-4000-8000-000000000101`.

## Ce qui a été validé (Phase 18)

- Backend : `manage.py check`, schéma OpenAPI validé sans avertissement, aucune migration
  manquante, 147 tests pytest dont le suivi et l'annulation par jeton (jeton faux, mal
  formé ou d'une autre réservation refusé de la même façon), l'annulation refusée après
  confirmation, le consentement obligatoire, le lien de suivi dans les emails (demande,
  annulation, devis accepté) et la demande de démonstration.
- Frontend : TypeScript, ESLint, 34 tests Vitest ; 274 tests Playwright sur ordinateur et
  mobile, stables sur deux passages consécutifs : parcours véhicule de la fiche au suivi
  (contenu exact de la requête, sans prix), départ de circuit (voyageurs bornés, départ
  complet entre-temps), chambre d'hôtel, dates manquantes et période déjà réservée, suivi
  en français et en anglais, annulation (refusée puis confirmée), lien invalide ; audit
  axe (WCAG 2.2 AA) de 38 pages dont les 3 nouvelles.
- Test rendu plus robuste : la recherche d'hôtels depuis l'accueil visait « le » panneau
  d'onglet alors que l'ancien panneau est encore présent pendant le changement d'onglet
  (échec intermittent) ; il vise désormais le panneau « Hôtels ».

## Backoffice (Phase 19)

Administration Django thémée avec **django-unfold** : http://localhost:8000/admin/
(connexion par email). Couleurs du site, menu en français, utilisable sur mobile.
Le backoffice est servi par Django, pas par le site ; en production, il est à une adresse
non standard (`ADMIN_URL_PATH`) et exige une double authentification (voir « Sécurité »).

- **Comptes de démonstration** (créés par `seed_demo`, jamais en production), mot de
  passe `Demo-Impact-2026` : `superadmin.demo@`, `admin.demo@`, `agent.demo@`,
  `commercial.demo@` et `gestionnaire.demo@example.com`. Chacun ne voit que ce que son
  rôle permet (menu, indicateurs, actions).
- **Tableau de bord** : indicateurs (devis et réservations à traiter, messages non lus,
  avis en attente, offres en cours, contenus publiés), listes « à traiter », notifications
  non lues, devis et réservations par mois sur 12 mois, destinations et circuits
  populaires (réservations puis vues). Statistiques en cache 5 minutes.
  Visiteurs : lus dans **Umami** (`UMAMI_API_URL`, `UMAMI_WEBSITE_ID`,
  `UMAMI_API_TOKEN`) ; tant qu'Umami n'est pas déployé (Phase 24), la carte l'indique.
- **Réservations** : fiche en lecture seule (sauf notes internes) ; **Confirmer**
  (réserve le stock), **Refuser** et **Annuler** (motif, stock libéré) passent par
  `bookings.services`, avec une page de confirmation et l'email au client. Seules les
  décisions permises par le statut sont proposées. Une réservation qui bloque du stock
  ne peut pas être supprimée ; la suppression est logique.
- **Devis** : assigner un commercial (le devis passe « En cours »), **Envoyer la
  proposition** (montant, validité, message : email avec le lien client), refuser,
  clôturer ; actions groupées « M'assigner », « Refuser », « Clôturer ».
- **Messages** marqués lus à l'ouverture, puis traités ou archivés ; **avis** approuvés,
  mis en avant sur l'accueil ou refusés (un par un ou en groupe).
- **Catalogue et contenus** : un champ par langue (`[fr]`, `[en]`), galeries photo,
  départs et programme jour par jour des circuits, chambres des hôtels, tarifs des
  services, publication groupée. Les places réservées d'un départ sont en lecture seule.
- **Administration** : utilisateurs (le rôle décide des droits ; seul un super
  administrateur peut attribuer ce rôle ou modifier un tel compte ; les groupes Django
  ne sont plus éditables), paramètres du site (une seule fiche), taux de change
  (mise à jour à la demande, cache vidé), paiements en lecture.
- **Mes notifications** : chacun voit les siennes ; « Ouvrir » les marque lues et mène
  à la fiche.
- Un enregistrement depuis l'admin ne réécrit que les champs modifiés : un statut
  changé entre-temps par le client (annulation, acceptation) n'est jamais écrasé.
- Le site reprend les modifications du catalogue en 5 minutes au plus (1 h pour les
  paramètres du site), le temps de son cache.

## Ce qui a été validé (Phase 19)

- Backend : `manage.py check`, schéma OpenAPI validé sans avertissement, aucune migration
  manquante, 203 tests pytest (56 nouveaux) : chaque écran de l'admin s'affiche avec la
  démonstration, confirmation / refus / annulation (stock, emails, statut concurrent,
  décisions proposées selon le statut et le rôle), proposition de devis, messages, avis,
  garde-fou des rôles, notifications (liens externes refusés), paramètres, taux de
  change, tableau de bord (statistiques, cache, filtrage par rôle, menu, Umami).
- Rendu vérifié dans Chromium (ordinateur et mobile), sans erreur JavaScript.
- **Corrections** : les groupes de rôles n'étaient plus synchronisés après `migrate` dès
  qu'une app sans modèles (ici `dashboard`) arrivait en dernier ; une connexion ouverte
  directement sur `/admin/login/` menait à une page 404.
- Limite connue : unfold ne fournit pas de traduction française ; quelques libellés
  de l'interface restent en anglais (« Type to search », « Choose file to upload »).

## Notifications (Phase 20)

- **Emails HTML + texte** : chaque email est décrit par un objet `Email` (titre,
  paragraphes, récapitulatif, bouton) construit par l'app métier
  (`bookings/emails.py`, `inquiries/emails.py`, `accounts/emails.py`), puis mis en page
  par `templates/emails/message.{html,txt}` : emblème et coordonnées de l'agence (tirées
  des paramètres du site), bouton accessible avec son lien en clair, compatible mobile.
- **Langue du client** : les emails partent dans la langue du site au moment de la
  demande (`language` de la réservation, du devis, du message ; langue préférée du
  compte), avec des liens `/en/…`, des dates et des montants au format de la langue.
  Le site transmet désormais la langue **de la page** (et non celle du navigateur).
- **Client** : demande de devis reçue, proposition (montant, validité, lien de
  validation), proposition acceptée ; réservation reçue, confirmée, refusée (motif,
  lien vers le devis), annulée (par le client ou par l'agence), **expirée** (nouveau) ;
  **accusé de réception du formulaire de contact** (nouveau) ; vérification de
  l'adresse et mot de passe oublié. Répondre écrit à l'adresse publique de l'agence.
- **Agence** : email HTML à `AGENCY_NOTIFICATION_EMAIL` avec récapitulatif complet et
  bouton vers la fiche de l'admin ; « Répondre » écrit directement au client. Nouveaux
  événements : **devis refusé par le client** (avec le motif) et **réservation
  expirée**. Les notifications du tableau de bord suivent les mêmes événements.
- **Canaux** : `STAFF_NOTIFICATION_CHANNELS` liste les canaux actifs (tableau de bord et
  email par défaut). `WhatsAppChannel` et `SmsChannel` sont prêts : ils écrivent aux
  membres de l'équipe concernés qui ont renseigné leur numéro, via le prestataire de
  `SHORT_MESSAGE_BACKEND` (par défaut, simple journalisation ; un prestataire réel —
  WhatsApp Cloud API, Twilio, Orange SMS — n'est qu'une classe `send(channel, to, text)`).
- **Purge** : les notifications lues depuis plus de 90 jours sont supprimées chaque nuit.
- **Développement** : **Mailpit** capture tous les emails (http://localhost:8025) tant
  que `EMAIL_HOST` est vide. Aperçu de tous les emails, en français et en anglais,
  sans rien envoyer :

  ```bash
  docker compose exec backend python manage.py preview_emails --out /tmp/emails
  docker compose cp backend:/tmp/emails ./email-previews
  ```

## Ce qui a été validé (Phase 20)

- Backend : `manage.py check`, aucune migration manquante, 218 tests pytest (15 nouveaux) :
  rendu HTML et texte, échappement du contenu saisi par le client, langue (textes,
  liens, dates, montants), pied de page de l'agence, envoi multipart après validation de
  la transaction (rien en cas d'échec), Reply-To, destinataires par rôle, canaux
  WhatsApp / SMS, purge, expiration, refus de devis, accusé de réception, commande
  d'aperçu.
- Parcours réel : un message de contact envoyé en anglais produit l'accusé de réception
  en anglais et l'alerte à l'agence, reçus dans Mailpit.
- Frontend : TypeScript, ESLint, 42 tests Playwright (contact en français et en anglais :
  la langue de la page est transmise, redirection /admin, réservations).
- Rendu des emails vérifié dans Chromium (ordinateur et mobile).

## Pages encore manquantes

Connexion et inscription (liées depuis l'en-tête), prévues avec les comptes clients.
L'espace client (« mes réservations ») viendra avec elles ; l'API le permet déjà. Les
liens des emails de compte (`/verifier-email`, `/reset-password`) mèneront à ces pages.

## SEO (Phase 21)

- **Métadonnées de toutes les pages publiques** par `pageMetadata()` (`frontend/lib/seo.ts`) :
  titre, description, URL canonique, variantes hreflang (fr, en, x-default), Open Graph
  complet (nom du site, langue, URL, photo de la fiche ou image de partage par défaut
  1200 × 630 `public/brand/og-default.jpg`) et Twitter Card. L'accueil a désormais ses
  propres métadonnées. Les listes filtrées ou paginées restent `noindex, follow` ; les
  pages personnelles (suivi de devis ou de réservation) et la recherche ne sont jamais
  indexées.
- **`/sitemap.xml`** : pages fixes, pages par continent et tous les contenus publiés
  (destinations, circuits, hôtels, résidences, véhicules, activités, événements, offres en
  cours, articles, albums, pays des visas), dans les deux langues, chacun avec ses
  variantes et sa date de modification. Contenus fournis par `GET /api/v1/seo/sitemap/`.
- **`/robots.txt`** : tout est exploré sauf l'API, l'admin, la recherche et les pages
  personnelles ; il annonce le plan du site. En recette, `SEO_NOINDEX=true` (frontend)
  interdit toute exploration et ajoute `noindex` à toutes les pages.
- **Régénération à la demande** : quand un contenu public change (admin, services,
  actions groupées), Django appelle après validation de la transaction la route
  `POST /api/revalidate` du site (secret `FRONTEND_SHARED_SECRET`), qui invalide les
  étiquettes de cache concernées. La page modifiée est à jour dès la visite suivante,
  sans attendre les 5 minutes du cache. Réglage `FRONTEND_REVALIDATE_URL` (fourni par
  docker-compose) ; vide, le site se met à jour à l'expiration de son cache.
- Données structurées (déjà en place) : TravelAgency, WebSite + SearchAction,
  TouristTrip, TouristDestination, Hotel, Event, Article, BreadcrumbList, AggregateRating.
- À savoir : Next.js envoie les métadonnées dans le `<head>` aux robots qui n'exécutent
  pas le JavaScript (WhatsApp, Facebook, Bing, LinkedIn…). Aux navigateurs et à
  Googlebot, il les diffuse en streaming : elles peuvent arriver après le `<head>`, ce
  que Google lit correctement.

## Ce qui a été validé (Phase 21)

- Backend : `manage.py check`, schéma OpenAPI validé, aucune migration manquante,
  226 tests pytest (8 nouveaux) : contenus du plan du site (brouillons, offres expirées
  et doublons de pays exclus), régénération (étiquettes par modèle, un appel par
  transaction, relations plusieurs-à-plusieurs, suppression, transaction annulée,
  désactivation, secret, nouvelle tentative), publication groupée depuis l'admin.
- Frontend : TypeScript, ESLint, 37 tests Vitest (dont `pageMetadata`), 291 tests
  Playwright sur ordinateur et mobile : sitemap (pages, langues, hreflang, pages
  privées absentes), robots.txt, aperçu WhatsApp d'une fiche et de l'accueil (balises
  dans le `<head>`), liste filtrée non indexée, route de régénération (secret,
  étiquettes inconnues refusées).
- Parcours réel dans Docker : un titre de circuit modifié dans Django apparaît sur le
  site en quelques secondes (tâche Celery → `/api/revalidate` → page recalculée).
- Corrigé au passage : les types TypeScript de l'API n'avaient pas été régénérés après
  les nouveaux événements de notification (Phase 20) ; Vitest ne pouvait pas charger un
  module qui importe la navigation de next-intl.

## Tests et qualité (Phase 22)

- **factory_boy** remplace les constructeurs faits main : 17 fabriques communes
  (`apps/core/tests/factories.py`), 177 appels migrés dans 30 fichiers de tests. Les
  dates par défaut sont relatives à aujourd'hui (un départ au 10/01/2027 figé aurait fait
  échouer les tests de réservation dès 2027).
- **Couverture mesurée** (pytest-cov, configuration dans `backend/pyproject.toml`) :
  97 % au global, 98 % sur les services et les permissions (objectif : 80 %).
- **Nouveaux tests** : règles de tarification des réservations (chaque demande
  impossible refusée avec son code), admin des offres (messages de validation,
  activation groupée), blog (publication immédiate ou programmée, temps de lecture,
  actions groupées) ; côté frontend, composants pagination, panneau de filtres et
  formulaire de contact (contrôles, erreurs de Django, limite de débit).
- **Lint et types** : ruff (erreurs, imports, bugs probables, modernisation, Django) et
  mypy « léger » sans erreur ; quelques annotations ajoutées aux classes de base.
- **Intégration continue** : voir « Lancer les tests ».

## Ce qui a été validé (Phase 22)

- Backend : ruff et mypy sans erreur, 238 tests pytest, couverture 97 % (98 % sur les
  services et les permissions), migrations à jour, schéma OpenAPI valide.
- Frontend : ESLint, TypeScript, 48 tests Vitest, build de production.
- Corrigé au passage : les actions groupées du blog réimplémentaient la publication au
  lieu d'utiliser `blog.services` (jamais appelé) ; Testing Library ne nettoyait pas le
  DOM entre deux tests (rendus accumulés).
- Limites connues : les parcours inscription et connexion (§ 14) seront testés avec les
  pages de compte, qui n'existent pas encore. Le compteur de vues des fiches
  (`view_count`) n'est jamais incrémenté : la colonne « Vues » du tableau de bord reste
  à 0 (prévu par l'architecture § 7.2, à faire avec les performances).

## Sécurité (Phase 23)

Revue OWASP (architecture § 11). À renseigner avant la mise en production :

| Variable | Où | Rôle |
|---|---|---|
| `ADMIN_URL_PATH` | `backend/.env` | Adresse du backoffice, non standard (obligatoire en production) |
| `TURNSTILE_SECRET_KEY` | `backend/.env` | Clé secrète Cloudflare Turnstile |
| `NEXT_PUBLIC_TURNSTILE_SITE_KEY` | `.env` racine (build du frontend) | Clé du site Turnstile |
| `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` | `backend/.env` | Domaines du backend (obligatoires en production) |

- **Backoffice** : en production, `/admin/` répond 404 ; seule l'adresse `ADMIN_URL_PATH`
  mène à l'admin, et le site ne la révèle pas (plus de redirection de `/admin`).
  **Double authentification** obligatoire pour l'équipe : au premier accès, chacun scanne
  un QR code avec une application (Google Authenticator, Microsoft Authenticator,
  FreeOTP…) et reçoit 10 codes de secours, affichés une seule fois ; ensuite, un code est
  demandé à chaque connexion. Téléphone perdu : un super administrateur clique
  « Réinitialiser la double authentification » sur la fiche du compte. La colonne
  « Double authentification » de la liste des utilisateurs montre qui l'a activée.
  En développement, elle est facultative : `STAFF_OTP_REQUIRED=True` dans `backend/.env`
  pour l'essayer.
- **Connexion** : 5 échecs pour une adresse IP ou un compte bloquent l'admin 15 minutes.
  À l'API, un compte de l'équipe doit aussi fournir son code (`otp_code` ; erreurs
  `otp_required`, `otp_invalid`, `otp_setup_required`).
- **Anti-spam** : widget Cloudflare Turnstile sur les formulaires de devis, de contact et
  de réservation (le jeton est aussi exigé par l'API pour les avis et l'inscription),
  vérifié par Django une fois les données valides. Sans clés, rien ne change
  (développement, tests). Clés de test Cloudflare : site `1x00000000000000000000AA`,
  secret `1x0000000000000000000000000000000AA` (toujours valides).
- **En-têtes** : CSP stricte à nonce sur toutes les pages du site (aucun script en ligne
  non signé, seul Turnstile est autorisé en dehors du site), CSP fermée sur les routes
  `/api` et les réponses de Django, CSP du backoffice limitée à son domaine, HSTS dès que
  `NEXT_PUBLIC_SITE_URL` est en HTTPS.
- **Relais `/api/backend/*`** : un chemin encodé (`%2F..%2F`) permettait d'atteindre
  n'importe quelle adresse de Django, backoffice compris, depuis le site : seuls des
  chemins simples sous `/api/v1` sont désormais relayés. Les envois venant d'un autre
  site sont refusés (`forbidden_origin`).
- **Images** : le format réel (JPEG, PNG, WebP) doit correspondre à l'extension, 40
  mégapixels au plus ; les photos des visiteurs (avis, avatar) perdent leurs métadonnées
  (position GPS, appareil).
- **Contenu riche** : aucun champ n'accepte de HTML ; articles et pages légales sont
  affichés comme du texte, sans interpréter de balise (pas besoin de nettoyeur HTML).
- **Données personnelles** : liste des utilisateurs → **Données personnelles**
  (administrateurs) : rechercher une adresse email, télécharger l'export JSON (droit
  d'accès), effacer (droit à l'effacement). Les réservations confirmées ou réalisées
  (pièces comptables), les demandes en cours et les comptes de l'équipe sont conservés,
  avec le motif affiché. Durées de conservation appliquées chaque nuit (reprises dans la
  politique de confidentialité) ; `python manage.py apply_retention` les applique tout
  de suite.
- **Documentation de l'API** : réservée en production à l'équipe connectée au
  backoffice ; l'API ne répond qu'en JSON (pas d'interface navigable).
- `manage.py check --deploy` ne signale plus rien avec les réglages de production ; la CI
  le vérifie à chaque push.

## Ce qui a été validé (Phase 23)

- Backend : ruff et mypy sans erreur, migrations à jour (validateur d'image ajouté aux
  champs photo : aucune modification de la base), schéma OpenAPI valide, `check --deploy`
  sans avertissement avec les réglages de production, 275 tests pytest (37 nouveaux :
  double authentification, blocage des connexions, CSP, documentation réservée,
  Turnstile, images, lien de réponse, données personnelles, durées de conservation),
  couverture 97 %.
- Frontend : ESLint, TypeScript, 58 tests Vitest (règles du relais, contrôle d'origine,
  CSP, widget Turnstile dans un formulaire), build de production, 307 tests Playwright
  sur ordinateur et mobile (dont : CSP à nonce sans aucune violation sur cinq pages et
  après une navigation, chemins encodés refusés par le relais, envois d'un autre site
  refusés, `/admin` sans redirection).
- Parcours réels : backoffice à une adresse non standard avec 2FA dans Chromium
  (`/admin/` → 404, enregistrement de l'application par QR code, codes de secours, accès,
  nouvelle connexion avec un code de secours, pages de l'admin sans violation de CSP) ;
  widget Turnstile avec la clé de test de Cloudflare (script et cadre autorisés par la
  CSP, jeton transmis, message enregistré) ; vérification côté Django auprès de
  Cloudflare avec les clés de test « toujours valide » et « toujours refusée ».
- Corrigé au passage : le relais `/api/backend/*` donnait accès à tout Django depuis le
  site (chemin encodé) ; le lien « Répondre par email » d'un message de contact
  permettait d'ajouter un destinataire caché via l'objet saisi par le visiteur ; les
  liens des notifications visaient `/admin/` en dur ; l'API navigable de DRF restait
  active en production ; zod 4 testait `eval` (bloqué par la CSP).
- Limites connues : comme toute page inconnue, `/admin` sur le site répond avec le statut
  200 (page introuvable servie en streaming, `noindex`) — à corriger avec les
  performances ; les mentions légales contiennent encore des champs « à compléter »
  (RCCM, hébergeur…) que seule l'agence peut fournir ; les tests d'activités supposent
  une démonstration chargée récemment (dates relatives au jour du chargement :
  `seed_demo --reset` puis `seed_demo`).

## Prochaine étape

**Phase 24 : Dockerisation et déploiement** — `docker-compose.prod.yml`, Nginx (TLS,
HSTS, limitation des pages, `client_max_body_size`, en-têtes des médias), Umami, images
sans utilisateur root, sauvegardes.
