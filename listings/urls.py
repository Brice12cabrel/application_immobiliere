# listings/urls.py — VERSION FINALE ULTIME (2025 PRO)
from django.urls import path
from .views import (
    ListingListCreateView,
    ListingDetailView,
  #  ListingUpdateDestroyView,   # Modification + suppression
)

urlpatterns = [
    # Liste + Création
    path('listings/', ListingListCreateView.as_view(), name='listing-list-create'),

    # Détail
    path('listings/<int:pk>/', ListingDetailView.as_view(), name='listing-detail'),

    # Modification + Suppression (même URL, méthode PATCH/DELETE)
  #  path('listings/<int:pk>/edit/', ListingUpdateDestroyView.as_view(), name='listing-edit-delete'),
]