# Nombre de archivo: tfg_backend/urls.py (El PRINCIPAL)

from django.contrib import admin
from django.urls import path, include  # <-- ¡Debe tener 'include'!

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Esta línea le dice a Django que busque en 'api.urls'
    path('api/', include('api.urls')), 
]