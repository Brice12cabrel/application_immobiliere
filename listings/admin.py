from django.contrib import admin
from .models import Listing, Categorie
from django.utils.html import format_html


# ----------------------------
#  CATEGORIE
# ----------------------------
@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'icone')
    search_fields = ('nom',)
    list_per_page = 20

# ----------------------------
#  LISTING
# ----------------------------
@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = (
        'titre', 'ville', 'prix', 'bailleur', 'disponible', 'date_creation'
    )
    list_filter = ('disponible', 'ville', 'meuble', 'climatisation', 'chauffage')
    search_fields = ('titre', 'description', 'ville', 'quartier', 'adresse_complete')
    ordering = ('-date_creation',)
    list_per_page = 20
    readonly_fields = ('date_creation', 'date_modification', 'date_disponibilite')

    # Affichage des images dans l’admin
    def images_preview(self, obj):
        if obj.images:
            return format_html(''.join([f'<img src="/media/{img}" width="100" style="margin:2px;" />' for img in obj.images]))
        return "-"
    images_preview.short_description = 'Images'

    fieldsets = (
        (None, {
            'fields': ('titre', 'description', 'prix', 'caution', 'disponible', 'bailleur')
        }),
        ('Localisation', {
            'fields': ('ville', 'quartier', 'adresse_complete')
        }),
        ('Caractéristiques', {
            'fields': ('surface', 'chambres', 'salles_de_bain', 'etage', 'annee_construction')
        }),
        ('Confort', {
            'fields': ('meuble', 'climatisation', 'chauffage', 'balcon', 'jardin', 'parking', 'piscine')
        }),
        ('Équipements', {
            'fields': ('wifi', 'television', 'machine_a_laver', 'cuisine_equipee')
        }),
        ('Images', {
            'fields': ('images', 'images_preview')
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_modification', 'date_disponibilite')
        }),
    )
