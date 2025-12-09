from rest_framework import serializers
from .models import Listing
from django.core.files.storage import default_storage
from django.conf import settings  # pour MEDIA_URL
from django.core.exceptions import ValidationError
import imghdr  # pour vérifier le type réel de l'image

ALLOWED_IMAGE_TYPES = ('jpeg', 'png', 'gif')  # types autorisés

class SafeIntegerField(serializers.IntegerField):
    def to_internal_value(self, data):
        if data in ('', None):
            return None
        return super().to_internal_value(data)

    def to_representation(self, value):
        if value in ('', None):
            return None
        return super().to_representation(value)


class ListingSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )

    photos = serializers.SerializerMethodField(read_only=True)

    surface = SafeIntegerField(required=False, allow_null=True)
    chambres = SafeIntegerField(required=False, allow_null=True)
    salles_de_bain = SafeIntegerField(required=False, allow_null=True)
    etage = SafeIntegerField(required=False, allow_null=True)
    annee_construction = SafeIntegerField(required=False, allow_null=True)
    caution = SafeIntegerField(required=False, allow_null=True)

    class Meta:
        model = Listing
        fields = [
            'id', 'titre', 'description', 'prix', 'caution', 'disponible',
            'ville', 'quartier', 'adresse_complete',
            'surface', 'chambres', 'salles_de_bain', 'etage', 'annee_construction',
            'meuble', 'climatisation', 'chauffage', 'balcon', 'jardin', 'parking', 'piscine',
            'wifi', 'television', 'machine_a_laver', 'cuisine_equipee',
            'images', 'photos', 'bailleur',
            'date_creation', 'date_modification', 'date_disponibilite'
        ]
        read_only_fields = ['bailleur', 'date_creation', 'date_modification']

    def get_photos(self, obj):
        """Retourne les URLs complètes pour le frontend"""
        return [settings.MEDIA_URL + path for path in (obj.images or [])]

    def validate_images(self, images):
        """Vérifie que chaque image est bien un jpeg/png/gif"""
        for img in images:
            img_type = imghdr.what(img.file)
            if img_type not in ALLOWED_IMAGE_TYPES:
                raise ValidationError(
                    f"Type d'image non autorisé: {img_type}. Seuls les types {ALLOWED_IMAGE_TYPES} sont acceptés."
                )
        return images

    def create(self, validated_data):
        images = validated_data.pop('images', [])
        validated_data['disponible'] = True
        listing = Listing.objects.create(**validated_data)

        saved_images = listing.images or []
        for img in images:
            path = default_storage.save(f'listings/{img.name}', img)
            saved_images.append(path)

        listing.images = saved_images
        listing.save()
        return listing

    def update(self, instance, validated_data):
        images = validated_data.pop('images', [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if images:
            saved_images = instance.images or []
            for img in images:
                path = default_storage.save(f'listings/{img.name}', img)
                saved_images.append(path)
            instance.images = saved_images

        instance.save()
        return instance
