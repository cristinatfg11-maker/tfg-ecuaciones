# Nombre de archivo: api/views.py
# Versión: UPDATE_RANKING_ENDPOINT_V4.0

from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
import json
import re
import random 
from . import ecuaciones_core
from .models import Ejercicio, ModeloEjercicio, ProgresoUsuario

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
            if User.objects.filter(username=username).exists(): return JsonResponse({'error': 'El usuario ya existe'}, status=400)
            user = User.objects.create_user(username=username, password=password)
            ProgresoUsuario.objects.create(usuario=user, puntos_totales=0)
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
                progreso, _ = ProgresoUsuario.objects.get_or_create(usuario=user)
                return JsonResponse({'status': 'exito', 'user_id': user.id, 'username': user.username, 'puntos': progreso.puntos_totales})
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
# 2. NUEVA LÓGICA ALEATORIA Y RANKING (GAMIFICACIÓN)
# =================================================================

@csrf_exempt
def obtener_ejercicio_aleatorio_view(request: HttpRequest):
    """Devuelve un ejercicio aleatorio NO completado del tipo solicitado"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('user_id')
            tipo_solicitado = data.get('tipo') 
            
            progreso = ProgresoUsuario.objects.get(usuario_id=user_id)
            completados_ids = progreso.ejercicios_completados.values_list('id', flat=True)
            disponibles = Ejercicio.objects.filter(tipo=tipo_solicitado).exclude(id__in=completados_ids)
            
            if not disponibles.exists():
                return JsonResponse({'status': 'fin', 'mensaje': '¡Has completado todos los ejercicios!'})
            
            seleccionado = random.choice(list(disponibles))
            
            return JsonResponse({
                'status': 'exito',
                'id': seleccionado.id,
                'ecuacion_str': seleccionado.ecuacion_str,
                'modelo_id': seleccionado.modelo.id,
                'caracteristicas': {
                    'incognita_una_vez': seleccionado.modelo.incognita_una_vez,
                    'incognita_mas_de_una_vez': seleccionado.modelo.incognita_mas_de_una_vez,
                    'con_parentesis': seleccionado.modelo.con_parentesis,
                    'con_fracciones': seleccionado.modelo.con_fracciones
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Solo POST'}, status=405)

@csrf_exempt
def marcar_ejercicio_completado_view(request: HttpRequest):
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

# ACTUALIZACIÓN 3a: Vista para obtener el Ranking
@csrf_exempt
def ranking_usuarios_view(request: HttpRequest):
    if request.method == 'GET':
        try:
            # Obtenemos los 10 mejores puntajes, orden descendente
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
    if "Infinitas" in solucion_latex or "No tiene" in solucion_latex: return solucion_latex
    valor = solucion_latex.replace('$$', '')
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
                ej_bd = Ejercicio.objects.get(ecuacion_str=equation_str)
                pasos = obtener_pasos_formateados(ej_bd)
                
                if ej_bd.tipo == 'ENTRENAMIENTO':
                    return JsonResponse({'status': 'exito', 'fuente': 'Entrenamiento', 'solucion_final': ej_bd.solucion, 'pasos_resolucion': pasos})
                else:
                    return JsonResponse({
                        'status': 'exito', 'fuente': 'Prueba', 'solucion_oculta': extraer_valor_simple(ej_bd.solucion),
                        'solucion_final_latex': ej_bd.solucion, 'pasos_descripciones': obtener_descripciones_pasos(pasos),
                        'pasos_completos_ocultos': pasos
                    })
            except Ejercicio.DoesNotExist:
                eq = ecuaciones_core.limpiar_y_crear_ecuacion(equation_str)
                if not eq: return JsonResponse({'error': 'Error parseo'}, status=400)
                pasos_c, sol_c = ecuaciones_core.solve_equation_step_by_step(eq)
                return JsonResponse({
                    'status': 'exito', 'fuente': 'Prueba', 'solucion_oculta': extraer_valor_simple(sol_c),
                    'solucion_final_latex': sol_c, 'pasos_descripciones': obtener_descripciones_pasos(pasos_c),
                    'pasos_completos_ocultos': pasos_c
                })
        except Exception as e: return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Solo POST'}, status=405)

# Compatibilidad
@csrf_exempt
def clasificar_modelo_view(request: HttpRequest): return JsonResponse({}) 
@csrf_exempt 
def get_ejercicios_por_modelo_view(request: HttpRequest, modelo_id: int): return JsonResponse({}) 
@csrf_exempt
def lista_modelos_view(request: HttpRequest): 
    # Necesario para el frontend corregido
    try:
        modelos = ModeloEjercicio.objects.all().order_by('nombre')
        lista = [{'id': m.id, 'nombre': m.nombre} for m in modelos]
        return JsonResponse({'modelos': lista})
    except: return JsonResponse({'modelos': []})