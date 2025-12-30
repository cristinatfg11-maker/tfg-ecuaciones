# Nombre de archivo: tfg_backend/api/ecuaciones_core.py
# Versión: FIX_LATEX_FRACTIONS_V4.0

import sympy
import re
from sympy import symbols, Eq, expand, solve
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

# Definimos 'x' como el símbolo
x = symbols('x')

def limpiar_y_crear_ecuacion(equation_str: str):
    """
    Convierte un string LaTeX (ej. "\frac{2x}{3} = 4") en una ecuación SymPy.
    """
    try:
        # --- 1. LIMPIEZA AVANZADA DE LATEX ---
        s = equation_str.strip()
        
        # Eliminar comandos de entorno LaTeX que no sirven para el cálculo
        s = s.replace(r'\[', '').replace(r'\]', '')
        s = s.replace(r'\left', '').replace(r'\right', '')
        
        # TRUCO: Convertir fracciones LaTeX \frac{A}{B} a (A)/(B)
        # Buscamos patrones \frac{...}{...} y los reemplazamos por divisiones
        # Repetimos varias veces por si hay fracciones anidadas simples
        for _ in range(3):
            s = re.sub(r'\\frac\s*\{(.*?)\}\s*\{(.*?)\}', r'(\1)/(\2)', s)

        # Reemplazar corchetes restantes por paréntesis
        s = s.replace('{', '(').replace('}', ')')
        s = s.replace('[', '(').replace(']', ')')
        
        # Eliminar cualquier backslash que haya sobrado (ej. espacios \,)
        s = s.replace('\\', '')

        # --- 2. VALIDACIÓN ---
        if '=' not in s:
            return None
            
        lhs_str, rhs_str = s.split('=', 1)

        # --- 3. PARSEO CON MULTIPLICACIÓN IMPLÍCITA (2x -> 2*x) ---
        transformations = (standard_transformations + (implicit_multiplication_application,))

        # Parsear Lado Izquierdo (LHS) - Intentando limpiar prefijos de texto
        parts = lhs_str.split()
        lhs_expr = None
        
        for i in range(len(parts)):
            candidate = " ".join(parts[i:])
            try:
                lhs_expr = parse_expr(candidate, transformations=transformations, evaluate=False)
                break 
            except Exception:
                continue
        
        if lhs_expr is None:
            return None 

        # Parsear Lado Derecho (RHS)
        rhs_expr = parse_expr(rhs_str, transformations=transformations, evaluate=False)

        return Eq(lhs_expr, rhs_expr, evaluate=False)

    except Exception as e:
        # Solo imprimimos errores graves, ignoramos warnings de parseo simple
        print(f"Advertencia parseando '{equation_str}': {e}")
        return None

def clasificar_ecuacion(eq_obj, eq_str: str) -> dict:
    s = eq_str.lower()
    return {
        "con_parentesis": '(' in s or '[' in s,
        "con_fracciones": 'frac' in s or '/' in s,
        "incognita_una_vez": str(eq_obj.lhs).count('x') + str(eq_obj.rhs).count('x') == 1,
        "incognita_mas_de_una_vez": str(eq_obj.lhs).count('x') + str(eq_obj.rhs).count('x') > 1
    }

def solve_equation_step_by_step(eq_obj):
    pasos = []
    try:
        # PASO 1: Expandir
        lhs_expand = expand(eq_obj.lhs)
        rhs_expand = expand(eq_obj.rhs)
        
        # COMPARACIÓN SEGURA (Como Strings) para evitar error "truth value"
        eq_original_str = str(eq_obj.lhs) + "=" + str(eq_obj.rhs)
        eq_expandida_str = str(lhs_expand) + "=" + str(rhs_expand)

        if eq_original_str != eq_expandida_str:
            pasos.append({
                "paso": 1, 
                "descripcion": "Eliminamos paréntesis y expandimos términos.",
                "ecuacion": f"{sympy.latex(lhs_expand)} = {sympy.latex(rhs_expand)}"
            })

        # PASO 2: Resolver
        solucion = solve(eq_obj, x)
        
        solucion_final = ""
        if not solucion:
            solucion_final = "Sin solución"
            pasos.append({"paso": 2, "descripcion": "La ecuación no tiene solución.", "ecuacion": "\\emptyset"})
        elif len(solucion) == 1:
            val = solucion[0]
            solucion_final = str(val)
            pasos.append({
                "paso": 2, 
                "descripcion": "Solución obtenida.",
                "ecuacion": f"x = {sympy.latex(val)}"
            })
        else:
            solucion_final = "Infinitas soluciones"
            pasos.append({"paso": 2, "descripcion": "Identidad.", "ecuacion": "0 = 0"})

        return pasos, solucion_final

    except Exception as e:
        print(f"Error resolviendo: {e}")
        return [], None