from django.conf import settings
from django.utils import translation

LANGUAGE_CODES = {code for code, _ in settings.LANGUAGES}


class QueryLanguageMiddleware:
    """
    ?lang=en force la langue de la réponse (liens partagés, tests, SEO).
    Placé après LocaleMiddleware, qui lit Accept-Language.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = request.GET.get("lang")
        if lang in LANGUAGE_CODES:
            translation.activate(lang)
            request.LANGUAGE_CODE = lang
        return self.get_response(request)


# API et fichiers servis par Django : rien à exécuter ni à afficher dans un cadre.
API_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
# Backoffice (unfold) : scripts et styles servis par Django ; Alpine.js, utilisé par
# unfold, évalue ses expressions (« unsafe-eval ») et les gabarits contiennent du code
# en ligne. La politique interdit tout chargement depuis un autre domaine.
ADMIN_CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "font-src 'self' data:",
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
])
# Swagger et ReDoc (drf-spectacular) chargent leurs scripts depuis un CDN.
DOCS_PATHS = ("/api/v1/docs/", "/api/v1/redoc/")


class ContentSecurityPolicyMiddleware:
    """
    En-tête Content-Security-Policy des réponses de Django (Phase 23). Les pages du
    site sont servies par Next.js, qui pose sa propre politique (frontend/proxy.ts).
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.admin_prefix = "/" + settings.ADMIN_URL

    def __call__(self, request):
        response = self.get_response(request)
        if "Content-Security-Policy" in response or request.path.startswith(DOCS_PATHS):
            return response
        if settings.DEBUG and response.status_code >= 400:  # pages d'erreur détaillées (styles en ligne)
            return response
        admin = request.path.startswith(self.admin_prefix)
        response["Content-Security-Policy"] = ADMIN_CSP if admin else API_CSP
        return response
