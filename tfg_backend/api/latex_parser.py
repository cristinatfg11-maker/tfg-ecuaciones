# Nombre de archivo: api/latex_parser.py
# VERSIÓN 10: Parser final (Soporta "La solución es...")
import os
import re
from pathlib import Path
from django.db import transaction
from .models import ModeloEjercicio, Ejercicio, PasoResolucion

BASE_DIR = Path(__file__).resolve().parent.parent
MODELOS_DIR = BASE_DIR / "Modelos"

def normalizar_contenido(content):
    content = re.sub(r"{\[", r"\[", content, flags=re.DOTALL)
    content = re.sub(r"\]}", r"\]", content, flags=re.DOTALL)
    content = re.sub(r"{]", r"\]", content, flags=re.DOTALL) 
    content = re.sub(r"\\\((.*?)\\\)", r"\[ \1 \]", content, flags=re.DOTALL)
    content = re.sub(r"\\begin\{(?:equation|align|align\*|equation\*|aligned)\}(.*?)\\end\{(?:equation|align|align\*|equation\*|aligned)\}", 
                     r"\[ \1 \]", content, flags=re.DOTALL)
    return content

REGEX_EQ_BLOCK = re.compile(r"\\\[(.*?)\\\]", re.DOTALL)

REGEX_PASO_DESC = re.compile(
    r"\\(?:subsection|textbf|section)\*?\{?\s*Paso (\d+)[^}]*\}?\s*(.*?)\s*(?=\\\[|\\subsection|\\textbf|\\section|\\end\{document\})",
    re.DOTALL | re.IGNORECASE
)

# EXPRESIÓN MEJORADA PARA SOLUCIONES
REGEX_SOLUCION = re.compile(
    r"\\boxed\{(.*?)\}"                
    r"|(infinitas soluciones)"         
    r"|(no tiene solución)"           
    r"|(?:\\textbf\{Solución: \s*\}\s*|Solución:)\s*\[\s*(.*?)\s*\]"
    r"|(?:\\text\{La solución es[:\s]*\}\s*)(.*?)(?=\s*[\}\]])", # <-- NUEVO: Para ejercicio 1.10
    re.DOTALL | re.IGNORECASE
)

def parsear_archivo_tex(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error leyendo {file_path}: {e}")
        return None

    content = normalizar_contenido(content)
    
    ecuaciones = REGEX_EQ_BLOCK.findall(content)
    if not ecuaciones:
        ecuaciones_fallback = re.findall(r"\$\$(.*?)\$\$", content, re.DOTALL)
        if not ecuaciones_fallback:
             return None 
        ecuaciones = ecuaciones_fallback

    ecuacion_principal_str = ""
    for eq in ecuaciones:
        if "Resolución" not in eq and "Prueba" not in eq:
            ecuacion_principal_str = f"$${eq.strip()}$$"
            break
    
    if not ecuacion_principal_str:
         if not ecuaciones: return None
         ecuacion_principal_str = f"$${ecuaciones[0].strip()}$$"


    solucion_match = REGEX_SOLUCION.search(content)
    solucion_final = ""

    if solucion_match:
        # Extraemos los grupos en orden
        g = solucion_match.groups()
        boxed = g[0]
        infinitas = g[1]
        no_sol = g[2]
        textbf = g[3]
        text_la_sol = g[4] # El nuevo grupo

        if boxed:
            solucion_final = f"$${boxed.strip()}$$"
        elif infinitas:
            solucion_final = "Infinitas soluciones"
        elif no_sol:
            solucion_final = "No tiene solución"
        elif textbf:
            solucion_final = f"$${textbf.strip()}$$"
        elif text_la_sol:
            # Si capturamos texto plano como "m = 0", lo envolvemos en $$
            solucion_final = f"$${text_la_sol.strip()}$$"
    
    if not solucion_final:
        solucion_final = f"$${ecuaciones[-1].strip()}$$"

    pasos_desc = REGEX_PASO_DESC.findall(content)
    pasos_data = []

    for i, (num_paso, desc) in enumerate(pasos_desc):
        if (i + 1) < len(ecuaciones):
            ecuacion_del_paso = f"$${ecuaciones[i+1].strip()}$$"
            pasos_data.append({
                'numero': int(num_paso),
                'descripcion': desc.strip().replace('\n', ' '),
                'ecuacion': ecuacion_del_paso
            })

    if not pasos_data:
        pasos_desc_fallback = re.findall(r"\\(?:subsection|textbf|section)\*?\{.*?\}(.*?)(?=\\\[|\\subsection|\\textbf|\\section|\\end\{document\})", content, re.DOTALL | re.IGNORECASE)
        for i, desc in enumerate(pasos_desc_fallback):
             if (i + 1) < len(ecuaciones):
                ecuacion_del_paso = f"$${ecuaciones[i+1].strip()}$$"
                pasos_data.append({
                    'numero': i + 1,
                    'descripcion': desc.strip().replace('\n', ' '),
                    'ecuacion': ecuacion_del_paso
                })

    return {
        'ecuacion_str': ecuacion_principal_str,
        'solucion': solucion_final,
        'pasos': pasos_data
    }

@transaction.atomic
def importar_modelos():
    log = []
    if not os.path.exists(MODELOS_DIR):
        log.append(f"ERROR: No se encontró la carpeta 'Modelos' en {MODELOS_DIR}")
        return log
    
    try:
        ejercicios_viejos = Ejercicio.objects.filter(ecuacion_str__startswith='$$')
        count = ejercicios_viejos.count()
        if count > 0:
            ejercicios_viejos.delete()
            log.append(f"--- Se eliminaron {count} ejercicios antiguos para recargar ---")
    except Exception as e:
        log.append(f"ERROR: No se pudieron eliminar los ejercicios antiguos. {e}")

    for modelo_dir in os.listdir(MODELOS_DIR):
        modelo_path = os.path.join(MODELOS_DIR, modelo_dir)
        if not os.path.isdir(modelo_path): continue
            
        modelo_obj = ModeloEjercicio.objects.filter(nombre__icontains=modelo_dir).first()
        if not modelo_obj:
            log.append(f"AVISO: No se encontró el Modelo '{modelo_dir}' en la BD. Saltando...")
            continue
        
        log.append(f"--- Importando para {modelo_obj.nombre} ---")

        for subdir in os.listdir(modelo_path):
            subdir_path = os.path.join(modelo_path, subdir)
            if not os.path.isdir(subdir_path): continue
            
            for tipo_dir in os.listdir(subdir_path):
                tipo_path = os.path.join(subdir_path, tipo_dir)
                if not os.path.isdir(tipo_path): continue

                if "entreno" in tipo_dir.lower():
                    tipo_ejercicio = "ENTRENAMIENTO"
                elif "prueba" in tipo_dir.lower():
                    tipo_ejercicio = "PRUEBA"
                else:
                    continue 
                
                log.append(f"  > Cargando {tipo_ejercicio} desde '{tipo_dir}'...")

                for tex_file in os.listdir(tipo_path):
                    if not tex_file.endswith(".tex"):
                        continue
                    
                    file_path = os.path.join(tipo_path, tex_file)
                    datos_ejercicio = parsear_archivo_tex(file_path)
                    
                    if not datos_ejercicio:
                        log.append(f"    ERROR: No se pudo parsear {tex_file}")
                        continue
                    
                    try:
                        ejercicio_obj = Ejercicio.objects.create(
                            ecuacion_str=datos_ejercicio['ecuacion_str'],
                            modelo=modelo_obj,
                            tipo=tipo_ejercicio,
                            solucion=datos_ejercicio['solucion']
                        )
                        log.append(f"    + CREADO: {tex_file}")

                        for paso in datos_ejercicio['pasos']:
                            PasoResolucion.objects.create(
                                ejercicio=ejercicio_obj,
                                numero_paso=paso['numero'],
                                descripcion=paso['descripcion'],
                                ecuacion_resultante=paso['ecuacion']
                            )
                    except Exception as e:
                        log.append(f"    ERROR al crear {tex_file}: {e}")
                        
    log.append("--- Proceso de importación finalizado. ---")
    return log