# auth_api/views.py — VERSION FINALE, NETTE ET SANS REDONDANCE
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.cache import cache
from django.utils import timezone

from .models import User
from .serializers import RegisterSerializer
from .utils import send_otp_terminal


# ──────────────────────── INSCRIPTION ────────────────────────
class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        send_otp_terminal(user.id, user.email)
        return Response({
            "user_id": user.id,
            "email": user.email,
            "role": user.role
        }, status=status.HTTP_201_CREATED)


# ──────────────────────── RENVIOYER OTP ────────────────────────
class SendOTPView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')
        try:
            user = User.objects.get(id=user_id, is_active=False)
            send_otp_terminal(user.id, user.email)
            return Response({"status": "otp_sent"})
        except User.DoesNotExist:
            return Response({"error": "Utilisateur introuvable ou déjà activé"}, status=404)


# ──────────────────────── VÉRIFIER OTP ────────────────────────
class VerifyOTPView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')
        code = request.data.get('code')

        if cache.get(f"otp_{user_id}") == code:
            user = User.objects.get(id=user_id)
            user.is_verified = user.is_active = True
            user.save()
            cache.delete(f"otp_{user_id}")

            refresh = RefreshToken.for_user(user)
            return Response({
                "verified": True,
                "token": str(refresh.access_token),
                "user": {"id": user.id, "nom": user.first_name or user.username, "role": user.role}
            })

        return Response({"verified": False, "error": "Code invalide"}, status=400)


# ──────────────────────── CONNEXION (compatible password + mot_de_passe) ────────────────────────
class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('mot_de_passe') or request.data.get('password')

        if not email or not password:
            return Response({"error": "Email et mot de passe requis"}, status=400)

        user = authenticate(username=email, password=password)
        if user and user.is_active and user.is_verified:
            refresh = RefreshToken.for_user(user)
            return Response({
                "token": str(refresh.access_token),
                "user": {"id": user.id, "email": user.email, "role": user.role, "is_superuser": user.is_superuser}
            })

        return Response({"error": "Identifiants incorrects ou compte non vérifié"}, status=401)


# ──────────────────────── MOT DE PASSE OUBLIÉ ────────────────────────
class ForgotPasswordView(APIView):
    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email, is_active=True)
            send_otp_terminal(user.id, user.email)
            return Response({"status": "otp_sent", "user_id": user.id})
        except User.DoesNotExist:
            return Response({"error": "Aucun compte actif avec cet email"}, status=404)


class ResetPasswordView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')
        code = request.data.get('code')
        nouveau = request.data.get('nouveau_mot_de_passe')

        if len(nouveau) < 8:
            return Response({"error": "Mot de passe trop court"}, status=400)

        if cache.get(f"otp_{user_id}") == code:
            user = User.objects.get(id=user_id)
            user.set_password(nouveau)
            user.save()
            cache.delete(f"otp_{user_id}")
            refresh = RefreshToken.for_user(user)
            return Response({"success": True, "token": str(refresh.access_token)})

        return Response({"error": "Code invalide"}, status=400)


# ──────────────────────── DEVENIR BAILLEUR ────────────────────────
class BecomeBailleurView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.role != 'locataire':
            return Response({"error": "Déjà bailleur ou admin"}, status=400)

        cni = request.FILES.get('cni')
        titre = request.FILES.get('titre_foncier')
        adresse = request.data.get('adresse')
        ville = request.data.get('ville')

        if not all([cni, titre, adresse, ville]):
            return Response({"error": "Tous les champs sont requis"}, status=400)

        user.cni_document = cni
        user.titre_foncier = titre
        user.adresse = adresse
        user.ville = ville
        user.role = 'bailleur_pending'
        user.bailleur_request_date = timezone.now()
        user.save()

        return Response({"success": True, "message": "Demande envoyée !"})


# ──────────────────────── APPROBATION BAILLEUR ────────────────────────
class ApproveBailleurView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id, role='bailleur_pending')
            user.role = 'bailleur'
            user.save()
            return Response({"success": True, "message": f"{user.email} est maintenant bailleur"})
        except User.DoesNotExist:
            return Response({"error": "Utilisateur introuvable ou pas en attente"}, status=404)


# ──────────────────────── STATUT BAILLEUR ────────────────────────
class BailleurStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "role": user.role,
            "is_locataire": user.role == 'locataire',
            "is_bailleur_pending": user.role == 'bailleur_pending',
            "is_bailleur": user.role == 'bailleur',
            "can_post_listings": user.role == 'bailleur',
            "request_date": user.bailleur_request_date.isoformat() if user.bailleur_request_date else None
        })


# ──────── SUPER ADMIN : VÉRIFIER / CRÉER (UNE SEULE FOIS) ────────
@api_view(['GET'])
@permission_classes([AllowAny])
def check_superadmin_exists(request):
    return Response({"exists": User.objects.filter(is_superuser=True).exists()})


@api_view(['POST'])
@permission_classes([AllowAny])
def create_superadmin(request):
    if User.objects.filter(is_superuser=True).exists():
        return Response({"error": "Super Admin déjà créé"}, status=400)

    email = request.data.get('email')
    password = request.data.get('mot_de_passe') or request.data.get('password')
    if not email or not password:
        return Response({"error": "Email et mot de passe requis"}, status=400)

    user = User.objects.create_superuser(
        username=email, email=email, password=password,
        role='admin', is_verified=True, is_staff=True, is_superuser=True
    )
    refresh = RefreshToken.for_user(user)
    return Response({"success": True, "token": str(refresh.access_token)})


# ──────── SUPER ADMIN : GESTION UTILISATEURS (4 FONCTIONS UNIQUES) ────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_users(request):
    if not request.user.is_superuser:
        return Response({"error": "Super Admin uniquement"}, status=403)
    users = User.objects.all().values('id', 'email', 'first_name', 'role', 'is_verified', 'is_active', 'date_joined')
    return Response(list(users))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_role(request, user_id):
    if not request.user.is_superuser:
        return Response({"error": "Super Admin uniquement"}, status=403)
    try:
        user = User.objects.get(id=user_id)
        role = request.data.get('role')
        if role not in ['locataire', 'bailleur', 'admin']:
            return Response({"error": "Rôle invalide"}, status=400)
        user.role = role
        user.save()
        return Response({"success": True})
    except User.DoesNotExist:
        return Response({"error": "Utilisateur introuvable"}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_user(request):
    if not request.user.is_superuser:
        return Response({"error": "Super Admin uniquement"}, status=403)
    
    email = request.data.get('email')
    password = request.data.get('mot_de_passe') or request.data.get('password')
    nom = request.data.get('nom', '')
    role = request.data.get('role', 'locataire')

    if not email or not password:
        return Response({"error": "Email et mot de passe requis"}, status=400)
    if User.objects.filter(email=email).exists():
        return Response({"error": "Email déjà utilisé"}, status=400)

    user = User.objects.create_user(username=email, email=email, password=password, first_name=nom, role=role, is_verified=True, is_active=True)
    return Response({"success": True, "user_id": user.id})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user(request, user_id):
    if not request.user.is_superuser:
        return Response({"error": "Super Admin uniquement"}, status=403)
    try:
        user = User.objects.get(id=user_id)
        if user.is_superuser:
            return Response({"error": "Impossible de supprimer un Super Admin"}, status=400)
        user.delete()
        return Response({"success": True})
    except User.DoesNotExist:
        return Response({"error": "Utilisateur introuvable"}, status=404)