# Plateforme Web Agence de Voyage — Phase 16

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
#    circuits, hébergements, véhicules, activités, événements, avis — fictifs, interdits en production
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

> Dans le conteneur `backend`, `DJANGO_SETTINGS_MODULE` vaut `config.settings.dev` et
> prime sur `pytest.ini` : forcer les réglages de test, sinon les tests d'emails échouent.
>
> ```bash
> docker compose exec -e DJANGO_SETTINGS_MODULE=config.settings.test backend pytest
> ```

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
  location et une demande préremplie (`/devis?vehicle=…&start=…&end=…` ; la réservation en
  ligne arrive en Phase 18), **calendrier de disponibilité** sur deux mois (jours réservés
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

## Ce qui a été validé (Phase 16)

- Backend : `manage.py check`, aucune migration manquante, 141 tests pytest dont la
  recherche (fautes et accents, tous les mots requis, contenus non publiés exclus, filtres
  par type et destination, paramètres invalides).
- Frontend : TypeScript, ESLint, 32 tests Vitest ; 144 tests Playwright sur ordinateur et
  mobile, stables sur deux passages : audit axe (WCAG 2.2 AA) de 17 pages sans violation
  grave, page de résultats et onglets, faute de frappe, aucun résultat, recherche
  instantanée au clavier, JSON-LD.

## Pages encore manquantes

Ces pages sont liées depuis le menu, le pied de page ou les fiches mais n'existent pas
encore (« Page introuvable ») : `/devis` (Phase 17), connexion et inscription, et des
rubriques **absentes du plan de développement** — services, offres, visas (`/visa/france`),
transport, médiathèque, à propos, contact, blog et pages légales (mentions, confidentialité,
conditions générales).

## Prochaine étape

**Phase 17 : Création du système de devis** — formulaire de demande de devis (prérempli
depuis les fiches : circuit, départ, hôtel, chambre, résidence, véhicule, activité, dates),
suivi et réponse de l'agence, acceptation par le client.
