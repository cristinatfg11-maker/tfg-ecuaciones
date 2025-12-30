# Nombre de archivo: tfg_backend/api/views.py
# Versión: FINAL_REPLICA_FIXED_V5.0

from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, get_user_model
import json
import re
import random 
from . import ecuaciones_core
from .models import Ejercicio, ModeloEjercicio, ProgresoUsuario

User = get_user_model()

# =================================================================
# 1. AUTENTICACIÓN
# =================================================================

@csrf_exempt
def registro_usuario_view(request: HttpRequest):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            if not username or not password: return JsonResponse({'error': 'Faltan datos'}, status=400)
            
            if User.objects.filter(username=username).exists(): 
                return JsonResponse({'error': 'El usuario ya existe'}, status=400)
            
            user = User.objects.create_user(username=username, password=password)
            
            # --- CORRECCIÓN: Puntos Iniciales = 50 (Solicitado) ---
            ProgresoUsuario.objects.create(usuario=user, puntos_totales=50)
            
            return JsonResponse({'status': 'exito', 'mensaje': 'Usuario registrado'})
        except Exception as e: return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Solo POST'}, status=405)

@csrf_exempt
def login_usuario_view(request: HttpRequest):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                progreso, _ = ProgresoUsuario.objects.get_or_create(usuario=user)
                return JsonResponse({
                    'status': 'exito', 
                    'user_id': user.id, 
                    'username': user.username, 
                    'puntos': progreso.puntos_totales
                })
            else: return JsonResponse({'error': 'Credenciales incorrectas'}, status=401)
        except Exception as e: return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Solo POST'}, status=405)

@csrf_exempt
def cambiar_password_view(request: HttpRequest):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = authenticate(username=data.get('username'), password=data.get('old_password'))
            if user:
                user.set_password(data.get('new_password'))
                user.save()
                return JsonResponse({'status': 'exito'})
            return JsonResponse({'error': 'Contraseña incorrecta'}, status=400)
        except Exception as e: return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Solo POST'}, status=405)

@csrf_exempt
def actualizar_puntos_view(request: HttpRequest):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            progreso = ProgresoUsuario.objects.get(usuario_id=data.get('user_id'))
            progreso.puntos_totales = data.get('puntos')
            progreso.save()
            return JsonResponse({'status': 'exito'})
        except Exception as e: return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Solo POST'}, status=405)

# =================================================================
# 2. LÓGICA ALEATORIA Y RANKING
# =================================================================

@csrf_exempt
def lista_modelos_view(request: HttpRequest):
    try:
        modelos = ModeloEjercicio.objects.all().order_by('nombre')
        lista = [{'id': m.id, 'nombre': m.nombre} for m in modelos]
        return JsonResponse({'modelos': lista})
    except: return JsonResponse({'modelos': []})

@csrf_exempt
def obtener_ejercicio_aleatorio_view(request: HttpRequest):
    """Devuelve un ejercicio aleatorio NO completado del tipo solicitado"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            tipo_solicitado = data.get('tipo', 'ENTRENAMIENTO')
            
            progreso = ProgresoUsuario.objects.get(usuario_id=user_id)
            completados_ids = progreso.ejercicios_completados.values_list('id', flat=True)
            disponibles = Ejercicio.objects.filter(tipo=tipo_solicitado).exclude(id__in=completados_ids)
            
            if not disponibles.exists():
                return JsonResponse({'status': 'fin', 'mensaje': '¡Has completado todos los ejercicios!'})
            
            seleccionado = random.choice(list(disponibles))
            
            # --- CORRECCIÓN: Usar detección dinámica para soportar variable 'm' ---
            # En lugar de usar los flags fijos de la BD, recalculamos al vuelo
            eq_obj = ecuaciones_core.limpiar_y_crear_ecuacion(seleccionado.ecuacion_str)
            caracteristicas_reales = ecuaciones_core.clasificar_ecuacion(eq_obj, seleccionado.ecuacion_str)
            
            return JsonResponse({
                'status': 'exito',
                'id': seleccionado.id,
                'ecuacion_str': seleccionado.ecuacion_str,
                'modelo_id': seleccionado.modelo.id if seleccionado.modelo else None,
                'caracteristicas': caracteristicas_reales # Usamos la calculada, no la de BD
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Solo POST'}, status=405)

@csrf_exempt
def marcar_ejercicio_completado_view(request: HttpRequest):
    # NOTA: Mantenemos el nombre EXACTO que espera urls.py
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            ejercicio_id = data.get('ejercicio_id')
            progreso = ProgresoUsuario.objects.get(usuario_id=user_id)
            ejercicio = Ejercicio.objects.get(id=ejercicio_id)
            progreso.ejercicios_completados.add(ejercicio)
            progreso.save()
            return JsonResponse({'status': 'exito'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Solo POST'}, status=405)

@csrf_exempt
def ranking_usuarios_view(request: HttpRequest):
    if request.method == 'GET':
        try:
            ranking = ProgresoUsuario.objects.select_related('usuario').order_by('-puntos_totales')[:10]
            data = [{'username': p.usuario.username, 'puntos': p.puntos_totales} for p in ranking]
            return JsonResponse({'ranking': data})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Solo GET'}, status=405)

# =================================================================
# 3. LÓGICA CORE (RESOLVER)
# =================================================================

def obtener_pasos_formateados(ejercicio_obj):
    pasos_en_bd = ejercicio_obj.pasos.all().order_by('numero_paso')
    return [{'paso': p.numero_paso, 'descripcion': p.descripcion, 'ecuacion': p.ecuacion_resultante} for p in pasos_en_bd]

def obtener_descripciones_pasos(pasos_formateados):
    return [f"Paso {p['paso']}: {p['descripcion']}" for p in pasos_formateados]

def extraer_valor_simple(solucion_latex):
    if not solucion_latex: return ""
    if "Infinitas" in solucion_latex or "No tiene" in solucion_latex: return solucion_latex
    valor = str(solucion_latex).replace('$$', '')
    valor = re.sub(r"\\text\{.*?\}", "", valor)
    valor = re.sub(r"\\boxed", "", valor)
    valor = re.sub(r"^[a-zA-Z]\s*=\s*", "", valor.strip())
    valor = re.sub(r"\\frac\{(-?\d+)\}\{(-?\d+)\}", r"\1/\2", valor)
    return valor.replace('{', '').replace('}', '').strip()

@csrf_exempt
def resolver_ecuacion_view(request: HttpRequest):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            equation_str = data.get('ecuacion')
            if not equation_str: return JsonResponse({'error': 'Falta ecuacion'}, status=400)
            
            try:
                # 1. Intentamos buscar en BD
                ej_bd = Ejercicio.objects.get(ecuacion_str=equation_str)
                tipo = ej_bd.tipo
                pasos = obtener_pasos_formateados(ej_bd)
                solucion = ej_bd.solucion
                
                # Si no tiene pasos guardados (fue importado solo con sol final), los calculamos
                if not pasos:
                    raise Ejercicio.DoesNotExist 

            except Ejercicio.DoesNotExist:
                # 2. Si no está en BD o no tiene pasos, calculamos al vuelo
                tipo = 'PRUEBA' # Por defecto si no se sabe
                eq = ecuaciones_core.limpiar_y_crear_ecuacion(equation_str)
                if not eq: return JsonResponse({'error': 'Error parseo'}, status=400)
                pasos, solucion = ecuaciones_core.solve_equation_step_by_step(eq)

            # 3. Respuesta
            if tipo == 'ENTRENAMIENTO':
                return JsonResponse({
                    'status': 'exito', 
                    'fuente': 'Entrenamiento', 
                    'solucion_final': f"x = {solucion}" if solucion and "x" not in str(solucion) else solucion, 
                    'pasos_resolucion': pasos
                })
            else:
                return JsonResponse({
                    'status': 'exito', 
                    'fuente': 'Prueba', 
                    'solucion_oculta': extraer_valor_simple(solucion),
                    'solucion_final_latex': f"x = {solucion}" if solucion and "x" not in str(solucion) else solucion, 
                    'pasos_descripciones': obtener_descripciones_pasos(pasos),
                    'pasos_completos_ocultos': pasos
                })
        except Exception as e: return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Solo POST'}, status=405)

# Compatibilidad para evitar errores 404 si el frontend llama a algo viejo
@csrf_exempt
def clasificar_modelo_view(request): return JsonResponse({}) 
@csrf_exempt 
def get_ejercicios_por_modelo_view(request, modelo_id): return JsonResponse({}) 
@csrf_exempt
def marcar_completado_view(request): 
    # Redirección interna por si acaso
    return marcar_ejercicio_completado_view(request)