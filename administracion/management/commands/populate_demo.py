import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from administracion.models import Usuario
from clientes.models import TipoMembresia, MembresiaCliente, PerfilCliente, RegistroMedidas
from rutinas.models import Rutina, DiaRutina, EjercicioRutina

class Command(BaseCommand):
    help = 'Popula la base de datos con datos de ejemplo para demostración'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando población de datos...")
        
        # 1. Planes
        planes_info = [
            {'nombre': 'basica', 'precio': 350.00, 'duracion': 30},
            {'nombre': 'pro', 'precio': 550.00, 'duracion': 30},
            {'nombre': 'max', 'precio': 750.00, 'duracion': 30},
        ]
        
        plan_objs = {}
        for p in planes_info:
            obj, _ = TipoMembresia.objects.get_or_create(
                nombre=p['nombre'],
                defaults={
                    'precio_mensual': p['precio'],
                    'duracion_dias': p['duracion'],
                    'acceso_clases_grupales': p['nombre'] != 'basica',
                    'acceso_areas_premium': p['nombre'] == 'max'
                }
            )
            plan_objs[p['nombre']] = obj

        # 2. Clientes
        nombres = ["Marcos", "Elena", "Roberto", "Lucía", "Fernando", "Gabriela", "Adrián", "Patricia", "Hugo", "Isabel", "Javier", "Mónica", "Diego", "Silvia", "Alejandro"]
        apellidos = ["Gómez", "López", "Díaz", "Torres", "Ruiz", "Vargas", "Castro", "Mendoza", "Ortiz", "Navarro"]
        
        counts = 0
        for i in range(15):
            nombre = nombres[i % len(nombres)]
            apellido = apellidos[i % len(apellidos)]
            email = f"{nombre.lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')}.{i}@demo.com"
            
            user, created = Usuario.objects.get_or_create(
                correo=email,
                defaults={
                    'nombre': nombre,
                    'apellido': apellido,
                    'rol': Usuario.Roles.CLIENTE,
                    'activo': True
                }
            )
            
            if created:
                user.set_password('demo123')
                # Distribuir registros en los últimos 6 meses
                meses_atras = random.randint(0, 6)
                user.fecha_registro = timezone.now() - timedelta(days=meses_atras * 30 + random.randint(0, 28))
                user.save()
                counts += 1

                # Perfil
                PerfilCliente.objects.get_or_create(
                    usuario=user,
                    defaults={'peso_lbs': random.randint(130, 220), 'altura_cm': random.randint(155, 195)}
                )

                # Membresías históricas
                for m in range(meses_atras + 1):
                    p_inicio = user.fecha_registro.date() + timedelta(days=m * 30)
                    if p_inicio > timezone.now().date(): break
                    
                    plan = random.choice(list(plan_objs.values()))
                    p_fin = p_inicio + timedelta(days=plan.duracion_dias)
                    
                    estado = MembresiaCliente.Estado.ACTIVA if p_fin >= timezone.now().date() else MembresiaCliente.Estado.VENCIDA
                    
                    MembresiaCliente.objects.create(
                        usuario=user,
                        tipo=plan,
                        fecha_inicio=p_inicio,
                        fecha_fin=p_fin,
                        precio_pagado=plan.precio_mensual,
                        estado=estado
                    )

                # Mediciones
                peso_base = random.randint(170, 200)
                for m in range(meses_atras + 1):
                    f_med = (user.fecha_registro + timedelta(days=m * 30)).date()
                    if f_med > timezone.now().date(): break
                    RegistroMedidas.objects.create(
                        usuario=user,
                        fecha=f_med,
                        peso_lbs=max(120, peso_base - (m * 2) + random.uniform(-1, 1)),
                        cintura=max(60, 95 - (m * 0.5)),
                        notas=f"Control demo mes {m}"
                    )

        self.stdout.write(self.style.SUCCESS(f"Se crearon {counts} nuevos clientes con sus historiales."))
