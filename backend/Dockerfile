FROM python:3.13-slim

# Empêche Python de bufferiser stdout/stderr et de générer des .pyc.
# Dépendances dans un environnement virtuel appartenant à l'utilisateur de l'application :
# en développement, « pip install -r requirements-dev.txt » fonctionne sans root.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH

# Utilisateur sans privilèges (Phase 24). UID 1000 : celui de l'utilisateur habituel d'un
# hôte Linux, propriétaire du dossier monté en développement. Dossier personnel hors du
# code : les caches (pip...) ne s'écrivent pas dans /app.
RUN groupadd --system --gid 1000 app \
    && useradd --system --uid 1000 --gid app --home-dir /home/app --create-home \
       --shell /usr/sbin/nologin app \
    && python -m venv "$VIRTUAL_ENV" \
    && chown -R app:app "$VIRTUAL_ENV"

WORKDIR /app

# psycopg[binary] et Pillow sont fournis précompilés : aucun outil de compilation.
COPY requirements.txt .
USER app
RUN pip install --no-cache-dir -r requirements.txt

# Le code appartient à root (lecture seule pour l'application) ; seuls les fichiers
# statiques collectés et les médias téléversés sont modifiables. Un volume vide monté
# sur ces dossiers reprend leur propriétaire.
USER root
COPY . .
RUN mkdir -p staticfiles media && chown app:app staticfiles media
USER app

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application"]
