# Nombre de archivo: api/models.py
# Versión: GAMIFICACION_FLOW_V3.0

from django.db import models
from django.contrib.auth.models import User

# --- MODELOS EXISTENTES ---
class ModeloEjercicio(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    
    incognita_una_vez = models.BooleanField(default=False)
    incognita_mas_de_una_vez = models.BooleanField(default=False)
    con_parentesis = models.BooleanField(default=False)
    con_fracciones = models.BooleanField(default=False)

    def __str__(self):
        return self.nombre

class Ejercicio(models.Model):
    TIPO_EJERCICIO = [
        ('ENTRENAMIENTO', 'Entrenamiento'),
        ('PRUEBA', 'Prueba'),
    ]
    modelo = models.ForeignKey(ModeloEjercicio, on_delete=models.CASCADE, related_name='ejercicios')
    tipo = models.CharField(max_length=20, choices=TIPO_EJERCICIO, default='ENTRENAMIENTO')
    ecuacion_str = models.CharField(max_length=255)
    solucion = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.modelo.nombre} ({self.tipo}) - {self.ecuacion_str}"

class PasoResolucion(models.Model):
    ejercicio = models.ForeignKey(Ejercicio, on_delete=models.CASCADE, related_name='pasos')
    numero_paso = models.PositiveIntegerField()
    descripcion = models.CharField(max_length=255)
    ecuacion_resultante = models.CharField(max_length=255)

    class Meta:
        ordering = ['numero_paso']

    def __str__(self):
        return f"Paso {self.numero_paso} para {self.ejercicio.ecuacion_str}"

# --- MODELO DE PROGRESO ACTUALIZADO ---
class ProgresoUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    puntos_totales = models.IntegerField(default=0)
    
    # Campo nuevo para evitar repeticiones
    ejercicios_completados = models.ManyToManyField(Ejercicio, blank=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.puntos_totales} pts"