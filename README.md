# Plateforme Web Agence de Voyage — Phase 2

Initialisation Django + PostgreSQL + Redis + Celery, dockerisée.

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

Créer un compte administrateur :

```bash
docker compose exec backend python manage.py createsuperuser
```

## Démarrage sans Docker (alternative)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # adapter DATABASE_HOST=localhost
python manage.py migrate
python manage.py runserver
```

Nécessite une instance PostgreSQL et Redis locales déjà démarrées.

## Structure créée à cette étape

```
.
├── docker-compose.yml
├── .env.example
├── README.md
└── backend/
    ├── config/
    │   ├── settings/{base,dev,prod,test}.py
    │   ├── urls.py, api_urls.py
    │   ├── wsgi.py, asgi.py, celery.py
    ├── apps/
    │   ├── core/           # mixins partagés (TimeStamped, Slug, SoftDelete)
    │   ├── accounts/       # modèle User minimal (étendu en Phase 3)
    │   └── ... (18 autres apps, squelettes vides — peuplées en Phase 3)
    ├── manage.py
    ├── requirements.txt
    ├── Dockerfile
    └── .env.example
```

## Ce qui a été validé

- `python manage.py check` → aucune erreur de configuration.
- `python manage.py makemigrations` → génère correctement la migration initiale du modèle `User`.
- Les 20 apps locales (19 apps métier + `core`) sont enregistrées dans `INSTALLED_APPS` et démarrent sans conflit.

## Prochaine étape

**Phase 3 : Création des modèles et migrations** — on remplira les modèles de chaque app (`Destination`, `Tour`, `Hotel`, etc.) selon le schéma défini dans l'architecture globale, puis on génèrera et appliquera les migrations correspondantes.
