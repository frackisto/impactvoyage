"""Outils des tests du backoffice : données d'un formulaire d'admin tel qu'affiché."""
from django import forms
from django.contrib.auth import get_user_model
from django.test import TestCase

from .helpers import make_user


def _put(data, key, field, value):
    if value is None or isinstance(field, forms.FileField):
        return
    if isinstance(field.widget, forms.MultiWidget):  # date + heure : champs _0 et _1
        parts = value if isinstance(value, (list, tuple)) else field.widget.decompress(value)
        for index, part in enumerate(parts):
            if part is not None:
                data[f"{key}_{index}"] = part
    elif isinstance(field, forms.JSONField):
        data[key] = field.prepare_value(value)
    elif isinstance(field, forms.BooleanField):
        if value:
            data[key] = "on"
    elif isinstance(value, (list, tuple)):
        data[key] = [str(v) for v in value]
    else:
        data[key] = value


def _form_data(form, data):
    for name, field in form.fields.items():
        _put(data, form.add_prefix(name), field, form[name].value())


def change_form_data(response, **overrides):
    """Valeurs du formulaire et des inlines d'une page de modification, prêtes à renvoyer."""
    data = {}
    _form_data(response.context["adminform"].form, data)
    for inline in response.context["inline_admin_formsets"]:
        formset = inline.formset
        _form_data(formset.management_form, data)
        for form in formset.forms:
            _form_data(form, data)
    data.update(overrides)
    return data


class AdminTestCase(TestCase):
    """Client connecté avec un rôle de l'équipe."""

    def login(self, role="SUPER_ADMIN", **kwargs):
        user = make_user(role, **kwargs)
        user = get_user_model().objects.get(pk=user.pk)
        self.client.force_login(user)
        return user
