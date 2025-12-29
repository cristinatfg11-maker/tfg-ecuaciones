# Nombre de archivo: api/urls.py
# Versión: UPDATE_RANKING_ENDPOINT_V4.0

from django.urls import path
from . import views

urlpatterns = [
    # --- AUTENTICACIÓN ---
    path('registro/', views.registro_usuario_view, name='registro'),
    path('login/', views.login_usuario_view, name='login'),
    path('cambiar-password/', views.cambiar_password_view, name='cambiar_password'),
    path('actualizar-puntos/', views.actualizar_puntos_view, name='actualizar_puntos'),

    # --- NUEVOS ENDPOINTS GAMIFICACIÓN ---
    path('ejercicio-aleatorio/', views.obtener_ejercicio_aleatorio_view, name='ejercicio_aleatorio'),
    path('marcar-completado/', views.marcar_ejercicio_completado_view, name='marcar_completado'),
    
    # ACTUALIZACIÓN 3a: Ruta para el Ranking
    path('ranking/', views.ranking_usuarios_view, name='ranking'),

    # --- LÓGICA CORE ---
    path('resolver/', views.resolver_ecuacion_view, name='resolver_ecuacion'),
    # Mantenemos estos por compatibilidad
    path('clasificar/', views.clasificar_modelo_view, name='clasificar_modelo'),
    path('lista-modelos/', views.lista_modelos_view, name='lista_modelos'),
    path('ejercicios-por-modelo/<int:modelo_id>/', views.get_ejercicios_por_modelo_view, name='get_ejercicios_por_modelo'),
]