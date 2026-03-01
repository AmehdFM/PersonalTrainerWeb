from django.db import models


class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet que redirige .delete() a borrado lógico."""

    def delete(self):
        return self.update(is_deleted=True)


class ActiveManager(models.Manager):
    """Manager por defecto: excluye registros borrados lógicamente."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)


class BaseModel(models.Model):
    """
    Clase base abstracta con borrado lógico.
    Todos los modelos del proyecto deben heredar de aqui.
    """

    is_deleted = models.BooleanField('Borrado', default=False, db_index=True)

    objects     = ActiveManager()   # solo registros activos
    all_objects = models.Manager()  # todos, incluyendo borrados

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Borrado lógico: marca is_deleted=True en lugar de eliminar la fila."""
        self.is_deleted = True
        self.save(update_fields=['is_deleted'])

    def restore(self):
        """Restaura un registro borrado lógicamente."""
        self.is_deleted = False
        self.save(update_fields=['is_deleted'])
