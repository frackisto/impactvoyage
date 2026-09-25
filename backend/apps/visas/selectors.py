from .models import VisaService


def visa_list(destination_country_code=None, nationality_code=None, purpose=None):
    """Recherche visa (CdC § 7) : pays de destination, nationalité, motif."""
    qs = VisaService.objects.published()
    if destination_country_code:
        qs = qs.filter(destination_country_code=destination_country_code.upper())
    if nationality_code:
        qs = qs.filter(nationality_code=nationality_code.upper())
    if purpose:
        qs = qs.filter(purpose=purpose)
    return qs


def visas_for_country(country_slug):
    """Page /visa/<pays> : toutes les formules pour un pays de destination."""
    return VisaService.objects.published().filter(country_slug=country_slug)
