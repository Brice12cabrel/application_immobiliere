# auth_project/urls.py — VERSION FINALE PARFAITE
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('auth_api.urls')),
    path('api/', include('listings.urls')),
]

# Servir les fichiers médias (CNI, titre foncier, etc.) en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)