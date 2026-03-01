from django.db import models
from django.core.validators import MinValueValidator

from administracion.base import BaseModel
from administracion.models import Usuario


class Rutina(BaseModel):

    class Meta:
        verbose_name        = 'Rutina'
        verbose_name_plural = 'Rutinas'
        ordering            = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['cliente', 'activa'], name='idx_rutina_cliente_activa'),
        ]

    cliente = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='rutinas',
        limit_choices_to={'rol': Usuario.Roles.CLIENTE},
        verbose_name='Cliente',
    )
    creado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='rutinas_creadas',
        limit_choices_to={'rol': Usuario.Roles.ADMIN},
        verbose_name='Creado por',
    )
    nombre     = models.CharField('Nombre', max_length=120)
    imagen_url = models.URLField('URL de imagen', blank=True, null=True)
    activa     = models.BooleanField('Activa', default=True)

    # Opcionales: si no se asignan, la rutina es indefinida
    fecha_inicio = models.DateField('Fecha de inicio', blank=True, null=True)
    fecha_fin    = models.DateField('Fecha de fin',    blank=True, null=True)

    fecha_creacion      = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre


class DiaRutina(BaseModel):

    class DiaSemana(models.IntegerChoices):
        LUNES     = 1, 'Lunes'
        MARTES    = 2, 'Martes'
        MIERCOLES = 3, 'Miércoles'
        JUEVES    = 4, 'Jueves'
        VIERNES   = 5, 'Viernes'
        SABADO    = 6, 'Sábado'
        DOMINGO   = 7, 'Domingo'

    class Meta:
        verbose_name        = 'Día de rutina'
        verbose_name_plural = 'Días de rutina'
        ordering            = ['orden']
        unique_together     = ['rutina', 'dia_semana']

    rutina     = models.ForeignKey(Rutina, on_delete=models.CASCADE, related_name='dias')
    dia_semana = models.PositiveSmallIntegerField('Día de la semana', choices=DiaSemana.choices)
    nombre     = models.CharField('Nombre del bloque', max_length=100, blank=True)
    orden      = models.PositiveSmallIntegerField('Orden', default=0)
    notas      = models.TextField('Notas', blank=True)

    def __str__(self):
        return f'{self.rutina.nombre} - {self.get_dia_semana_display()}'


class EjercicioRutina(BaseModel):

    class TipoCarga(models.TextChoices):
        ABSOLUTO  = 'absoluto',  'Peso absoluto (lbs)'
        POR_DISCO = 'por_disco', 'Por disco (lbs por lado)'

    class Meta:
        verbose_name        = 'Ejercicio de rutina'
        verbose_name_plural = 'Ejercicios de rutina'
        ordering            = ['orden']
        indexes = [
            models.Index(fields=['ejercicio_id'], name='idx_ejercicio_ext_id'),
        ]

    dia = models.ForeignKey(DiaRutina, on_delete=models.CASCADE, related_name='ejercicios')

    # Referencia al catálogo del microservicio externo
    ejercicio_id = models.CharField('ID ejercicio (microservicio)', max_length=64, db_index=True)

    # Parámetros de ejecución
    series = models.PositiveSmallIntegerField(
        'Series',
        validators=[MinValueValidator(1)],
        default=3,
    )
    repeticiones = models.PositiveSmallIntegerField(
        'Repeticiones',
        validators=[MinValueValidator(1)],
        default=10,
    )

    # Carga
    tipo_carga         = models.CharField(
        'Tipo de carga',
        max_length=10,
        choices=TipoCarga.choices,
        default=TipoCarga.ABSOLUTO,
        help_text=(
            'Absoluto: peso total en lbs. '
            'Por disco: lbs cargados en cada lado de la barra.'
        ),
    )
    peso_lbs           = models.DecimalField(
        'Peso (lbs)',
        max_digits=6, decimal_places=2,
        blank=True, null=True,
    )
    usar_peso_corporal = models.BooleanField('Peso corporal', default=False)

    descanso_segundos = models.PositiveSmallIntegerField(
        'Descanso (seg)',
        default=60,
        validators=[MinValueValidator(0)],
    )
    tempo = models.CharField(
        'Tempo',
        max_length=20,
        blank=True,
        help_text='Formato excéntrico-pausa-concéntrico, ej: "3-1-1".',
    )
    orden = models.PositiveSmallIntegerField('Orden', default=0)
    notas = models.TextField('Notas', blank=True)

    fecha_creacion      = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.ejercicio_id}'
