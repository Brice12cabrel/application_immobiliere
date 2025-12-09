from rest_framework import generics, permissions
from .models import Listing
from .serializers import ListingSerializer


class ListingListCreateView(generics.ListCreateAPIView):
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = Listing.objects.all()

        # Filtrer uniquement les annonces disponibles
        qs = qs.filter(disponible=True)

        # Si ?mine=true → retourner seulement mes annonces
        if self.request.GET.get("mine"):
            return qs.filter(bailleur=self.request.user)

        return qs

    def perform_create(self, serializer):
        serializer.save(bailleur=self.request.user)


class ListingDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Listing.objects.all()

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        # Version correcte : DRF appelle instance.delete()
        instance.delete()
