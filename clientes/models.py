from django.db import models
from django.utils import timezone

from administracion.base import BaseModel
from administracion.models import Usuario


class TipoMembresia(BaseModel):

    class Nombre(models.TextChoices):
        BASICA = 'basica', 'Básica'
        PRO    = 'pro',    'Pro'
        MAX    = 'max',    'Max'

    class Meta:
        verbose_name        = 'Tipo de membresía'
        verbose_name_plural = 'Tipos de membresía'
        ordering            = ['precio_mensual']

    nombre         = models.CharField('Plan', max_length=10, choices=Nombre.choices, unique=True)
    descripcion    = models.TextField('Descripción', blank=True)
    precio_mensual = models.DecimalField('Precio mensual (MXN)', max_digits=8, decimal_places=2)
    duracion_dias  = models.PositiveIntegerField('Duración (días)', default=30)

    acceso_clases_grupales = models.BooleanField('Clases grupales', default=False)
    acceso_areas_premium   = models.BooleanField('Áreas premium', default=False)
    acceso_nutricionista   = models.BooleanField('Nutricionista', default=False)
    numero_acompanantes    = models.PositiveSmallIntegerField('Acompañantes', default=0)

    activo              = models.BooleanField('Activo', default=True)
    fecha_creacion      = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre


class MembresiaCliente(BaseModel):

    class Estado(models.TextChoices):
        ACTIVA     = 'activa',     'Activa'
        VENCIDA    = 'vencida',    'Vencida'
        CANCELADA  = 'cancelada',  'Cancelada'
        SUSPENDIDA = 'suspendida', 'Suspendida'

    class MetodoPago(models.TextChoices):
        EFECTIVO      = 'efectivo',      'Efectivo'
        TARJETA       = 'tarjeta',       'Tarjeta'
        TRANSFERENCIA = 'transferencia', 'Transferencia'
        OTRO          = 'otro',          'Otro'

    class Meta:
        verbose_name        = 'Membresía de cliente'
        verbose_name_plural = 'Membresías de clientes'
        ordering            = ['-fecha_inicio']
        indexes = [
            models.Index(fields=['usuario', 'estado'],  name='idx_mem_usuario_estado'),
            models.Index(fields=['tipo', 'estado'],     name='idx_mem_tipo_estado'),
            models.Index(fields=['fecha_inicio'],        name='idx_mem_fecha_inicio'),
            models.Index(fields=['fecha_fin'],           name='idx_mem_fecha_fin'),
        ]

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='membresias',
        limit_choices_to={'rol': Usuario.Roles.CLIENTE},
        verbose_name='Cliente',
    )
    tipo = models.ForeignKey(
        TipoMembresia,
        on_delete=models.PROTECT,
        related_name='contrataciones',
        verbose_name='Plan',
    )

    fecha_inicio = models.DateField('Fecha de inicio')
    fecha_fin    = models.DateField('Fecha de fin')

    precio_pagado      = models.DecimalField('Precio pagado (MXN)', max_digits=8, decimal_places=2)
    descuento_aplicado = models.DecimalField('Descuento (%)', max_digits=5, decimal_places=2, default=0)
    metodo_pago        = models.CharField('Método de pago', max_length=15, choices=MetodoPago.choices, default=MetodoPago.EFECTIVO)

    estado       = models.CharField('Estado', max_length=12, choices=Estado.choices, default=Estado.ACTIVA)
    auto_renovar = models.BooleanField('Auto-renovar', default=False)
    notas        = models.TextField('Notas', blank=True)

    registrado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='membresias_registradas',
        limit_choices_to={'rol': Usuario.Roles.ADMIN},
        verbose_name='Registrado por',
    )
    fecha_registro      = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.usuario_id} - {self.tipo_id}'

    @property
    def esta_vigente(self):
        return self.estado == self.Estado.ACTIVA and self.fecha_fin >= timezone.now().date()

    @property
    def dias_restantes(self):
        return (self.fecha_fin - timezone.now().date()).days


class PerfilCliente(BaseModel):

    class Meta:
        verbose_name        = 'Perfil de cliente'
        verbose_name_plural = 'Perfiles de clientes'

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='perfil_cliente',
        limit_choices_to={'rol': Usuario.Roles.CLIENTE},
        verbose_name='Cliente',
    )
    peso_lbs  = models.DecimalField('Peso (lbs)', max_digits=5, decimal_places=2, blank=True, null=True)
    altura_cm = models.DecimalField('Altura (cm)', max_digits=5, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return str(self.usuario_id)

    @property
    def imc(self):
        """IMC calculado convirtiendo lbs → kg internamente."""
        if self.peso_lbs and self.altura_cm and self.altura_cm > 0:
            peso_kg  = float(self.peso_lbs) * 0.453592
            altura_m = float(self.altura_cm) / 100
            return round(peso_kg / (altura_m ** 2), 2)
        return None

    @property
    def membresia_activa(self):
        today = timezone.now().date()
        return (
            self.usuario.membresias
            .filter(estado=MembresiaCliente.Estado.ACTIVA, fecha_fin__gte=today)
            .select_related('tipo')
            .first()
        )

class RegistroMedidas(BaseModel):
    class Meta:
        verbose_name = 'Registro de medidas'
        verbose_name_plural = 'Registros de medidas'
        ordering = ['-fecha']

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='registros_medidas'
    )
    fecha = models.DateField(default=timezone.now)
    
    # Medidas corporales (todas en cm o lbs)
    peso_lbs = models.DecimalField('Peso (lbs)', max_digits=5, decimal_places=2)
    cuello = models.DecimalField('Cuello (cm)', max_digits=5, decimal_places=2, blank=True, null=True)
    hombros = models.DecimalField('Hombros (cm)', max_digits=5, decimal_places=2, blank=True, null=True)
    pecho = models.DecimalField('Pecho (cm)', max_digits=5, decimal_places=2, blank=True, null=True)
    cintura = models.DecimalField('Cintura (cm)', max_digits=5, decimal_places=2, blank=True, null=True)
    cadera = models.DecimalField('Cadera (cm)', max_digits=5, decimal_places=2, blank=True, null=True)
    brazo_izq = models.DecimalField('Brazo Izq (cm)', max_digits=5, decimal_places=2, blank=True, null=True)
    brazo_der = models.DecimalField('Brazo Der (cm)', max_digits=5, decimal_places=2, blank=True, null=True)
    muslo_izq = models.DecimalField('Muslo Izq (cm)', max_digits=5, decimal_places=2, blank=True, null=True)
    muslo_der = models.DecimalField('Muslo Der (cm)', max_digits=5, decimal_places=2, blank=True, null=True)
    pantorrilla_izq = models.DecimalField('Pantorrilla Izq (cm)', max_digits=5, decimal_places=2, blank=True, null=True)
    pantorrilla_der = models.DecimalField('Pantorrilla Der (cm)', max_digits=5, decimal_places=2, blank=True, null=True)

    # Datos adicionales manuales
    imc = models.DecimalField('IMC', max_digits=5, decimal_places=2, blank=True, null=True)
    porcentaje_grasa = models.DecimalField('% Grasa', max_digits=5, decimal_places=2, blank=True, null=True)

    notas = models.TextField('Notas', blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.usuario.correo} - {self.fecha}'
