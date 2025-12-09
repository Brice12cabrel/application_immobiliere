# listings/models.py — VERSION ULTIME PROFESSIONNELLE (2025)
from django.db import models
from auth_api.models import User

class Categorie(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    icone = models.CharField(max_length=50, blank=True)  # ex: "home", "building"
    
    def __str__(self):
        return self.nom

class Listing(models.Model):
    # Propriétaire
    bailleur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mes_annonces')

    # Infos principales
    titre = models.CharField(max_length=200)
    description = models.TextField()

    # Prix & disponibilité
    prix = models.PositiveIntegerField(help_text="Prix par mois en FCFA")
    caution = models.PositiveIntegerField(default=0, help_text="Caution (optionnel)")
    disponible = models.BooleanField(default=True)

    # Localisation
    ville = models.CharField(max_length=100)
    quartier = models.CharField(max_length=100, blank=True)
    adresse_complete = models.CharField(max_length=300, blank=True)  # Visible seulement aux abonnés

    # Caractéristiques
    surface = models.PositiveSmallIntegerField(null=True, blank=True, help_text="En m²")
    chambres = models.PositiveSmallIntegerField(null=True, blank=True)
    salles_de_bain = models.PositiveSmallIntegerField(default=1)
    etage = models.PositiveSmallIntegerField(null=True, blank=True)
    annee_construction = models.PositiveSmallIntegerField(null=True, blank=True)

    # Confort
    meuble = models.BooleanField(default=False)
    climatisation = models.BooleanField(default=False)
    chauffage = models.BooleanField(default=False)
    balcon = models.BooleanField(default=False)
    jardin = models.BooleanField(default=False)
    parking = models.BooleanField(default=False)
    piscine = models.BooleanField(default=False)

    # Équipements
    wifi = models.BooleanField(default=False)
    television = models.BooleanField(default=False)
    machine_a_laver = models.BooleanField(default=False)
    cuisine_equipee = models.BooleanField(default=False)

    # Photos
    images = models.JSONField(default=list)  # ["media/listings/..."]

    # Catégories
    categories = models.ManyToManyField(Categorie, blank=True)

    # Dates
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    date_disponibilite = models.DateField(null=True, blank=True)

    # Stats (futur)
    vues = models.PositiveIntegerField(default=0)
    favoris = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-date_creation']
        verbose_name = "Annonce"
        verbose_name_plural = "Annonces"

    def __str__(self):
        return f"{self.titre} - {self.ville} ({self.prix} FCFA)"