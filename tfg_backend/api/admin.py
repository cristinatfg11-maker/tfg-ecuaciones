# Nombre de archivo: api/admin.py
# Versión: GAMIFICACION_FLOW_V3.0

from django.contrib import admin
from django.urls import path
from django.template.response import TemplateResponse
from .models import ModeloEjercicio, Ejercicio, PasoResolucion, ProgresoUsuario

class PasoResolucionInline(admin.TabularInline):
    model = PasoResolucion
    extra = 1

@admin.register(Ejercicio)
class EjercicioAdmin(admin.ModelAdmin):
    list_display = ('ecuacion_str', 'modelo', 'tipo', 'solucion')
    list_filter = ('modelo', 'tipo')
    inlines = [PasoResolucionInline]
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'importar-latex/',
                self.admin_site.admin_view(self.importar_latex_view),
                name='importar-latex',
            ),
        ]
        return custom_urls + urls

    def importar_latex_view(self, request):
        log = []
        if request.method == 'POST':
            from .latex_parser import importar_modelos
            log = importar_modelos()
            self.message_user(request, "Importación completada.")
        
        context = {
            **self.admin_site.each_context(request),
            'title': 'Importar Ejercicios desde LaTeX',
            'log': log,
        }
        return TemplateResponse(request, "admin/importar_latex.html", context)

@admin.register(ModeloEjercicio)
class ModeloEjercicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'incognita_una_vez', 'incognita_mas_de_una_vez', 'con_parentesis', 'con_fracciones')
    list_editable = ('incognita_una_vez', 'incognita_mas_de_una_vez', 'con_parentesis', 'con_fracciones')

@admin.register(ProgresoUsuario)
class ProgresoUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'puntos_totales')
    filter_horizontal = ('ejercicios_completados',) # Para ver la lista de completados mejor