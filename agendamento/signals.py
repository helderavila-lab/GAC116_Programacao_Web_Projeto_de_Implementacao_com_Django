from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .models import Consulta, HorarioDisponivel


def _atualizar_horario(horario_id):
    horario = HorarioDisponivel.objects.filter(pk=horario_id).first()
    if horario:
        horario.atualizar_disponibilidade()


@receiver(pre_save, sender=Consulta)
def guardar_horario_anterior(sender, instance, **kwargs):
    instance._horario_anterior_id = None
    if instance.pk:
        instance._horario_anterior_id = (
            Consulta.objects.filter(pk=instance.pk).values_list('horario_id', flat=True).first()
        )


@receiver(post_save, sender=Consulta)
def sincronizar_disponibilidade_ao_salvar(sender, instance, **kwargs):
    """Mantém o campo 'disponivel' do horário coerente com as consultas (vale para
    admin, edição em lista e qualquer outro ponto do sistema)."""
    _atualizar_horario(instance.horario_id)
    anterior = getattr(instance, '_horario_anterior_id', None)
    if anterior and anterior != instance.horario_id:
        _atualizar_horario(anterior)


@receiver(post_delete, sender=Consulta)
def sincronizar_disponibilidade_ao_excluir(sender, instance, **kwargs):
    _atualizar_horario(instance.horario_id)
