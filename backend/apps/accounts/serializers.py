from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.core.serializers import HoneypotSerializerMixin
from apps.inquiries.serializers import validate_country_code, validate_phone

User = get_user_model()
LANGUAGE_CODES = [code for code, _ in settings.LANGUAGES]


class UserSerializer(serializers.ModelSerializer):
    """Profil de l'utilisateur connecté (/auth/me/). Rôle et vérification en lecture seule."""

    role_label = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "phone", "whatsapp", "country_code",
            "avatar", "preferred_language", "preferred_currency", "role", "role_label",
            "is_verified", "date_joined",
        ]
        read_only_fields = ["id", "email", "role", "is_verified", "date_joined"]

    validate_phone = staticmethod(validate_phone)
    validate_whatsapp = staticmethod(validate_phone)
    validate_country_code = staticmethod(validate_country_code)

    def validate_preferred_language(self, value):
        if value not in LANGUAGE_CODES:
            raise serializers.ValidationError("Langue non disponible.")
        return value


class RegisterSerializer(HoneypotSerializerMixin, serializers.Serializer):
    """Inscription d'un client (CdC § 24) ; validated_data prêt pour accounts.services.register_user."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=30,
                                  validators=[validate_phone])
    consent = serializers.BooleanField(write_only=True)

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Un compte existe déjà avec cet email.")
        return value

    def validate_consent(self, value):
        if not value:
            raise serializers.ValidationError("Vous devez accepter les conditions d'utilisation.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        candidate = User(email=attrs["email"], first_name=attrs["first_name"],
                         last_name=attrs["last_name"])
        try:
            validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as exc:  # erreur Django → erreur de champ DRF
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        attrs.pop("consent")
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Mot de passe actuel incorrect.")
        return value

    def validate_new_password(self, value):
        try:
            validate_password(value, user=self.context["request"].user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value
