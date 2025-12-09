# listings/views.py — VERSION ULTIME PROFESSIONNELLE (2025)
from rest_framework import generics, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Listing
from .serializers import (
    ListingListSerializer,
    ListingDetailSerializer,
    ListingCreateSerializer
)

# Permission : seul le propriétaire peut modifier/supprimer
class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.bailleur == request.user


# LISTE + CRÉATION
class ListingListCreateView(generics.ListCreateAPIView):
    queryset = Listing.objects.filter(disponible=True)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ListingCreateSerializer
        return ListingListSerializer

    def perform_create(self, serializer):
        # L'utilisateur connecté devient automatiquement le bailleur
        serializer.save(bailleur=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()

        # Filtres avancés
        ville = self.request.query_params.get('ville')
        prix_min = self.request.query_params.get('prix_min')
        prix_max = self.request.query_params.get('prix_max')
        chambres = self.request.query_params.get('chambres')
        meuble = self.request.query_params.get('meuble')
        search = self.request.query_params.get('search')

        if ville:
            qs = qs.filter(ville__icontains=ville)
        if prix_min:
            qs = qs.filter(prix__gte=prix_min)
        if prix_max:
            qs = qs.filter(prix__lte=prix_max)
        if chambres:
            qs = qs.filter(chambres=chambres)
        if meuble in ('true', '1'):
            qs = qs.filter(meuble=True)
        if search:
            qs = qs.filter(titre__icontains=search) | qs.filter(description__icontains=search)

        return qs.distinct().order_by('-date_creation')


# DÉTAIL + MODIFICATION + SUPPRESSION
class ListingDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Listing.objects.filter(disponible=True)
    permission_classes = [IsOwnerOrReadOnly]

    def get_serializer_class(self):
        # Si non connecté → version publique (moins d'infos)
        if not self.request.user.is_authenticated:
            return ListingListSerializer
        return ListingDetailSerializer

    def perform_update(self, serializer):
        # Gestion des nouvelles images
        images = self.request.FILES.getlist('images')
        if images:
            image_urls = [f"media/listings/{img.name}" for img in images]
            serializer.save(images=image_urls)
        else:
            serializer.save()

    def perform_destroy(self, instance):
        # Suppression douce (recommandée pour garder l'historique)
        instance.disponible = False
        instance.save()
        # Pour suppression totale : instance.delete()