from django.contrib import admin
from .models import Rutina, DiaRutina, EjercicioRutina


class EjercicioRutinaInline(admin.TabularInline):
    model   = EjercicioRutina
    extra   = 1
    ordering = ['orden']
    fields  = (
        'orden', 'ejercicio_id',
        'series', 'repeticiones',
        'tipo_carga', 'peso_lbs', 'usar_peso_corporal',
        'descanso_segundos', 'tempo', 'notas',
    )


class DiaRutinaInline(admin.StackedInline):
    model           = DiaRutina
    extra           = 1
    ordering        = ['orden']
    fields          = ('orden', 'dia_semana', 'notas')
    show_change_link = True


@admin.register(Rutina)
class RutinaAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'cliente', 'creado_por', 'activa', 'fecha_inicio', 'fecha_fin', 'is_deleted')
    list_filter   = ('activa', 'is_deleted')
    search_fields = ('nombre', 'cliente__correo', 'cliente__nombre', 'cliente__apellido')
    autocomplete_fields = ('cliente', 'creado_por')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    ordering  = ('-fecha_creacion',)
    inlines   = [DiaRutinaInline]

    fieldsets = (
        (None, {'fields': ('nombre', 'imagen_url', 'activa', 'is_deleted')}),
        ('Asignación', {'fields': ('cliente', 'creado_por')}),
        ('Período', {'fields': ('fecha_inicio', 'fecha_fin'), 'classes': ('collapse',)}),
        ('Auditoría', {'fields': ('fecha_creacion', 'fecha_actualizacion'), 'classes': ('collapse',)}),
    )


@admin.register(DiaRutina)
class DiaRutinaAdmin(admin.ModelAdmin):
    list_display  = ('id', 'rutina', 'dia_semana', 'orden', 'is_deleted')
    list_filter   = ('is_deleted', 'dia_semana')
    search_fields = ('rutina__nombre', 'rutina__cliente__nombre')
    ordering      = ('rutina', 'orden')
    inlines       = [EjercicioRutinaInline]


@admin.register(EjercicioRutina)
class EjercicioRutinaAdmin(admin.ModelAdmin):
    list_display  = ('id', 'ejercicio_id', 'dia', 'series', 'repeticiones', 'tipo_carga', 'peso_lbs', 'descanso_segundos', 'orden', 'is_deleted')
    list_filter   = ('tipo_carga', 'usar_peso_corporal', 'is_deleted')
    search_fields = ('ejercicio_id', 'dia__rutina__nombre', 'dia__rutina__cliente__nombre')
    ordering      = ('dia__rutina', 'dia__orden', 'orden')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
