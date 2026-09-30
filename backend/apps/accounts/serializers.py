from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.core.serializers import HoneypotSerializerMixin
from apps.core.validators import strip_image_metadata
from apps.inquiries.serializers import validate_country_code, validate_phone

from . import otp

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

    def validate_avatar(self, value):
        if not value:
            return value
        # Contenu déjà contrôlé par les validateurs du modèle ; retrait des métadonnées
        # (position GPS de la photo).
        return strip_image_metadata(value)

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


class LoginSerializer(TokenObtainPairSerializer):
    """
    Connexion email + mot de passe. Le jeton d'accès porte le rôle et le nom
    (affichage et redirections côté Next.js) ; la réponse inclut le profil.

    Membres de l'équipe (Phase 23) : le code de double authentification est exigé
    en plus (`otp_code`), comme dans le backoffice. Erreurs : `otp_required` (code
    à demander), `otp_invalid`, `otp_setup_required` (application jamais enregistrée :
    se connecter d'abord au backoffice).
    """

    otp_code = serializers.CharField(required=False, allow_blank=True, write_only=True,
                                     help_text="Code de double authentification (équipe)")

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["name"] = user.get_full_name()
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        if otp.otp_required(self.user):
            self._check_otp(attrs.get("otp_code", ""))
        data["user"] = UserSerializer(self.user, context=self.context).data
        return data

    def _check_otp(self, code):
        if not otp.has_confirmed_device(self.user):
            raise otp.TwoFactorError(
                "Activez d'abord la double authentification en vous connectant au backoffice.",
                code="otp_setup_required",
            )
        if not code:
            raise otp.TwoFactorError(
                "Saisissez le code de votre application d'authentification.", code="otp_required"
            )
        if otp.verify_code(self.user, code) is None:
            raise otp.TwoFactorError("Code incorrect ou expiré.", code="otp_invalid")


class AuthResponseSerializer(serializers.Serializer):
    """Schéma OpenAPI des réponses d'inscription et de connexion."""

    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)
