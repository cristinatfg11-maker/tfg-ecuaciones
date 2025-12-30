# Nombre de archivo: tfg_backend/api/views.py
# Versión: LOCAL_REPLICA_FINAL

import json
import random
from django.contrib.auth import authenticate, login, get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F
from .models import Ejercicio, ModeloEjercicio, ProgresoUsuario, PasoResolucion
from .ecuaciones_core import solve_equation_step_by_step, limpiar_y_crear_ecuacion, clasificar_ecuacion

User = get_user_model()

@csrf_exempt
def registro_usuario_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'El usuario ya existe'}, status=400)
        
        user = User.objects.create_user(username=username, password=password)
        
        # --- REPLICA EXACTA LOCAL: Puntos Iniciales = 50 ---
        ProgresoUsuario.objects.create(usuario=user, puntos_totales=50)
        
        return JsonResponse({'status': 'exito', 'mensaje': 'Usuario registrado'})
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
def login_usuario_view(request):
    if request.method == 'POST':
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
        else:
            return JsonResponse({'error': 'Credenciales inválidas'}, status=400)
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
def cambiar_password_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        new_password = data.get('new_password')
        
        user = authenticate(username=username, password=password)
        if user is not None:
            user.set_password(new_password)
            user.save()
            return JsonResponse({'status': 'exito', 'mensaje': 'Contraseña actualizada'})
        else:
            return JsonResponse({'error': 'Credenciales actuales incorrectas'}, status=400)
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
def lista_modelos_view(request):
    modelos = ModeloEjercicio.objects.all().values('id', 'nombre')
    return JsonResponse({'modelos': list(modelos)})

@csrf_exempt
def obtener_ejercicio_aleatorio_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_id = data.get('user_id')
        tipo = data.get('tipo', 'ENTRENAMIENTO')
        
        try:
            progreso = ProgresoUsuario.objects.get(usuario_id=user_id)
            completados_ids = progreso.ejercicios_completados.values_list('id', flat=True)
            
            # Filtrar ejercicios del tipo solicitado que NO estén completados
            ejercicios_disponibles = Ejercicio.objects.filter(tipo=tipo).exclude(id__in=completados_ids)
            
            if not ejercicios_disponibles.exists():
                return JsonResponse({'status': 'fin', 'mensaje': 'No hay más ejercicios disponibles.'})
            
            ejercicio = random.choice(list(ejercicios_disponibles))
            
            eq_obj = limpiar_y_crear_ecuacion(ejercicio.ecuacion_str)
            caracteristicas = clasificar_ecuacion(eq_obj, ejercicio.ecuacion_str)
            
            # Inyectamos las características reales desde la lógica matemática
            # para asegurar que coincidan con la clasificación visual
            
            return JsonResponse({
                'status': 'exito',
                'id': ejercicio.id,
                'ecuacion_str': ejercicio.ecuacion_str,
                'modelo_id': ejercicio.modelo.id if ejercicio.modelo else None,
                'caracteristicas': caracteristicas
            })
            
        except ProgresoUsuario.DoesNotExist:
            return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def resolver_ecuacion_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        ecuacion_str = data.get('ecuacion')
        
        # 1. Buscar si ya existe en BD para ahorrar cálculo
        ej_bd = Ejercicio.objects.filter(ecuacion_str=ecuacion_str).first()
        tipo_ejercicio = ej_bd.tipo if ej_bd else 'ENTRENAMIENTO'
        
        # 2. Calcular pasos dinámicamente usando el core (Local Logic)
        eq_obj = limpiar_y_crear_ecuacion(ecuacion_str)
        if eq_obj is None:
            return JsonResponse({'error': 'Ecuación inválida'}, status=400)
            
        pasos, solucion_final = solve_equation_step_by_step(eq_obj)
        
        # 3. Preparar respuesta según modo
        if tipo_ejercicio == 'PRUEBA':
            # Modo Prueba: Ocultamos la solución final y la descripción completa
            pasos_ocultos = []
            for p in pasos:
                pasos_ocultos.append({
                    'paso': p['paso'],
                    'descripcion': p['descripcion'], # Se enviará, pero el Frontend decide cuándo mostrar
                    'ecuacion': p['ecuacion']
                })
            
            return JsonResponse({
                'fuente': 'Prueba',
                'solucion_oculta': solucion_final, # Para validación interna del frontend
                'solucion_final_latex': f"x = {solucion_final}" if solucion_final and "x =" not in str(solucion_final) else solucion_final,
                'pasos_completos_ocultos': pasos_ocultos
            })
        else:
            # Modo Entrenamiento: Enviamos todo abierto
            return JsonResponse({
                'fuente': 'Entrenamiento',
                'pasos_resolucion': pasos,
                'solucion_final': f"x = {solucion_final}" if solucion_final and "x =" not in str(solucion_final) else solucion_final
            })

@csrf_exempt
def actualizar_puntos_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_id = data.get('user_id')
        nuevos_puntos = data.get('puntos')
        
        try:
            progreso = ProgresoUsuario.objects.get(usuario_id=user_id)
            progreso.puntos_totales = nuevos_puntos
            progreso.save()
            return JsonResponse({'status': 'ok', 'puntos': progreso.puntos_totales})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def marcar_completado_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_id = data.get('user_id')
        ejercicio_id = data.get('ejercicio_id')
        
        try:
            progreso = ProgresoUsuario.objects.get(usuario_id=user_id)
            ejercicio = Ejercicio.objects.get(id=ejercicio_id)
            progreso.ejercicios_completados.add(ejercicio)
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def ranking_usuarios_view(request):
    ranking = ProgresoUsuario.objects.select_related('usuario').order_by('-puntos_totales')[:10]
    data = [{'username': r.usuario.username, 'puntos': r.puntos_totales} for r in ranking]
    return JsonResponse({'ranking': data})