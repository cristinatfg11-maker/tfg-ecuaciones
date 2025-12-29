# Nombre de archivo: tfg_backend/api/ecuaciones_core.py
# Versión: FIX_RELATIONAL_ERROR_V3.0

import sympy
from sympy import symbols, Eq, expand, solve
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

# Definimos 'x' como el símbolo
x = symbols('x')

def limpiar_y_crear_ecuacion(equation_str: str):
    """
    Convierte un string (ej. "2x + 4 = 10") en una ecuación SymPy.
    """
    try:
        # 0. Limpieza básica de LaTeX y espacios
        clean_str = equation_str.replace(r'\[', '').replace(r'\]', '')
        clean_str = clean_str.replace('{', '(').replace('}', ')')
        clean_str = clean_str.replace('[', '(').replace(']', ')')
        clean_str = clean_str.strip()
        
        # 1. Validar que tenga '='
        if '=' not in clean_str:
            return None
            
        lhs_str, rhs_str = clean_str.split('=', 1)

        # 2. Configurar transformaciones (2x -> 2*x)
        transformations = (standard_transformations + (implicit_multiplication_application,))

        # 3. Parsear Lado Izquierdo (LHS)
        parts = lhs_str.split()
        lhs_expr = None
        
        # Intentar parsear quitando palabras del principio si falla
        for i in range(len(parts)):
            candidate = " ".join(parts[i:])
            try:
                lhs_expr = parse_expr(candidate, transformations=transformations, evaluate=False)
                break 
            except Exception:
                continue
        
        if lhs_expr is None:
            return None 

        # 4. Parsear Lado Derecho (RHS)
        rhs_expr = parse_expr(rhs_str, transformations=transformations, evaluate=False)

        # 5. Retornar ecuación
        return Eq(lhs_expr, rhs_expr, evaluate=False)

    except Exception as e:
        print(f"Error parseando '{equation_str}': {e}")
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
        
        # CORRECCION CRITICA: Comparamos como STRING para evitar error booleano
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