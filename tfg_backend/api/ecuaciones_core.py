# Nombre de archivo: tfg_backend/api/ecuaciones_core.py
# Versión: FIX_IMPLICIT_MULT_V2.0

import sympy
from sympy import symbols, Eq, expand, solve
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

# Definimos 'x' como el símbolo
x = symbols('x')

def limpiar_y_crear_ecuacion(equation_str: str):
    """
    Convierte un string (ej. "2x + 4 = 10") en una ecuación SymPy.
    Maneja multiplicación implícita (2x -> 2*x).
    """
    try:
        # 0. Limpieza básica de LaTeX
        clean_str = equation_str.replace(r'\[', '').replace(r'\]', '') # Quitar bloques latex
        clean_str = clean_str.replace('{', '(').replace('}', ')') # Corchetes latex a parentesis
        clean_str = clean_str.replace('[', '(').replace(']', ')') # Corchetes normales a parentesis
        
        # 1. Validar que tenga '='
        if '=' not in clean_str:
            return None
            
        lhs_str, rhs_str = clean_str.split('=', 1)

        # 2. Configurar transformaciones para entender "2x" como "2*x"
        transformations = (standard_transformations + (implicit_multiplication_application,))

        # 3. Parsear Lado Izquierdo (LHS)
        # Intentamos limpiar prefijos tipo "3a)" iterativamente
        parts = lhs_str.split()
        lhs_expr = None
        
        # Probamos desde la frase completa e ir quitando la primera palabra si falla
        for i in range(len(parts)):
            candidate = " ".join(parts[i:])
            try:
                lhs_expr = parse_expr(candidate, transformations=transformations, evaluate=False)
                break # Si funciona, nos quedamos con este
            except Exception:
                continue
        
        if lhs_expr is None:
            return None # No se pudo entender el lado izquierdo

        # 4. Parsear Lado Derecho (RHS)
        rhs_expr = parse_expr(rhs_str, transformations=transformations, evaluate=False)

        # 5. Retornar ecuación
        return Eq(lhs_expr, rhs_expr, evaluate=False)

    except Exception as e:
        print(f"Error en limpiar_y_crear_ecuacion: {e}")
        return None

def clasificar_ecuacion(eq_obj, eq_str: str) -> dict:
    """Clasifica la ecuación para el frontend."""
    # Convertimos a string para buscar caracteres visuales
    s = eq_str.lower()
    return {
        "con_parentesis": '(' in s or '[' in s,
        "con_fracciones": 'frac' in s or '/' in s,
        # Nota: Esto es una heurística simple
        "incognita_una_vez": str(eq_obj.lhs).count('x') + str(eq_obj.rhs).count('x') == 1,
        "incognita_mas_de_una_vez": str(eq_obj.lhs).count('x') + str(eq_obj.rhs).count('x') > 1
    }

def solve_equation_step_by_step(eq_obj):
    """Resuelve la ecuación y devuelve pasos + solución final."""
    pasos = []
    try:
        # PASO 1: Expandir (quitar paréntesis)
        lhs_expand = expand(eq_obj.lhs)
        rhs_expand = expand(eq_obj.rhs)
        eq_expandida = Eq(lhs_expand, rhs_expand)

        if eq_expandida != eq_obj:
            pasos.append({
                "paso": 1, 
                "descripcion": "Eliminamos paréntesis y expandimos términos.",
                "ecuacion": f"{sympy.latex(lhs_expand)} = {sympy.latex(rhs_expand)}"
            })

        # PASO 2: Resolver
        solucion = solve(eq_obj, x)
        
        # Interpretación de la solución
        solucion_final = ""
        if not solucion:
            solucion_final = "Sin solución"
            pasos.append({"paso": 2, "descripcion": "La ecuación no tiene solución.", "ecuacion": "0 = 1"})
        elif len(solucion) == 1:
            val = solucion[0]
            solucion_final = str(val) # Convertir a string simple para la BD
            # Generamos paso final LaTeX
            pasos.append({
                "paso": 2, 
                "descripcion": "Agrupamos y despejamos la incógnita.",
                "ecuacion": f"x = {sympy.latex(val)}"
            })
        else:
            solucion_final = "Infinitas soluciones"
            pasos.append({"paso": 2, "descripcion": "Cualquier valor es válido.", "ecuacion": "0 = 0"})

        return pasos, solucion_final

    except Exception as e:
        print(f"Error resolviendo: {e}")
        return [], None