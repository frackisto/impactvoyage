"""
Authentification JWT (CdC § 24 ; architecture § 6.1) : /api/v1/auth/...
Les jetons sont renvoyés dans le corps ; le frontend Next.js les stocke en
cookies httpOnly via ses Route Handlers (jamais dans localStorage).
"""
from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

from . import services
from .serializers import (
    AuthResponseSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    TokenSerializer,
    UserSerializer,
)

MESSAGE_SCHEMA = {200: {"type": "object", "properties": {"message": {"type": "string"}}}}


class AuthThrottleMixin:
    """10 tentatives par minute et par IP sur les points d'entrée sensibles (anti force brute)."""

    throttle_classes = [AnonRateThrottle, UserRateThrottle, ScopedRateThrottle]
    throttle_scope = "auth"


def tokens_for(user):
    refresh = RefreshToken.for_user(user)
    refresh["role"] = user.role
    refresh["name"] = user.get_full_name()
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class RegisterView(AuthThrottleMixin, APIView):
    """Inscription d'un client ; renvoie ses jetons et envoie le lien de vérification."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(request=RegisterSerializer, responses={201: AuthResponseSerializer})
    def post(self, request):
        payload = RegisterSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        user = services.register_user(**payload.validated_data)
        body = {**tokens_for(user), "user": UserSerializer(user, context={"request": request}).data}
        return Response(body, status=status.HTTP_201_CREATED)


@extend_schema(responses=AuthResponseSerializer)
class LoginView(AuthThrottleMixin, TokenObtainPairView):
    """Connexion email + mot de passe : jetons d'accès (15 min) et de rafraîchissement (7 j)."""


class RefreshView(TokenRefreshView):
    """Nouveau jeton d'accès ; le refresh est remplacé et l'ancien révoqué (rotation)."""


class LogoutView(TokenBlacklistView):
    """Déconnexion : révoque le refresh token fourni."""


class MeView(generics.RetrieveUpdateAPIView):
    """Profil de l'utilisateur connecté (le rôle et l'email ne sont pas modifiables ici)."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer
    http_method_names = ["get", "patch"]

    def get_object(self):
        return self.request.user


class PasswordChangeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=PasswordChangeSerializer, responses=MESSAGE_SCHEMA)
    def post(self, request):
        payload = PasswordChangeSerializer(data=request.data, context={"request": request})
        payload.is_valid(raise_exception=True)
        services.change_password(request.user, payload.validated_data["new_password"])
        return Response({"message": "Mot de passe modifié. Reconnectez-vous sur vos autres appareils."})


class PasswordResetRequestView(AuthThrottleMixin, APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=PasswordResetRequestSerializer, responses=MESSAGE_SCHEMA)
    def post(self, request):
        payload = PasswordResetRequestSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        services.request_password_reset(payload.validated_data["email"])
        # Même réponse que le compte existe ou non.
        return Response({"message": "Si un compte existe pour cet email, un lien vient d'être envoyé."})


class PasswordResetConfirmView(AuthThrottleMixin, APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=PasswordResetConfirmSerializer, responses=MESSAGE_SCHEMA)
    def post(self, request):
        payload = PasswordResetConfirmSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        try:
            services.reset_password(data["uid"], data["token"], data["new_password"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"new_password": list(exc.messages)}) from exc
        return Response({"message": "Mot de passe réinitialisé. Vous pouvez vous connecter."})


class VerifyEmailView(AuthThrottleMixin, APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=TokenSerializer, responses=MESSAGE_SCHEMA)
    def post(self, request):
        payload = TokenSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        services.verify_email(payload.validated_data["token"])
        return Response({"message": "Adresse email confirmée."})


class ResendVerificationView(AuthThrottleMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=None, responses=MESSAGE_SCHEMA)
    def post(self, request):
        services.send_verification_email(request.user)
        return Response({"message": "Un nouveau lien de vérification vient d'être envoyé."})
