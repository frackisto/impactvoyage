"""Emails des comptes (Phase 20), dans la langue préférée de l'utilisateur."""
from apps.notifications.emails import Email, frontend_url, pick


def _greeting(user):
    name = user.first_name
    return pick(user.preferred_language, f"Bonjour {name}," if name else "Bonjour,",
                f"Hello {name}," if name else "Hello,")


def verification(user, token):
    lang = user.preferred_language
    return Email(
        subject=pick(lang, "Confirmez votre adresse email", "Confirm your email address"),
        heading=pick(lang, "Bienvenue chez Impact Voyage !", "Welcome to Impact Voyage!"),
        language=lang,
        greeting=_greeting(user),
        paragraphs=[pick(
            lang,
            "Confirmez votre adresse email pour activer toutes les fonctions de votre compte. "
            "Le lien est valable 3 jours.",
            "Confirm your email address to activate all the features of your account. "
            "The link is valid for 3 days.",
        )],
        action=(pick(lang, "Confirmer mon adresse", "Confirm my address"),
                frontend_url(f"/verifier-email?token={token}", lang)),
        note=pick(lang, "Vous n'avez pas créé de compte ? Ignorez ce message.",
                  "You did not create an account? Ignore this message."),
    )


def password_reset(user, uid, token, minutes):
    lang = user.preferred_language
    return Email(
        subject=pick(lang, "Réinitialisation de votre mot de passe", "Reset your password"),
        heading=pick(lang, "Choisissez un nouveau mot de passe", "Choose a new password"),
        language=lang,
        greeting=_greeting(user),
        paragraphs=[pick(
            lang,
            f"Pour choisir un nouveau mot de passe, ouvrez ce lien (valable {minutes} minutes, "
            "une seule utilisation).",
            f"To choose a new password, open this link (valid for {minutes} minutes, "
            "single use).",
        )],
        action=(pick(lang, "Choisir un nouveau mot de passe", "Choose a new password"),
                frontend_url(f"/reset-password?uid={uid}&token={token}", lang)),
        note=pick(lang, "Si vous n'êtes pas à l'origine de cette demande, ignorez ce message : "
                        "votre mot de passe reste inchangé.",
                  "If you did not make this request, ignore this message: your password "
                  "remains unchanged."),
    )
