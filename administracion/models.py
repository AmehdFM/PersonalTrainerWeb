from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from .base import SoftDeleteQuerySet


class UsuarioManager(BaseUserManager):

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)

    def create_user(self, correo, password=None, **extra_fields):
        if not correo:
            raise ValueError('El correo electrónico es obligatorio.')
        correo = self.normalize_email(correo)
        user = self.model(correo=correo, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, correo, password=None, **extra_fields):
        extra_fields.setdefault('rol', Usuario.Roles.ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(correo, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):

    class Roles(models.TextChoices):
        ADMIN   = 'admin',  'Administrador'
        CLIENTE = 'client', 'Cliente'

    # Información personal
    nombre           = models.CharField('Nombre', max_length=100)
    apellido         = models.CharField('Apellido', max_length=100)
    correo           = models.EmailField('Correo electrónico', unique=True)
    telefono         = models.CharField('Teléfono', max_length=20, blank=True, null=True)
    fecha_nacimiento = models.DateField('Fecha de nacimiento', blank=True, null=True)
    direccion        = models.CharField('Dirección', max_length=255, blank=True, null=True)
    foto_perfil      = models.ImageField('Foto de perfil', upload_to='perfiles/', blank=True, null=True)

    # Rol y estado
    rol    = models.CharField('Rol', max_length=10, choices=Roles.choices, default=Roles.CLIENTE)
    activo = models.BooleanField('Activo', default=True)

    # Campos requeridos por Django
    is_staff  = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # Borrado lógico
    is_deleted = models.BooleanField('Borrado', default=False, db_index=True)

    # Auditoría
    fecha_registro       = models.DateTimeField('Fecha de registro', auto_now_add=True)
    ultima_actualizacion = models.DateTimeField('Última actualización', auto_now=True)

    objects     = UsuarioManager()
    all_objects = models.Manager()

    USERNAME_FIELD  = 'correo'
    REQUIRED_FIELDS = ['nombre', 'apellido']

    class Meta:
        verbose_name        = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering            = ['-fecha_registro']

    def __str__(self):
        return self.correo

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.save(update_fields=['is_deleted'])

    def restore(self):
        self.is_deleted = False
        self.save(update_fields=['is_deleted'])

    @property
    def nombre_completo(self):
        return f'{self.nombre} {self.apellido}'.strip()

    @property
    def es_admin(self):
        return self.rol == self.Roles.ADMIN

    @property
    def es_cliente(self):
        return self.rol == self.Roles.CLIENTE
