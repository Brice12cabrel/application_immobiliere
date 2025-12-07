import random
from django.core.cache import cache
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # ON AJOUTE CES CHAMPS DANS LE TOKEN
        token['role'] = user.role
        token['is_superuser'] = user.is_superuser
        token['is_staff'] = user.is_staff
        token['user_id'] = user.id
        token['email'] = user.email

        return token

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
def send_otp_terminal(user_id: int, email: str):
    code = str(random.randint(100000, 999999))
    print("\n" + "═" * 65)
    print(" OTP DE SÉCURITÉ – NE PAS PARTAGER")
    print(f" User ID : {user_id}")
    print(f" Email   : {email}")
    print(f" CODE → → →  {code}  ← ← ←  (valable 10 minutes)")
    print("═" * 65 + "\n")
    
    cache.set(f"otp_{user_id}", code, timeout=600)
    return code