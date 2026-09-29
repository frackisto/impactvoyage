"""
Emails transactionnels (Phase 20, CdC § 30).

Chaque email est décrit par un objet Email (titre, paragraphes, récapitulatif,
bouton d'action) construit par l'app métier, puis rendu dans une mise en page
commune en HTML et en texte brut (templates/emails/message.{html,txt}), dans la
langue du destinataire. Aucune logique de langue dans les gabarits : les textes
fixes de la mise en page sont ici, les textes métier dans les apps.

L'envoi part après validation de la transaction, par Celery (jamais d'email
pour une opération annulée).
"""
from dataclasses import dataclass, field

from django.conf import settings
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import translation

DEFAULT_LANGUAGE = "fr"


def normalize_language(language):
    codes = {code for code, _ in settings.LANGUAGES}
    language = (language or "").split("-")[0].lower()
    return language if language in codes else DEFAULT_LANGUAGE


def pick(language, fr, en):
    """Texte dans la langue du destinataire (le français par défaut)."""
    return en if normalize_language(language) == "en" else fr


def frontend_url(path, language=DEFAULT_LANGUAGE):
    """Lien vers le site dans la langue du client : /… en français, /en/… sinon."""
    language = normalize_language(language)
    prefix = "" if language == settings.LANGUAGE_CODE else f"/{language}"
    return f"{settings.FRONTEND_URL}{prefix}{path}"


# Textes fixes de la mise en page, par langue.
LAYOUT = {
    "fr": {
        "signature": "L'équipe Impact Voyage",
        "colon": " :",
        "button_fallback": "Si le bouton ne fonctionne pas, copiez ce lien dans votre navigateur :",
        "footer": "Cet email vous est envoyé suite à votre démarche auprès d'Impact Voyage. "
                  "Pour toute question, répondez simplement à ce message.",
        "agency_footer": "Notification automatique du site Impact Voyage.",
    },
    "en": {
        "signature": "The Impact Voyage team",
        "colon": ":",
        "button_fallback": "If the button does not work, copy this link into your browser:",
        "footer": "You are receiving this email following your request to Impact Voyage. "
                  "For any question, simply reply to this message.",
        "agency_footer": "Automatic notification from the Impact Voyage website.",
    },
}


@dataclass
class Email:
    """Contenu d'un email, indépendant de sa mise en forme."""

    subject: str
    heading: str
    language: str = DEFAULT_LANGUAGE
    greeting: str = ""
    paragraphs: list = field(default_factory=list)
    details: list = field(default_factory=list)  # [(libellé, valeur)]
    action: tuple | None = None  # (libellé du bouton, URL)
    note: str = ""  # texte discret après le bouton
    reply_to: list = field(default_factory=list)
    for_agency: bool = False  # email interne : pas de signature client


def _agency():
    from apps.core.models import SiteSettings

    site = SiteSettings.load()
    return {
        "name": site.agency_name,
        "phone": site.phone,
        "whatsapp": site.whatsapp,
        "email": site.email,
        "address": site.address,
    }


def render(email):
    """(sujet, texte, html) de l'email, dans sa langue."""
    language = normalize_language(email.language)
    context = {
        "email": email,
        "lang": language,
        "layout": LAYOUT[language],
        "agency": _agency(),
        "site_url": frontend_url("/", language),
        "logo_url": f"{settings.EMAIL_ASSETS_URL.rstrip('/')}/brand/emblem.png",
        # Version texte : une ligne par information.
        "text_details": [(label, " · ".join(str(value).splitlines()))
                         for label, value in email.details],
    }
    with translation.override(language):
        text = render_to_string("emails/message.txt", context).strip() + "\n"
        html = render_to_string("emails/message.html", context)
    return email.subject, text, html


def send_email(to, email):
    """Programme l'envoi après validation de la transaction."""
    from .tasks import send_email_task

    recipients = [to] if isinstance(to, str) else list(to)
    subject, text, html = render(email)
    # Un client qui répond écrit à l'adresse publique de l'agence (paramètres du site).
    reply_to = list(email.reply_to) or (
        [] if email.for_agency else [_agency()["email"] or settings.AGENCY_NOTIFICATION_EMAIL]
    )
    transaction.on_commit(
        lambda: send_email_task.delay(recipients, subject, text, html, reply_to)
    )
