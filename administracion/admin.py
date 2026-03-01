from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model         = Usuario
    list_display  = ('correo', 'nombre', 'apellido', 'rol', 'activo', 'is_deleted', 'fecha_registro')
    list_filter   = ('rol', 'activo', 'is_deleted', 'is_staff')
    search_fields = ('correo', 'nombre', 'apellido')
    ordering      = ('-fecha_registro',)
    readonly_fields = ('fecha_registro', 'ultima_actualizacion')

    fieldsets = (
        (None, {'fields': ('correo', 'password')}),
        (_('Información Personal'), {
            'fields': ('nombre', 'apellido', 'telefono', 'fecha_nacimiento', 'direccion', 'foto_perfil')
        }),
        (_('Rol y Estado'), {'fields': ('rol', 'activo', 'is_staff', 'is_superuser', 'is_deleted')}),
        (_('Permisos'), {'fields': ('groups', 'user_permissions'), 'classes': ('collapse',)}),
        (_('Fechas'), {'fields': ('fecha_registro', 'ultima_actualizacion', 'last_login')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('correo', 'nombre', 'apellido', 'rol', 'password1', 'password2'),
        }),
    )
