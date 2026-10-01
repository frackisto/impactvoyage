# Guide de déploiement — Impact Voyage

Mise en production avec `docker-compose.prod.yml` (Phase 24, architecture § 15).
Pour le développement local, voir le [README](README.md).

## 1. Vue d'ensemble

```
Internet ──▶ Nginx (80, 443) ─┬─▶ https://SITE_DOMAIN   Next.js  (pages, relais /api)
                              │      /media/*  ──────▶ volume des médias (lecture seule)
                              │      /stats/*  ──────▶ Umami (script, collecte)
                              ├─▶ https://API_DOMAIN    Django + Gunicorn (backoffice, API)
                              │      /static/*, /media/*  servis par Nginx
                              └─▶ https://STATS_DOMAIN  Umami (statistiques)

Réseau interne : PostgreSQL (bases voyage_db et umami), Redis, worker et planificateur
Celery, certbot (certificat Let's Encrypt), backup (sauvegardes quotidiennes).
```

| Service | Rôle |
|---|---|
| `nginx` | TLS, HSTS, redirection HTTP → HTTPS, limitation de débit, médias et fichiers statiques, pages de maintenance |
| `frontend` | Site Next.js (image autonome, utilisateur `nextjs`) |
| `backend` | Django + Gunicorn (utilisateur `app`) ; migrations et `collectstatic` à chaque démarrage |
| `celery`, `celery-beat` | Emails, régénération des pages, tâches planifiées |
| `db`, `redis` | PostgreSQL 16, Redis 7 (jamais exposés) |
| `umami` | Mesure d'audience sans cookie |
| `certbot` | Obtient puis renouvelle le certificat ; Nginx le recharge seul |
| `backup` | Sauvegarde chaque nuit, test de restauration le 1er du mois |

Seuls les ports **80** et **443** sont ouverts sur le serveur.

## 2. Prérequis

- Un serveur Linux (Ubuntu 24.04 LTS ou Debian 12) : 2 vCPU, 4 Go de mémoire, 40 Go de
  disque au minimum (les sauvegardes des médias en demandent davantage).
- Docker Engine 24 ou plus récent avec l'extension Compose (`docker compose version`).
- Trois noms de domaine (enregistrements DNS A, et AAAA si le serveur a une adresse IPv6)
  pointant vers le serveur, par exemple :

  | Variable | Exemple | Usage |
  |---|---|---|
  | `SITE_DOMAIN` | `www.impactvoyage.ci` | site public |
  | `SITE_ALIASES` | `impactvoyage.ci` | redirigé vers le site (facultatif) |
  | `API_DOMAIN` | `gestion.impactvoyage.ci` | backoffice et API |
  | `STATS_DOMAIN` | `stats.impactvoyage.ci` | statistiques Umami |

- Pare-feu : ports 22 (SSH), 80 et 443 ouverts, rien d'autre.

  ```bash
  sudo ufw allow OpenSSH && sudo ufw allow 80,443/tcp && sudo ufw enable
  ```

- Un compte chez un prestataire d'envoi d'emails (SMTP) et, conseillé, un widget
  Cloudflare Turnstile (anti-robot des formulaires).

## 3. Installation

```bash
git clone https://github.com/frackisto/impactvoyage.git && cd impactvoyage
cp .env.prod.example .env.prod
chmod 600 .env.prod
```

Renseigner `.env.prod` (chaque variable y est commentée) : domaines, email Let's Encrypt,
clés et mots de passe. Générer chaque secret séparément :

```bash
openssl rand -base64 48 | tr -d '/+=' | cut -c1-50
```

Raccourci utilisé dans la suite du guide (à ajouter à `~/.bashrc`) :

```bash
alias dc='docker compose -f docker-compose.prod.yml --env-file .env.prod'
```

Premier démarrage :

```bash
dc up -d --build
dc ps                      # tous les services « healthy » ou « running »
dc logs -f certbot nginx   # obtention du certificat
```

Nginx démarre avec un certificat autosigné provisoire, le temps que Let's Encrypt
valide les domaines (défi HTTP sur le port 80) ; le vrai certificat est chargé dans la
minute qui suit, sans redémarrage. En cas d'échec (DNS pas encore propagé, port 80
fermé), certbot réessaie toutes les heures.

> **Premier essai sans risque** : `LETSENCRYPT_STAGING=1` demande un certificat de test
> (non reconnu par les navigateurs, mais sans quota). Pour passer ensuite au vrai :
> `dc run --rm --entrypoint certbot certbot delete --cert-name impactvoyage`, remettre
> `LETSENCRYPT_STAGING=0`, puis `dc up -d certbot`.

### Contenu et comptes

```bash
# Contenu réel de l'agence (coordonnées, services, destinations, photos)
dc exec backend python manage.py load_agency_content

# Premier super administrateur (connexion par email)
dc exec backend python manage.py createsuperuser
```

Le backoffice est à `https://API_DOMAIN/<ADMIN_URL_PATH>/` (`/admin/` répond 404). À la
première connexion, chaque membre de l'équipe enregistre la double authentification
(QR code) et note ses 10 codes de secours.

### Umami (statistiques de fréquentation)

1. Ouvrir `https://STATS_DOMAIN`, se connecter avec `admin` / `umami` et **changer
   immédiatement ce mot de passe** (Settings → Profile ; la langue de l'interface se
   choisit dans Settings → Preferences).
2. Settings → Websites → Add website : nom « Impact Voyage », domaine `SITE_DOMAIN`.
   Copier son **Website ID** dans `UMAMI_WEBSITE_ID`.
3. Settings → API keys → créer une clé (nom « tableau de bord ») : copier la clé
   `umami_…`, affichée une seule fois, dans `UMAMI_API_TOKEN`.
4. Appliquer, sans reconstruire : `dc up -d frontend backend celery celery-beat`.

Le site charge alors `/stats/script.js` (servi par Nginx, aucun domaine tiers) et la carte
« Visiteurs » du tableau de bord affiche les 30 derniers jours. Umami ne dépose aucun
cookie, ne conserve pas les adresses IP et respecte « Do Not Track ».

## 4. Vérifications après installation

```bash
curl -I http://SITE_DOMAIN/                       # 301 vers https://
curl -sI https://SITE_DOMAIN/ | grep -i strict    # HSTS
curl -s https://API_DOMAIN/api/v1/health/         # {"status": "ok", ...}
curl -s -o /dev/null -w "%{http_code}\n" https://API_DOMAIN/admin/   # 404
dc exec backend python manage.py check --deploy   # aucun avertissement
```

Puis, dans un navigateur : une fiche avec photos, un formulaire (devis ou contact, avec
le widget Turnstile), l'arrivée de l'email, le backoffice.

## 5. Mettre à jour le site

```bash
git pull
dc up -d --build
```

Les migrations, la synchronisation des rôles et `collectstatic` s'exécutent au
redémarrage du backend ; le site attend que Django soit prêt. Pendant les quelques
secondes de bascule, Nginx affiche une page « Site en cours de mise à jour ». Avant une
mise à jour importante, lancer une sauvegarde (§ 6).

Changer une valeur de `.env.prod` : `dc up -d` recrée les services concernés. Les
valeurs figées au build du site (`SITE_DOMAIN`, `NEXT_PUBLIC_TURNSTILE_SITE_KEY`,
`SEO_NOINDEX`) demandent `dc up -d --build frontend`.

Journaux : `dc logs -f backend` (Django, Gunicorn), `dc logs -f nginx` (accès, requêtes
limitées), `dc logs celery` (emails). Chaque fichier de journal est limité à 5 × 10 Mo.

## 6. Sauvegardes

Le service `backup` sauvegarde chaque nuit à `BACKUP_TIME` (UTC, l'heure d'Abidjan) dans
`BACKUP_DIR` (`./backups` par défaut) :

```
backups/2026-10-01_0230/
├── voyage_db.dump     base du site (pg_dump, format compressé)
├── umami.dump         statistiques
├── media.tar.gz       photos téléversées
└── SHA256SUMS         empreintes, vérifiées avant toute restauration
```

Les bases sont gardées `BACKUP_RETENTION_DAYS` jours (30), les archives des médias
`MEDIA_BACKUP_RETENTION_DAYS` jours (7). Le 1er de chaque mois, la dernière sauvegarde
est restaurée dans une base temporaire puis vérifiée (`dc logs backup`).

**Copie hors du serveur — indispensable** : une sauvegarde restée sur le serveur disparaît
avec lui. Par exemple, chaque nuit après la sauvegarde, vers un stockage S3 avec
[rclone](https://rclone.org) (crontab de l'hôte) :

```bash
30 3 * * * rclone sync /chemin/impactvoyage/backups s3-agence:impactvoyage-sauvegardes
```

Commandes utiles :

```bash
dc exec backup sh /opt/backup/backup.sh           # sauvegarde immédiate
dc exec backup sh /opt/backup/restore-check.sh    # test de restauration
```

### Restaurer

```bash
# 1. Arrêter ce qui écrit dans la base
dc stop frontend backend celery celery-beat
# 2. Restaurer la base du site (la base actuelle est remplacée)
dc exec backup sh /opt/backup/restore.sh 2026-10-01_0230 voyage_db
# 3. Si besoin, les photos (archive complète, fichiers existants écrasés)
dc run --rm --no-deps -T backend tar -xzf - -C /app/media < backups/2026-10-01_0230/media.tar.gz
# 4. Redémarrer
dc up -d
```

Pour les statistiques : `dc stop umami`, `restore.sh <dossier> umami`, `dc up -d`.

## 7. Recette

Une installation de recette utilise les mêmes fichiers, avec ses propres domaines et :

```bash
SEO_NOINDEX=true          # jamais indexée par les moteurs de recherche
DEMO_DATA_ALLOWED=True    # autorise seed_demo (signalé par check --deploy : core.W005)
```

```bash
dc up -d --build
dc exec backend python manage.py load_agency_content
dc exec backend python manage.py seed_demo
```

## 8. Sécurité de l'installation

- `.env.prod` contient tous les secrets : droits `600`, jamais commité, copié dans un
  gestionnaire de mots de passe.
- Les applications tournent sans root (`app`, `nextjs`), avec `no-new-privileges` ; le code
  de Django est en lecture seule dans son image ; seuls les médias et les fichiers
  statiques sont modifiables.
- Nginx : TLS 1.2 et 1.3 uniquement, HSTS (`preload`), poignée de main refusée pour un nom
  inconnu, médias limités aux images (jamais exécutés, CSP `sandbox`), corps de requête
  limité à 10 Mo sur le site et 64 Mo sur le backoffice.
- Limitation de débit par adresse IP : pages 20 requêtes/s (rafales de 100), optimisation
  d'images 30/s, routes `/api` du site 5/s (rafales de 30), Django 10/s ; au-delà, réponse
  429 (page dédiée, ou JSON au format de l'API). Les limites de Django (formulaires,
  connexion) s'appliquent en plus.
- Mises à jour du système : `sudo apt update && sudo apt upgrade` régulièrement ; images
  de base : `dc pull && dc up -d --build` une fois par mois.
