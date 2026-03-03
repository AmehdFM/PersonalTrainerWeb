import os
import json
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse_lazy, reverse
from django.db import transaction, models
from django.db.models import Sum, Count, Prefetch
from django.http import JsonResponse
from django import forms
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

from .models import Usuario
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from clientes.models import MembresiaCliente, TipoMembresia, PerfilCliente, RegistroMedidas
from rutinas.models import Rutina, DiaRutina, EjercicioRutina

# Forms
class UsuarioEditForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'correo', 'telefono', 'fecha_nacimiento']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
        }

class MembresiaManualForm(forms.ModelForm):
    class Meta:
        model = MembresiaCliente
        fields = ['tipo', 'fecha_fin']
        widgets = {
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
        }

class PerfilClienteForm(forms.ModelForm):
    class Meta:
        model = PerfilCliente
        fields = ['peso_lbs', 'altura_cm']

class RegistroMedidasForm(forms.ModelForm):
    class Meta:
        model = RegistroMedidas
        exclude = ['usuario', 'fecha_registro', 'is_deleted']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
        }

# Decorators
def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.rol != Usuario.Roles.ADMIN:
            return redirect('landing')
        return view_func(request, *args, **kwargs)
    return wrapper

# Views
def landing_page(request):
    return render(request, 'landing.html')

def admin_dashboard(request):
    # 1. Core Metrics
    total_clients = Usuario.objects.filter(rol=Usuario.Roles.CLIENTE, is_deleted=False).count()
    active_clients = Usuario.objects.filter(rol=Usuario.Roles.CLIENTE, activo=True, is_deleted=False).count()
    active_memberships = MembresiaCliente.objects.filter(estado='activa')
    active_memberships_count = active_memberships.count()
    total_routines = Rutina.objects.count()
    
    # 2. Retention Metrics (Expirations in next 7 days)
    today = timezone.now().date()
    next_week = today + timedelta(days=7)
    expiring_soon = active_memberships.filter(fecha_fin__lte=next_week, fecha_fin__gte=today).count()
    
    stats = {
        'total_clients': total_clients,
        'active_clients': active_clients,
        'active_memberships': active_memberships_count,
        'total_routines': total_routines,
        'expiring_soon': expiring_soon,
    }

    return render(request, 'admin/dashboard.html', {
        'stats': stats,
    })

def admin_clientes(request):
    clientes = Usuario.objects.filter(rol=Usuario.Roles.CLIENTE, is_deleted=False).select_related('perfil_cliente').prefetch_related(
        Prefetch('membresias', 
                 queryset=MembresiaCliente.objects.filter(estado='activa').select_related('tipo'),
                 to_attr='active_membership')
    ).order_by('-fecha_registro')
    return render(request, 'admin/clientes.html', {'clientes': clientes})

def admin_rutinas(request):
    rutinas = Rutina.objects.all().select_related('cliente')
    return render(request, 'admin/rutinas.html', {'rutinas': rutinas})

def admin_cliente_detail(request, pk):
    cliente = get_object_or_404(Usuario, pk=pk)
    perfil, _ = PerfilCliente.objects.get_or_create(usuario=cliente)
    membresia = cliente.membresias.filter(estado='activa').first()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'edit_full_profile':
            user_form = UsuarioEditForm(request.POST, instance=cliente)
            perfil_form = PerfilClienteForm(request.POST, instance=perfil)
            
            # Use MembresiaManualForm for the active membership if it exists
            if membresia:
                mem_form = MembresiaManualForm(request.POST, instance=membresia)
            else:
                mem_form = None

            if user_form.is_valid() and perfil_form.is_valid() and (not mem_form or mem_form.is_valid()):
                user_form.save()
                perfil_form.save()
                if mem_form:
                    mem_form.save()
                return redirect('admin_cliente_detail', pk=cliente.pk)
        
        elif action in ['add_medida', 'edit_medida']:
            instance = None
            if action == 'edit_medida':
                medida_id = request.POST.get('medida_id')
                instance = get_object_or_404(RegistroMedidas, pk=medida_id, usuario=cliente)
            
            form = RegistroMedidasForm(request.POST, instance=instance)
            if form.is_valid():
                medida = form.save(commit=False)
                medida.usuario = cliente
                medida.save()
                return redirect('admin_cliente_detail', pk=cliente.pk)
    
    # Context for GET or invalid POST
    context = {
        'cliente_obj': cliente,
        'user_form': UsuarioEditForm(instance=cliente),
        'perfil_form': PerfilClienteForm(instance=perfil),
        'mem_form': MembresiaManualForm(instance=membresia) if membresia else None,
        'medidas_form': RegistroMedidasForm(),
        'medidas_historial': cliente.registros_medidas.all(),
        'rutinas_asignadas': cliente.rutinas.all(),
        'tipos_membresia': TipoMembresia.objects.filter(activo=True),
    }
    return render(request, 'admin/cliente_detail.html', context)

def _get_catalogo_ejercicios():
    from decouple import config
    import requests
    from django.core.cache import cache
    api_key = config('MICROSERVICE_API_KEY', default='')
    base_url = config('MICROSERVICE_BASE_URL', default='https://exercisecatalog.dsem.app/api/')
    headers = {'Authorization': f'Api-Key {api_key}'}
    
    exercises_json = cache.get('routine_exercises_list')
    if exercises_json is None:
        try:
            ex_res = requests.get(f"{base_url}exercises/", headers=headers, timeout=10)
            if ex_res.status_code == 200:
                exercises_json = ex_res.json()
                if isinstance(exercises_json, dict) and 'results' in exercises_json:
                    exercises_json = exercises_json['results']
                cache.set('routine_exercises_list', exercises_json, 86400) # 24h
        except Exception as e:
            print(f"Error fetching microservice data: {e}")
            
    if isinstance(exercises_json, dict) and 'results' in exercises_json:
        exercises_json = exercises_json['results']
        
    return exercises_json or []

def _get_ejercicios_especificos(ejercicio_ids):
    from decouple import config
    import requests
    from django.core.cache import cache
    api_key = config('MICROSERVICE_API_KEY', default='')
    base_url = config('MICROSERVICE_BASE_URL', default='https://exercisecatalog.dsem.app/api/')
    headers = {'Authorization': f'Api-Key {api_key}'}
    
    resultados = []
    for eid in set(ejercicio_ids):
        if not eid: continue
        cache_key = f'ejercicio_detalle_{eid}'
        cached = cache.get(cache_key)
        if cached:
            resultados.append(cached)
            continue
            
        try:
            res = requests.get(f"{base_url}exercises/{eid}/", headers=headers, timeout=5)
            if res.status_code == 200:
                data = res.json()
                cache.set(cache_key, data, 86400)
                resultados.append(data)
        except Exception as e:
            print(f"Error fetching exercise {eid}: {e}")
            
    return resultados

def admin_rutina_builder(request, pk=None):
    rutina_existente = None
    if pk:
        rutina_existente = get_object_or_404(Rutina, pk=pk)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
            
        try:
            with transaction.atomic():
                # 1. Update/Create Routine
                cliente_id = data.get('cliente_id')
                nombre_rutina = data.get('nombre', 'Nueva Rutina')
                
                if rutina_existente:
                    rutina_existente.cliente_id = cliente_id
                    rutina_existente.nombre = nombre_rutina
                    rutina_existente.imagen_url = data.get('imagen_url', '')
                    rutina_existente.save()
                    rutina = rutina_existente
                else:
                    rutina = Rutina.objects.create(
                        cliente_id=cliente_id,
                        nombre=nombre_rutina,
                        imagen_url=data.get('imagen_url', ''),
                        creado_por=request.user,
                        activa=True
                    )
                
                # 2. Add/Update Days and Exercises
                dias_agregados = set()
                for day_data in data.get('days', []):
                    dias_asignados = day_data.get('dias', [])
                    exercises_to_add = day_data.get('exercises', [])
                    
                    if not dias_asignados:
                        continue

                    for dia_val_raw in dias_asignados:
                        try:
                            dia_val = int(dia_val_raw)
                        except (ValueError, TypeError):
                            continue
                            
                        if dia_val in dias_agregados:
                            continue 
                        dias_agregados.add(dia_val)
                        
                        # Use update_or_create to avoid UNIQUE constraint conflicts in the middle of a transaction
                        dia_obj, _ = DiaRutina.objects.update_or_create(
                            rutina=rutina,
                            dia_semana=dia_val,
                            defaults={
                                'nombre': day_data.get('nombre_bloque', ''),
                                'orden': day_data.get('orden', 0),
                                'notas': day_data.get('notas', '')
                            }
                        )
                        
                        # Rebuild exercises for this specific day
                        dia_obj.ejercicios.all().delete()
                        for exercise_data in exercises_to_add:
                            EjercicioRutina.objects.create(
                                dia=dia_obj,
                                ejercicio_id=exercise_data.get('id_externo'),
                                series=exercise_data.get('series', 3),
                                repeticiones=exercise_data.get('reps', 10),
                                peso_lbs=exercise_data.get('peso', None),
                                descanso_segundos=exercise_data.get('descanso', 60),
                                notas=exercise_data.get('notas', ''),
                                orden=exercise_data.get('orden', 0)
                            )
                
                # 3. Delete orphaned days (present in DB but not in current request)
                DiaRutina.objects.filter(rutina=rutina).exclude(dia_semana__in=dias_agregados).delete()
                
                return JsonResponse({'status': 'ok', 'rutina_id': rutina.id})
                
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return JsonResponse({'status': 'error', 'message': f"Error en servidor: {str(e)}"}, status=500)

    # GET logic
    clientes = Usuario.objects.filter(rol=Usuario.Roles.CLIENTE)
    
    exercises_json = _get_catalogo_ejercicios()
    
    # Try to get tags data from cache first
    from decouple import config
    api_key = config('MICROSERVICE_API_KEY', default='')
    base_url = config('MICROSERVICE_BASE_URL', default='https://exercisecatalog.dsem.app/api/')
    headers = {'Authorization': f'Api-Key {api_key}'}
    
    tags_json = cache.get('routine_tags_list')
    if tags_json is None:
        try:
            tags_res = requests.get(f"{base_url}tags/", headers=headers, timeout=10)
            if tags_res.status_code == 200:
                tags_json = tags_res.json()
                if isinstance(tags_json, dict) and 'results' in tags_json:
                    tags_json = tags_json['results']
                cache.set('routine_tags_list', tags_json, 86400)
        except Exception as e:
            print(f"Error fetching tags data: {e}")
            tags_json = []

    if isinstance(tags_json, dict) and 'results' in tags_json:
        tags_json = tags_json['results']
    tags_json = tags_json or []
        
    clientes_data = [{'pk': c.pk, 'nombre_completo': c.nombre_completo, 'email': c.correo} for c in clientes]
    
    # Existing data for editing
    rutina_data = None
    if rutina_existente:
        rutina_data = {
            'id': rutina_existente.id,
            'nombre': rutina_existente.nombre,
            'imagen_url': rutina_existente.imagen_url or '',
            'cliente_id': rutina_existente.cliente_id,
            'cliente_nombre': rutina_existente.cliente.nombre_completo,
            'days': []
        }
        for dia in rutina_existente.dias.all():
            day_json = {
                'nombre_bloque': dia.nombre,
                'dias': [dia.dia_semana],
                'exercises': [],
                'notas': dia.notas,
                'orden': dia.orden
            }
            for ej in dia.ejercicios.all():
                # Try to find the actual name from the exercises we just loaded/cached
                ej_name = 'Ejercicio'
                if exercises_json:
                    # Match by 'id' or 'pk' and support 'name' or 'nombre'
                    matched = next((x for x in exercises_json if str(x.get('id', x.get('pk', ''))) == str(ej.ejercicio_id)), None)
                    if matched:
                        ej_name = matched.get('name') or matched.get('nombre') or 'Ejercicio'

                day_json['exercises'].append({
                    'id_externo': ej.ejercicio_id,
                    'name': ej_name,
                    'series': ej.series,
                    'reps': ej.repeticiones,
                    'peso': ej.peso_lbs,
                    'descanso': ej.descanso_segundos,
                    'notas': ej.notas,
                    'orden': ej.orden
                })
            rutina_data['days'].append(day_json)
            
    return render(request, 'admin/rutina_builder.html', {
        'clientes': clientes,
        'clientes_data': clientes_data,
        'exercises_json': exercises_json,
        'tags_json': tags_json,
        'rutina_data': rutina_data
    })

def custom_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomAuthenticationForm()
        
    return render(request, 'login.html', {'form': form})

def register_user(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
        
    return render(request, 'register.html', {'form': form})

def logout_user(request):
    logout(request)
    return redirect('landing')

# ─── Cliente Area ────────────────────────────────────────────────────────────

def _get_demo_cliente(request):
    """Return the simulated logged-in client from session."""
    cliente_id = request.session.get('demo_cliente_id')
    if cliente_id:
        try:
            return Usuario.objects.select_related('perfil_cliente').get(pk=cliente_id, rol=Usuario.Roles.CLIENTE)
        except Usuario.DoesNotExist:
            pass
    return None

def cliente_home(request):
    """Entry point: pick a random client and store in session, then redirect."""
    import random as rnd
    # Prefer clients who have at least one rutina
    clientes_con_rutina = list(
        Usuario.objects.filter(rol=Usuario.Roles.CLIENTE, is_deleted=False)
        .annotate(num_rutinas=models.Count('rutinas'))
        .filter(num_rutinas__gt=0)
    )
    pool = clientes_con_rutina if clientes_con_rutina else list(
        Usuario.objects.filter(rol=Usuario.Roles.CLIENTE, is_deleted=False)
    )
    if not pool:
        return render(request, 'clientes/sin_clientes.html')
    cliente = rnd.choice(pool)
    request.session['demo_cliente_id'] = cliente.pk
    return redirect('cliente_inicio')

def cliente_inicio(request):
    cliente = _get_demo_cliente(request)
    if not cliente:
        return redirect('cliente_home')

    from datetime import date
    from clientes.models import MembresiaCliente, PerfilCliente
    from rutinas.models import Rutina, DiaRutina

    membresia = cliente.membresias.filter(estado='activa').select_related('tipo').first()
    perfil, _ = PerfilCliente.objects.get_or_create(usuario=cliente)

    hoy = date.today()
    dia_semana_hoy = hoy.weekday() + 1  # Mon=1 … Sun=7 (same as DiaRutina)

    # Find today's training day
    rutina_hoy = None
    dia_hoy = DiaRutina.objects.filter(
        rutina__cliente=cliente,
        rutina__activa=True,
        dia_semana=dia_semana_hoy
    ).select_related('rutina').prefetch_related('ejercicios').first()

    rutinas = cliente.rutinas.filter(activa=True).prefetch_related('dias')
    medidas_count = cliente.registros_medidas.count()

    return render(request, 'clientes/home.html', {
        'cliente': cliente,
        'membresia': membresia,
        'perfil': perfil,
        'dia_hoy': dia_hoy,
        'rutinas': rutinas,
        'medidas_count': medidas_count,
        'hoy': hoy,
    })

def cliente_rutina(request):
    cliente = _get_demo_cliente(request)
    if not cliente:
        return redirect('cliente_home')

    from datetime import date
    from rutinas.models import Rutina, DiaRutina

    hoy = date.today()
    dia_semana_hoy = hoy.weekday() + 1

    rutinas = cliente.rutinas.filter(activa=True).prefetch_related('dias__ejercicios')
    # Mark which days of each rutina match today
    dia_hoy_ids = set(
        DiaRutina.objects.filter(
            rutina__cliente=cliente,
            rutina__activa=True,
            dia_semana=dia_semana_hoy
        ).values_list('id', flat=True)
    )

    return render(request, 'clientes/rutina.html', {
        'cliente': cliente,
        'rutinas': rutinas,
        'dia_hoy_ids': dia_hoy_ids,
        'dia_semana_hoy': dia_semana_hoy,
    })

def cliente_rutina_play(request, dia_id):
    cliente = _get_demo_cliente(request)
    if not cliente:
        return redirect('cliente_home')

    from rutinas.models import DiaRutina
    dia = get_object_or_404(DiaRutina, pk=dia_id, rutina__cliente=cliente)
    ejercicios_db = list(dia.ejercicios.all().order_by('orden'))

    # Enrich with names from cache/API
    ids = [ej.ejercicio_id for ej in ejercicios_db if ej.ejercicio_id]
    exercises_json = _get_ejercicios_especificos(ids)
    ex_map = {str(x.get('id', x.get('pk', ''))): x for x in exercises_json}

    ejercicios = []
    for ej in ejercicios_db:
        cached = ex_map.get(str(ej.ejercicio_id), {})
        ejercicios.append({
            'id': ej.pk,
            'nombre': cached.get('name') or cached.get('nombre') or f'Ejercicio {ej.ejercicio_id}',
            'gif_url': cached.get('gif_url', ''),
            'series': ej.series,
            'reps': ej.repeticiones,
            'peso_lbs': str(ej.peso_lbs) if ej.peso_lbs else None,
            'descanso_seg': ej.descanso_segundos,
            'notas': ej.notas,
        })

    return render(request, 'clientes/rutina_play.html', {
        'cliente': cliente,
        'dia': dia,
        'ejercicios_json': ejercicios,
        'total': len(ejercicios),
    })

def cliente_medidas(request):
    cliente = _get_demo_cliente(request)
    if not cliente:
        return redirect('cliente_home')

    from clientes.models import RegistroMedidas
    from datetime import date

    if request.method == 'POST':
        from decimal import Decimal, InvalidOperation
        def dec(val):
            try:
                return Decimal(val) if val else None
            except InvalidOperation:
                return None

        RegistroMedidas.objects.create(
            usuario=cliente,
            fecha=request.POST.get('fecha') or date.today(),
            peso_lbs=dec(request.POST.get('peso_lbs')) or Decimal('0'),
            cuello=dec(request.POST.get('cuello')),
            hombros=dec(request.POST.get('hombros')),
            pecho=dec(request.POST.get('pecho')),
            cintura=dec(request.POST.get('cintura')),
            cadera=dec(request.POST.get('cadera')),
            brazo_izq=dec(request.POST.get('brazo_izq')),
            brazo_der=dec(request.POST.get('brazo_der')),
            muslo_izq=dec(request.POST.get('muslo_izq')),
            muslo_der=dec(request.POST.get('muslo_der')),
            notas=request.POST.get('notas', ''),
        )
        return redirect('cliente_medidas')

    historial = cliente.registros_medidas.all()[:20]

    # Build weight chart data (last 10 measurements, oldest first)
    chart_data = list(
        cliente.registros_medidas.values('fecha', 'peso_lbs').order_by('fecha')[:10]
    )

    return render(request, 'clientes/medidas.html', {
        'cliente': cliente,
        'historial': historial,
        'chart_data': chart_data,
        'hoy': date.today().isoformat(),
        'field_list': [
            {'name': 'cuello',         'label': 'Cuello'},
            {'name': 'hombros',        'label': 'Hombros'},
            {'name': 'pecho',          'label': 'Pecho'},
            {'name': 'cintura',        'label': 'Cintura'},
            {'name': 'cadera',         'label': 'Cadera'},
            {'name': 'brazo_izq',      'label': 'Brazo Izq'},
            {'name': 'brazo_der',      'label': 'Brazo Der'},
            {'name': 'muslo_izq',      'label': 'Muslo Izq'},
            {'name': 'muslo_der',      'label': 'Muslo Der'},
        ],
    })
