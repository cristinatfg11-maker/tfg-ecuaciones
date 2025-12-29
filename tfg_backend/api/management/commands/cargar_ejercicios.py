# Nombre de archivo: tfg_backend/api/management/commands/cargar_ejercicios.py
# Versión: FIX_SYMPY_BOOLEAN_CHECK_V2.0

import os
import re
from django.core.management.base import BaseCommand
from django.conf import settings
from api.models import Ejercicio, ModeloEjercicio
from api import ecuaciones_core

class Command(BaseCommand):
    help = 'Carga masiva automática de ejercicios desde carpetas .tex'

    def handle(self, *args, **kwargs):
        self.stdout.write("--- INICIANDO ROBOT DE IMPORTACIÓN ---")
        
        # Ruta base donde están tus modelos
        base_dir = os.path.join(settings.BASE_DIR, 'Modelos')

        if not os.path.exists(base_dir):
            self.stdout.write(self.style.ERROR(f"No encuentro la carpeta Modelos en: {base_dir}"))
            return

        # 1. Crear los Modelos (Categorías) si no existen
        config_modelos = [
            (1, "Modelo 1 (Despeje simple)", {}),
            (2, "Modelo 2 (Agrupación simple)", {}),
            (3, "Modelo 3 (Con paréntesis)", {'con_parentesis': True}),
            (4, "Modelo 4 (Con fracciones)", {'con_fracciones': True}),
            (5, "Modelo 5 (Mixta)", {'con_parentesis': True, 'con_fracciones': True, 'incognita_mas_de_una_vez': True}),
        ]

        mapa_modelos_bd = {} # Para guardar referencia

        for num, nombre, flags in config_modelos:
            mod_obj, created = ModeloEjercicio.objects.get_or_create(
                nombre=nombre,
                defaults=flags
            )
            mapa_modelos_bd[num] = mod_obj
            estado = "CREADO" if created else "YA EXISTIA"
            # self.stdout.write(f"Modelo {num}: {estado}") # Comentado para limpiar log

        # 2. Recorrer carpetas y buscar .tex
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.endswith(".tex"):
                    full_path = os.path.join(root, file)
                    self.procesar_archivo(full_path, file, mapa_modelos_bd)

        self.stdout.write(self.style.SUCCESS(f"--- PROCESO FINALIZADO ---"))

    def procesar_archivo(self, path, filename, mapa_modelos):
        # A. Detectar Modelo
        modelo_num = 1
        if "Modelo 2" in path or "_2_" in filename: modelo_num = 2
        elif "Modelo 3" in path or "_3" in filename: modelo_num = 3
        elif "Modelo 4" in path or "_4_" in filename: modelo_num = 4
        elif "Modelo 5" in path or "_5_" in filename: modelo_num = 5
        
        modelo_obj = mapa_modelos.get(modelo_num)

        # B. Detectar Tipo
        tipo = 'PRUEBA'
        if "_e.tex" in filename.lower() or "entreno" in path.lower():
            tipo = 'ENTRENAMIENTO'

        # C. Leer y Extraer
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            matches = re.findall(r'\\\[(.*?)\\\]', content, re.DOTALL)
            if not matches:
                return 
            
            ecuacion_raw = matches[0].strip()
            ecuacion_limpia = ecuacion_raw.replace('\n', ' ').strip()

            # D. Resolver
            eq_obj = ecuaciones_core.limpiar_y_crear_ecuacion(ecuacion_limpia)
            
            # CORRECCIÓN CRÍTICA: Usar 'is None' en lugar de 'if not ...'
            # SymPy falla si intentas evaluar una ecuación como booleano.
            if eq_obj is None:
                self.stdout.write(self.style.WARNING(f"Saltado {filename}: No se pudo entender la ecuación."))
                return

            pasos, solucion_val = ecuaciones_core.solve_equation_step_by_step(eq_obj)
            solucion_str = str(solucion_val) if solucion_val is not None else "Sin solución"

            # E. Guardar
            obj, created = Ejercicio.objects.update_or_create(
                ecuacion_str=ecuacion_limpia,
                defaults={
                    'modelo': modelo_obj,
                    'tipo': tipo,
                    'solucion': solucion_str,
                    'incognita_una_vez': modelo_num == 1, 
                    'con_parentesis': modelo_obj.con_parentesis,
                    'con_fracciones': modelo_obj.con_fracciones,
                    'incognita_mas_de_una_vez': modelo_obj.incognita_mas_de_una_vez
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"Importado: {filename} ({tipo})"))

        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Error en {filename}: {e}"))