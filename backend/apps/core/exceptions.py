"""
Erreurs métier levées par les services. Indépendantes de DRF : la couche API
(Phase 6) les traduit en réponses JSON au format unique de l'architecture § 5.1.
"""


class BusinessError(Exception):
    """Règle métier non respectée. `code` est stable et exploitable par le frontend."""

    code = "business_error"
    status_code = 400

    def __init__(self, message, code=None, details=None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        self.details = details or {}


class NotAvailable(BusinessError):
    """Stock insuffisant ou créneau déjà pris (places, véhicule, chambre...)."""

    code = "not_available"
    status_code = 409


class InvalidTransition(BusinessError):
    """Changement de statut interdit depuis le statut actuel."""

    code = "invalid_transition"
    status_code = 409


class InvalidToken(BusinessError):
    """Lien client (devis) invalide."""

    code = "invalid_token"
    status_code = 404
