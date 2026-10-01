"""
Configuration de Gunicorn (Phase 24), lue automatiquement depuis le dossier courant.
Derrière Nginx en production : il termine le TLS et transmet X-Forwarded-Proto.
"""
import os

bind = "0.0.0.0:8000"
# WEB_CONCURRENCY : nombre de processus (2 × cœurs + 1 est un bon point de départ).
workers = int(os.environ.get("WEB_CONCURRENCY", "3"))
timeout = 60
graceful_timeout = 30
keepalive = 5
# Processus renouvelés régulièrement : une fuite de mémoire ne s'accumule pas.
max_requests = 1000
max_requests_jitter = 100
# Battements de cœur des processus en mémoire (le disque d'un conteneur peut être lent).
worker_tmp_dir = "/dev/shm"
# Seul Nginx joint Gunicorn (réseau Docker interne) : ses en-têtes X-Forwarded-* sont fiables.
forwarded_allow_ips = "*"

# Journaux sur la sortie standard (docker compose logs), adresse réelle posée par Nginx.
accesslog = "-"
errorlog = "-"
access_log_format = '%({x-real-ip}i)s "%(r)s" %(s)s %(b)s %(M)sms "%(a)s"'
