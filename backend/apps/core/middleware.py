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
