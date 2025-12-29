# Nombre de archivo: api/ecuaciones_core.py
# VERSIÓN FINAL: Genera LaTeX

import re
from sympy import sympify, Eq, symbols, solve, simplify
from sympy import latex # ¡NUEVA IMPORTACIÓN!

# Definimos el símbolo 'x'
x = symbols('x')

def limpiar_y_crear_ecuacion(equation_str: str):
    """
    Limpia el string de la ecuación y la convierte en un objeto Ecuación de SymPy.
    """
    try:
        # 1. Eliminar cualquier etiqueta o prefijo (ej. "3a) ")
        cleaned_str = re.sub(r'^[a-zA-Z0-9]+\)\s*', '', equation_str).strip()
        
        # 2. Asegurarse de que los multiplicadores implícitos sean explícitos (ej. 2(x -> 2*(x)
        cleaned_str = re.sub(r'(\d+)\s*\(', r'\1*(', cleaned_str)
        cleaned_str = re.sub(r'\)\s*\(', r')*(', cleaned_str)
        
        # 3. Separar la ecuación en lado izquierdo y derecho
        if '=' not in cleaned_str:
            return None # No es una ecuación válida
        
        parts = cleaned_str.split('=')
        left_side = sympify(parts[0])
        right_side = sympify(parts[1])
        
        # 4. Crear el objeto Ecuación
        eq = Eq(left_side, right_side)
        return eq
        
    except Exception as e:
        print(f"Error en limpiar_y_crear_ecuacion: {e}")
        return None

def solve_equation_step_by_step(eq: Eq):
    """
    Resuelve una ecuación de primer grado paso a paso y devuelve los pasos y la solución
    en formato LaTeX.
    """
    pasos = []
    
    # --- ¡NUEVA FUNCIÓN INTERNA PARA CONVERTIR A LATEX! ---
    def to_latex(expression):
        # Convierte la expresión a LaTeX y la envuelve en $$
        return f"$${latex(expression)}$$"

    try:
        # Paso 1: Expandir (Eliminar paréntesis)
        eq_expanded = eq.expand()
        
        # Solo añadimos el paso si la ecuación cambió
        if eq_expanded != eq:
            pasos.append({
                'paso': 1,
                'descripcion': 'Eliminamos los paréntesis aplicando la propiedad distributiva.',
                'ecuacion': to_latex(eq_expanded) # ¡Convertido a LaTeX!
            })
        
        # Paso 2: Agrupar términos (x a la izquierda, números a la derecha)
        # SymPy lo hace "lhs - rhs = 0", así que reorganizamos
        expr = eq_expanded.lhs - eq_expanded.rhs
        
        # Separar términos con 'x' de los términos constantes
        terms_with_x = expr.collect(x).coeff(x) * x
        constants = expr.subs(x, 0)
        
        # Crear la nueva ecuación agrupada: terms_with_x = -constants
        eq_grouped = Eq(terms_with_x, -constants)
        
        paso_num = len(pasos) + 1
        pasos.append({
            'paso': paso_num,
            'descripcion': "Agrupamos y operamos todos los términos con 'x' en un lado y los números en el otro.",
            'ecuacion': to_latex(eq_grouped) # ¡Convertido a LaTeX!
        })

        # Paso 3: Aislar x (resolver para x)
        solucion = solve(eq_grouped, x)
        
        # Obtener el coeficiente de x y la constante
        coeficiente = terms_with_x.coeff(x)
        constante = -constants

        paso_num_final = paso_num + 1
        if coeficiente != 1:
            pasos.append({
                'paso': paso_num_final,
                'descripcion': f"Aislamos 'x' pasando el coeficiente ({coeficiente}) a dividir.",
                'ecuacion': to_latex(Eq(x, constante / coeficiente)) # ¡Convertido a LaTeX!
            })
            
        # Paso 4: Solución final simplificada
        solucion_final_expr = constante / coeficiente
        pasos.append({
            'paso': paso_num_final + 1,
            'descripcion': 'Solución final.',
            'ecuacion': to_latex(Eq(x, solucion_final_expr.simplify())) # ¡Convertido a LaTeX!
        })
        
        # La solución es el valor numérico
        solucion_final_valor = solucion_final_expr.simplify()
        
        # Devolvemos los pasos y la solución final (también en LaTeX)
        return pasos, to_latex(Eq(x, solucion_final_valor))
        
    except Exception as e:
        print(f"Error en solve_equation_step_by_step: {e}")
        return [], None