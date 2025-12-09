from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.cache import cache
from .models import User
from .serializers import RegisterSerializer
from .utils import send_otp_terminal


from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone   # ← OBLIGATOIRE pour timezone.now()
# ──────────────────────── SUPER ADMIN ────────────────────────
#
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response



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
            "role": user.role,
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
            user.is_verified = True
            user.is_active = True
            user.save()
            cache.delete(f"otp_{user_id}")

            refresh = RefreshToken.for_user(user)
            return Response({
                "verified": True,
                "token": str(refresh.access_token),
                "user": {
                    "id": user.id,
                    "nom": user.first_name or user.username,
                    "role": user.role
                }
            })

        return Response({"verified": False, "error": "Code invalide"}, status=400)


# ──────────────────────── CONNEXION ────────────────────────
class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('mot_de_passe') or request.data.get('password')

        user = authenticate(username=email, password=password)
        if user and user.is_active and user.is_verified:
            refresh = RefreshToken.for_user(user)
            return Response({
                "token": str(refresh.access_token),
                "user": {
                    "id": user.id,
                    "nom": user.first_name or user.username,
                    "role": user.role
                }
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
            return Response({
                "success": True,
                "message": "Mot de passe réinitialisé",
                "token": str(refresh.access_token)
            })

        return Response({"error": "Code invalide"}, status=400)


# ──────────────────────── devenir bailleur ────────────────────────
    
# auth_api/views.py → BecomeBailleurView
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

        # On sauvegarde directement les fichiers
        user.cni_document = cni
        user.titre_foncier = titre
        user.adresse = adresse
        user.ville = ville
        user.role = 'bailleur_pending'
        user.bailleur_request_date = timezone.now()
        user.save()

        return Response({
            "success": True,
            "message": "Demande envoyée ! L'admin va vérifier vos documents."
        })

# ──────────────────────── approbation de bailleur ────────────────────────

class ApproveBailleurView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            if user.role != 'bailleur_pending':
                return Response({"error": "Pas en attente"}, status=400)

            user.role = 'bailleur'
            user.save()
            return Response({"success": True, "message": f"{user.email} est maintenant bailleur"})
        except User.DoesNotExist:
            return Response({"error": "Utilisateur introuvable"}, status=404)


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



# ──────── SUPER ADMIN : VÉRIFIER S'IL EXISTE ────────
@api_view(['GET'])
@permission_classes([AllowAny])
def check_superadmin_exists(request):
    exists = User.objects.filter(is_superuser=True).exists()
    return Response({"exists": exists})


# ──────── SUPER ADMIN : CRÉATION UNIQUE ────────
@api_view(['POST'])
@permission_classes([AllowAny])
def create_superadmin(request):
    # Empêche la création s'il existe déjà
    if User.objects.filter(is_superuser=True).exists():
        return Response({"error": "Super Admin déjà créé"}, status=400)

    email = request.data.get('email')
    password = request.data.get('mot_de_passe') or request.data.get('password')

    if not email or not password:
        return Response({"error": "Email et mot de passe requis"}, status=400)

    # Création du superuser (username = email)
    user = User.objects.create_superuser(
        username=email,      # ← OBLIGATOIRE
        email=email,
        password=password,
        role='admin',
        is_verified=True,
        is_staff=True,
        is_superuser=True
    )

    # Génère le token
    refresh = RefreshToken.for_user(user)
    return Response({
        "success": True,
        "message": "Super Admin créé avec succès",
        "token": str(refresh.access_token)
    })
    
# ──────── SUPER ADMIN : LISTE TOUS LES UTILISATEURS ────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_users(request):
    if not request.user.is_superuser:
        return Response({"error": "Super Admin uniquement"}, status=403)
    
    users = User.objects.all().values(
        'id', 'email', 'first_name', 'role', 'is_verified', 'is_active', 'date_joined'
    )
    return Response(list(users))

# ──────── CHANGER RÔLE ────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_role(request, user_id):
    if not request.user.is_superuser:
        return Response({"error": "Super Admin uniquement"}, status=403)
    
    try:
        user = User.objects.get(id=user_id)
        new_role = request.data.get('role')
        if new_role not in ['locataire', 'bailleur', 'admin']:
            return Response({"error": "Rôle invalide"}, status=400)
        
        user.role = new_role
        user.save()
        return Response({"success": True, "message": f"Rôle changé en {new_role}"})
    except User.DoesNotExist:
        return Response({"error": "Utilisateur introuvable"}, status=404)

# ──────── CRÉER UTILISATEUR ────────
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

    user = User.objects.create_user(
        username=email,
        email=email,
        password=password,
        first_name=nom,
        role=role,
        is_verified=True,
        is_active=True
    )
    return Response({"success": True, "message": "Utilisateur créé", "user_id": user.id})

# ──────── SUPPRIMER UTILISATEUR ────────
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


# ──────── SUPER ADMIN : LISTE TOUS LES UTILISATEURS ────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_users(request):
    if not request.user.is_superuser:
        return Response({"error": "Accès réservé au Super Admin"}, status=403)
    
    users = User.objects.all().values(
        'id', 'email', 'first_name', 'last_name', 'role', 'is_verified', 'is_active', 'date_joined'
    )
    return Response(list(users))


# ──────── CHANGER LE RÔLE D'UN UTILISATEUR ────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_role(request, user_id):
    if not request.user.is_superuser:
        return Response({"error": "Super Admin uniquement"}, status=403)
    
    try:
        user = User.objects.get(id=user_id)
        new_role = request.data.get('role')
        
        if new_role not in ['locataire', 'bailleur', 'admin']:
            return Response({"error": "Rôle invalide"}, status=400)
        
        user.role = new_role
        user.save()
        return Response({"success": True, "message": f"Rôle changé → {new_role}"})
    except User.DoesNotExist:
        return Response({"error": "Utilisateur introuvable"}, status=404)


# ──────── CRÉER UN UTILISATEUR ────────
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
        return Response({"error": "Cet email est déjà utilisé"}, status=400)

    user = User.objects.create_user(
        username=email,
        email=email,
        password=password,
        first_name=nom,
        role=role,
        is_verified=True,
        is_active=True
    )
    return Response({"success": True, "message": "Utilisateur créé", "user_id": user.id})


# ──────── SUPPRIMER UN UTILISATEUR ────────
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
        return Response({"success": True, "message": "Utilisateur supprimé"})
    except User.DoesNotExist:
        return Response({"error": "Utilisateur introuvable"}, status=404)
    
    
    # ──────── ADMIN : LISTE DES DEMANDES BAILLEURS EN ATTENTE ────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pending_bailleur_requests(request):
    # Autorise admin ET superadmin
    if request.user.role != 'admin' and not request.user.is_superuser:
        return Response({"error": "Accès réservé aux administrateurs"}, status=403)
    
    users = User.objects.filter(role='bailleur_pending').values(
        'id', 'email', 'first_name', 'adresse', 'ville',
        'cni_document', 'titre_foncier', 'bailleur_request_date'
    )
    return Response(list(users))

# ──────── ADMIN : REJETER UNE DEMANDE BAILLEUR ────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_bailleur(request, user_id):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return Response({"error": "Accès refusé"}, status=403)

    try:
        user = User.objects.get(id=user_id, role='bailleur_pending')
        
        # SUPPRIME LES FICHIERS PHYSIQUEMENT
        if user.cni_document:
            user.cni_document.delete(save=False)
        if user.titre_foncier:
            user.titre_foncier.delete(save=False)

        # REMET EN LOCATAIRE
        user.role = 'locataire'
        user.cni_document = None
        user.titre_foncier = None
        user.adresse = None
        user.ville = None
        user.bailleur_request_date = None
        user.save()

        return Response({"success": True, "message": "Demande rejetée et documents supprimés"})
    
    except User.DoesNotExist:
        return Response({"error": "Demande introuvable"}, status=404)