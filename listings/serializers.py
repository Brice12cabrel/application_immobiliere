# listings/serializers.py — VERSION FINALE ULTIME (100% PROPRE & FONCTIONNELLE)
from rest_framework import serializers
from .models import Listing, Categorie
from django.core.files.storage import default_storage


class CategorieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorie
        fields = ['id', 'nom']


class ListingListSerializer(serializers.ModelSerializer):
    """Serializer for listing list view (public)"""
    categories = CategorieSerializer(many=True)
    bailleur_nom = serializers.CharField(source='bailleur.first_name', read_only=True)
    photo_principale = serializers.SerializerMethodField()
    surface = serializers.IntegerField(required=False, allow_null=True)
    chambres = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Listing
        fields = [
            'id', 'titre', 'prix', 'ville', 'quartier', 'surface', 'chambres',
            'meuble', 'photo_principale', 'categories', 'disponible', 'bailleur_nom',
            'date_creation'
        ]

    def get_photo_principale(self, obj):
        if obj.images and len(obj.images) > 0:
            first_image = obj.images[0]
            if first_image.startswith('http'):
                return first_image
            return f"http://127.0.0.1:8000/{first_image}"
        return None

    def to_representation(self, instance):
        if instance.surface == '':
            instance.surface = None
        if instance.chambres == '':
            instance.chambres = None
        return super().to_representation(instance)


class ListingDetailSerializer(serializers.ModelSerializer):
    """Serializer for listing detail view (authenticated users see full info)"""
    categories = CategorieSerializer(many=True)
    bailleur = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = [
            'id', 'titre', 'description', 'prix',
            'ville', 'quartier', 'adresse_complete',
            'surface', 'chambres', 'meuble',
            'images', 'categories', 'disponible',
            'date_creation', 'date_modification',
            'bailleur'
        ]

    def get_images(self, obj):
        if obj.images:
            return [f"http://127.0.0.1:8000/{img}" if not img.startswith('http') else img for img in obj.images]
        return []

    def get_bailleur(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return {
                "nom": obj.bailleur.first_name or "Anonyme",
                "telephone": getattr(obj.bailleur, 'phone_number', 'N/A'),
                "email": obj.bailleur.email
            }
        return {"nom": "Anonyme", "telephone": None, "email": None}

    def to_representation(self, instance):
        if instance.surface == '':
            instance.surface = None
        if instance.chambres == '':
            instance.chambres = None
        return super().to_representation(instance)


class ListingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating listings with image uploads"""
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
        max_length=10
    )
    categories = serializers.PrimaryKeyRelatedField(
        queryset=Categorie.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = Listing
        fields = [
            'titre', 'description', 'prix',
            'ville', 'quartier', 'adresse_complete',
            'surface', 'chambres', 'meuble',
            'images', 'categories'
        ]

    def create(self, validated_data):
        images = validated_data.pop('images', [])
        categories = validated_data.pop('categories', [])

        listing = Listing.objects.create(**validated_data)

        # SAVE actual image files to media/listings/
        image_urls = []
        for img in images:
            path = default_storage.save(f'listings/{img.name}', img)
            image_urls.append(path)

        listing.images = image_urls

        if categories:
            listing.categories.set(categories)

        listing.save()
        return listing