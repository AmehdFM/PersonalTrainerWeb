from django.contrib import admin
from django.utils.html import format_html

from .models import TipoMembresia, MembresiaCliente, PerfilCliente


@admin.register(TipoMembresia)
class TipoMembresiaAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'precio_mensual', 'duracion_dias', 'acceso_clases_grupales', 'acceso_areas_premium', 'acceso_nutricionista', 'activo', 'is_deleted')
    list_filter   = ('activo', 'is_deleted')
    ordering      = ('precio_mensual',)

    fieldsets = (
        (None, {'fields': ('nombre', 'descripcion', 'precio_mensual', 'duracion_dias', 'activo', 'is_deleted')}),
        ('Beneficios', {'fields': ('acceso_clases_grupales', 'acceso_areas_premium', 'acceso_nutricionista', 'numero_acompanantes')}),
    )


@admin.register(MembresiaCliente)
class MembresiaClienteAdmin(admin.ModelAdmin):
    list_display    = ('usuario', 'tipo', 'estado', 'fecha_inicio', 'fecha_fin', 'precio_pagado', 'metodo_pago', 'is_deleted')
    list_filter     = ('estado', 'tipo__nombre', 'metodo_pago', 'is_deleted')
    search_fields   = ('usuario__correo', 'usuario__nombre', 'usuario__apellido')
    ordering        = ('-fecha_inicio',)
    date_hierarchy  = 'fecha_inicio'
    autocomplete_fields = ('usuario', 'registrado_por')
    readonly_fields = ('fecha_registro', 'fecha_actualizacion')

    fieldsets = (
        ('Cliente y Plan', {'fields': ('usuario', 'tipo')}),
        ('Vigencia', {'fields': ('fecha_inicio', 'fecha_fin', 'estado', 'auto_renovar')}),
        ('Pago', {'fields': ('precio_pagado', 'descuento_aplicado', 'metodo_pago')}),
        ('Administración', {'fields': ('registrado_por', 'notas', 'is_deleted', 'fecha_registro', 'fecha_actualizacion'), 'classes': ('collapse',)}),
    )

    @admin.display(description='Vigente', boolean=True)
    def estado_vigencia(self, obj):
        return obj.esta_vigente


@admin.register(PerfilCliente)
class PerfilClienteAdmin(admin.ModelAdmin):
    list_display  = ('usuario', 'peso_lbs', 'altura_cm', 'get_imc', 'is_deleted')
    search_fields = ('usuario__correo', 'usuario__nombre', 'usuario__apellido')
    list_filter   = ('is_deleted',)
    autocomplete_fields = ('usuario',)

    @admin.display(description='IMC')
    def get_imc(self, obj):
        imc = obj.imc
        if imc is None:
            return '—'
        if imc < 18.5:
            color = '#3b82f6'
        elif imc < 25:
            color = '#22c55e'
        elif imc < 30:
            color = '#f59e0b'
        else:
            color = '#ef4444'
        return format_html('<b style="color:{}">{}</b>', color, imc)
