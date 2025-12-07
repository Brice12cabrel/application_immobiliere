# auth_api/serializers.py
from rest_framework import serializers
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    mot_de_passe = serializers.CharField(write_only=True, min_length=8)
    # On accepte "nom" dans le JSON, mais on le stocke dans first_name
    nom = serializers.CharField(max_length=150, write_only=True)

    class Meta:
        model = User
        fields = ('nom', 'email', 'mot_de_passe', 'phone_number', 'photo_profil')

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    def create(self, validated_data):
        # On extrait le "nom" qu’on a reçu
        nom = validated_data.pop('nom', '')
        mot_de_passe = validated_data.pop('mot_de_passe')

        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            first_name=nom,                     # ← ici on met le nom
            phone_number=validated_data.get('phone_number'),
            photo_profil=validated_data.get('photo_profil'),
            is_active=False,
            is_verified=False
        )
        user.set_password(mot_de_passe)
        user.save()
        return user