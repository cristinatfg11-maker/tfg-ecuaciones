# Nombre de archivo: ecuaciones_core.py
#
# VERSIÓN 7 (Corregida): 05-Nov-2025
# - Reescribe 'limpiar_y_crear_ecuacion' para que sea robusta.
# - Ya no corta la ecuación por la mitad.
# - Ahora resuelve la Prueba 2 correctamente (x=2).
#
import sympy
from sympy import symbols, Eq, expand, simplify, solve, sympify

# Definimos 'x' como el símbolo que usaremos en nuestras ecuaciones
x = symbols('x')

def limpiar_y_crear_ecuacion(equation_str: str) -> Eq:
    """
    Toma un string de ecuación, lo limpia de texto introductorio 
    (ej. "3a)" o "3 pruder") y lo convierte en un objeto Ecuación.
    
    REGLA: Requiere multiplicación explícita (ej. '2*(x-3)')
    """
    
    # --- INICIO DE LA CORRECCIÓN DE LÓGICA ---
    
    # 1. Dividir por el '=' que es el único separador fiable
    if '=' not in equation_str:
        print("Error: La ecuación no tiene un '='.")
        return None
    
    lhs_full_str, rhs_full_str = equation_str.split('=', 1)

    # 2. Parsear el lado derecho (suele estar limpio)
    try:
        rhs_expr = sympify(rhs_full_str, evaluate=False)
    except Exception as e:
        print(f"Error al parsear el lado derecho (RHS): {e}")
        return None

    # 3. Parsear el lado izquierdo (puede tener prefijos)
    try:
        # Intento 1: Asumir que está limpio
        lhs_expr = sympify(lhs_full_str, evaluate=False)
        return Eq(lhs_expr, rhs_expr, evaluate=False)
    except Exception:
        # Intento 2: Falló, hay un prefijo. Empezar a quitar palabras.
        lhs_words = lhs_full_str.split()
        for i in range(1, len(lhs_words)):
            # Quita la primera palabra, luego la segunda, etc.
            test_str = " ".join(lhs_words[i:])
            try:
                lhs_expr = sympify(test_str, evaluate=False)
                # Éxito: Encontramos la parte matemática
                return Eq(lhs_expr, rhs_expr, evaluate=False)
            except Exception:
                # Sigue sin ser matemático, continuar quitando
                continue
    
    # Si llegamos aquí, no se pudo parsear
    print(f"Error: No se pudo limpiar ni parsear el lado izquierdo (LHS): {lhs_full_str}")
    return None
    # --- FIN DE LA CORRECCIÓN DE LÓGICA ---


def clasificar_ecuacion(eq_obj: Eq, eq_str: str) -> dict:
    """
    Clasifica la ecuación según las preguntas del esquema.
    """
    caracteristicas = {
        "con_parentesis": '(' in eq_str or ')' in eq_str,
        "con_fracciones": '/' in eq_str,
        "incognita_una_vez": str(eq_obj.lhs).count('x') + str(eq_obj.rhs).count('x') == 1
    }
    
    # Lógica del árbol de decisión
    if caracteristicas["incognita_una_vez"]:
        modelo = "Modelo 1 (Despeje simple)"
    elif not caracteristicas["con_parentesis"] and not caracteristicas["con_fracciones"]:
        modelo = "Modelo 2 (Agrupación simple)"
    elif caracteristicas["con_parentesis"] and not caracteristicas["con_fracciones"]:
        modelo = "Modelo 3 (Con paréntesis)"
    elif not caracteristicas["con_parentesis"] and caracteristicas["con_fracciones"]:
        modelo = "Modelo 4 (Con fracciones)"
    else:
        modelo = "Modelo 5 (Mixta)"
        
    caracteristicas["modelo_sugerido"] = modelo
    return caracteristicas

def solve_equation_step_by_step(eq_obj: Eq) -> (dict, float):
    """
    Resuelve una ecuación de primer grado paso a paso.
    """
    pasos = []
    
    try:
        # --- PASO 1: Eliminar paréntesis (Expandir) ---
        eq_expandida = Eq(expand(eq_obj.lhs), expand(eq_obj.rhs))
        
        if eq_expandida != eq_obj:
            pasos.append({
                "paso": 1,
                "descripcion": "Eliminamos los paréntesis aplicando la propiedad distributiva.",
                "ecuacion": str(eq_expandida)
            })
        else:
            pasos.append({
                "paso": 1,
                "descripcion": "No hay paréntesis para eliminar.",
                "ecuacion": str(eq_expandida)
            })

        # --- PASO 2: Agrupar y operar términos ---
        L = eq_expandida.lhs
        R = eq_expandida.rhs
        
        const_lhs = L.subs(x, 0)
        const_rhs = R.subs(x, 0)
        
        x_terms_lhs = L - const_lhs
        x_terms_rhs = R - const_rhs
        
        eq_agrupada = Eq(x_terms_lhs - x_terms_rhs, const_rhs - const_lhs)

        pasos.append({
            "paso": 2,
            "descripcion": "Agrupamos y operamos todos los términos con 'x' en un lado y los números en el otro.",
            "ecuacion": str(eq_agrupada)
        })
        
        eq_simplificada = eq_agrupada 

        # --- PASO 3: Aislar la incógnita (Resolver) ---
        solucion = solve(eq_simplificada, x)
        
        if not solucion:
            pasos.append({
                "paso": 3,
                "descripcion": "La ecuación no tiene solución (es una inconsistencia).",
                "ecuacion": str(eq_simplificada)
            })
            solucion_final = None
        elif len(solucion) == 1:
            solucion_final = solucion[0]
            
            lhs_simplificado = eq_simplificada.lhs
            rhs_simplificado = eq_simplificada.rhs
            coeficiente_x = lhs_simplificado.coeff(x)

            if coeficiente_x != 1:
                pasos.append({
                    "paso": 3,
                    "descripcion": f"Aislamos 'x' pasando el coeficiente ({coeficiente_x}) a dividir.",
                    "ecuacion": f"x = {rhs_simplificado} / {coeficiente_x}"
                })
                pasos.append({
                    "paso": 4,
                    "descripcion": "Solución final.",
                    "ecuacion": f"x = {solucion_final}"
                })
            else:
                 pasos.append({
                    "paso": 3,
                    "descripcion": "Solución final.",
                    "ecuacion": f"x = {solucion_final}"
                })
        else:
             pasos.append({
                "paso": 3,
                "descripcion": "La ecuación es una identidad (infinitas soluciones).",
                "ecuacion": str(eq_simplificada)
            })
             solucion_final = "Infinitas soluciones"

        return pasos, solucion_final

    except Exception as e:
        print(f"Error durante la resolución: {e}")
        return [{"paso": 0, "descripcion": f"Error: {e}", "ecuacion": ""}], None

# --- Placeholders para Funciones de IA y Analítica ---

def track_to_lrs(student_id, exercise_id, paso, exito, tiempo_ms, respuesta_usuario):
    print(f"[LRS_TRACKER]: Estudiante {student_id} en Ejercicio {exercise_id}, "
          f"Paso {paso}, Éxito: {exito}, Tiempo: {tiempo_ms}ms.")
    pass

def update_bkt_model(student_id, skill, es_correcto):
    print(f"[BKT_MODEL]: Actualizando conocimiento de {student_id} "
          f"en '{skill}'. Respuesta correcta: {es_correcto}.")
    pass

def get_next_exercise(student_id):
    print(f"[ADAPTATIVE_ENGINE]: Buscando próximo ejercicio para {student_id}...")
    return "5*(x-1) = 10" 

def explain_recommendation_with_shap(student_id, exercise_id):
    print(f"[XAI_SHAP]: Explicación para {student_id} sobre Ejercicio {exercise_id}: "
          "Recomendado porque falló 'agrupación' 3/5 veces (70% prob. de no saber).")
    pass


# --- EJECUCIÓN DE PRUEBA ---
if __name__ == "__main__":
    
    # Ejemplo 1 : 
    print("--- PRUEBA 1: EJERCICIO MODELO 3 ---")
    eq_str_1 = "3a) 2*(x-3) + 5*(-4+3*x) = -1*(6*x+3)"
    print(f"Ecuación Original: {eq_str_1}\n")
    
    eq_obj_1 = limpiar_y_crear_ecuacion(eq_str_1)
    
    if eq_obj_1 is not None:
        # 1. Clasificar
        caracteristicas_1 = clasificar_ecuacion(eq_obj_1, eq_str_1)
        print("Clasificación de la ecuación:")
        print(caracteristicas_1)
        print("-" * 20)
        
        # 2. Resolver
        print("Resolución Paso a Paso:")
        pasos_1, sol_1 = solve_equation_step_by_step(eq_obj_1)
        for paso in pasos_1:
            print(f"  Paso {paso['paso']}: {paso['descripcion']}")
            print(f"     {str(paso['ecuacion'])}")
        
        print(f"\nSolución Final: x = {sol_1}")
        
        # 3. Simular tracking
        track_to_lrs("estudiante_01", "ej_modelo3_1", "final", sol_1 == 1, 15000, sol_1)
        update_bkt_model("estudiante_01", "resolver-con-parentesis", sol_1 == 1)
    
    else:
        print("La Ecuación 1 no pudo ser procesada.")

    print("\n" + "=" * 40 + "\n")

    # Ejemplo 2 :
    print("--- PRUEBA 2: EJERCICIO PRUEBA MODELO 3 ---")
    eq_str_2 = "3 pruder 6 - 1*(5-2*x) + 7*(x-4) = 3-6*x"
    print(f"Ecuación Original: {eq_str_2}\n")
    
    eq_obj_2 = limpiar_y_crear_ecuacion(eq_str_2)
    
    if eq_obj_2 is not None:
        # 1. Clasificar
        caracteristicas_2 = clasificar_ecuacion(eq_obj_2, eq_str_2)
        print("Clasificación de la ecuación:")
        print(caracteristicas_2)
        print("-" * 20)
        
        # 2. Resolver
        print("Resolución Paso a Paso:")
        pasos_2, sol_2 = solve_equation_step_by_step(eq_obj_2)
        for paso in pasos_2:
            print(f"  Paso {paso['paso']}: {paso['descripcion']}")
            print(f"     {str(paso['ecuacion'])}")
            
        print(f"\nSolución Final: x = {sol_2}")
        
        # 3. Simular tracking
        track_to_lrs("estudiante_02", "ej_modelo3_2_pr", "final", sol_2 == 2, 12000, sol_2)
        update_bkt_model("estudiante_02", "resolver-con-parentesis", sol_2 == 2)
    
    else:
        print("La Ecuarción 2 no pudo ser procesada.")