# auth_api/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('locataire', 'Locataire'),
        ('bailleur_pending', 'Bailleur (en attente)'),
        ('bailleur', 'Bailleur'),
        ('admin', 'Admin'),
    )

    email = models.EmailField(unique=True, db_index=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    photo_profil = models.URLField(blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='locataire')
    is_verified = models.BooleanField(default=False)

    # Champs pour devenir bailleur
    cni_document = models.URLField(blank=True, null=True)
    titre_foncier = models.URLField(blank=True, null=True)
    adresse = models.CharField(max_length=255, blank=True, null=True)
    ville = models.CharField(max_length=100, blank=True, null=True)
    bailleur_request_date = models.DateTimeField(null=True, blank=True)
    
    # DOCUMENTS RÉELS (pas juste des URLs)
    cni_document = models.FileField(upload_to='documents/cni/', blank=True, null=True)
    titre_foncier = models.FileField(upload_to='documents/titre/', blank=True, null=True)


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']