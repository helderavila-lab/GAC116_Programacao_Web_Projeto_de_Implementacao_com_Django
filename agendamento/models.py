from django.core.exceptions import ValidationError
from django.db import models

from usuarios.models import PerfilMedico, PerfilPaciente


class HorarioDisponivel(models.Model):
    medico = models.ForeignKey(
        PerfilMedico, on_delete=models.CASCADE, related_name='horarios', verbose_name='Médico',
    )
    data = models.DateField()
    hora_inicio = models.TimeField('Hora de início')
    hora_fim = models.TimeField('Hora de fim')
    disponivel = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Horário disponível'
        verbose_name_plural = 'Horários disponíveis'
        ordering = ['data', 'hora_inicio']
        unique_together = ('medico', 'data', 'hora_inicio')

    def clean(self):
        if self.hora_inicio and self.hora_fim and self.hora_fim <= self.hora_inicio:
            raise ValidationError({'hora_fim': 'A hora de fim deve ser posterior à hora de início.'})

        if self.medico_id and self.data and self.hora_inicio and self.hora_fim:
            # Horários que se sobrepõem (ex.: 09:00-10:00 e 09:30-10:30) para o mesmo médico.
            # Mesma hora de início já é tratada pela restrição de unicidade.
            sobrepostos = (
                HorarioDisponivel.objects
                .filter(medico_id=self.medico_id, data=self.data,
                        hora_inicio__lt=self.hora_fim, hora_fim__gt=self.hora_inicio)
                .exclude(hora_inicio=self.hora_inicio)
                .exclude(pk=self.pk)
            )
            if sobrepostos.exists():
                raise ValidationError('Este horário se sobrepõe a outro horário do mesmo médico nesta data.')

    def __str__(self):
        return f'{self.medico} - {self.data:%d/%m/%Y} {self.hora_inicio:%H:%M}-{self.hora_fim:%H:%M}'

    def atualizar_disponibilidade(self):
        """Disponível quando não há consulta ativa (não cancelada) neste horário."""
        ocupado = self.consultas.exclude(status=Consulta.STATUS_CANCELADA).exists()
        if self.disponivel == ocupado:
            self.disponivel = not ocupado
            self.save(update_fields=['disponivel'])


class Consulta(models.Model):
    STATUS_AGENDADA = 'agendada'
    STATUS_CONFIRMADA = 'confirmada'
    STATUS_CANCELADA = 'cancelada'
    STATUS_CONCLUIDA = 'concluida'
    STATUS_CHOICES = [
        (STATUS_AGENDADA, 'Agendada'),
        (STATUS_CONFIRMADA, 'Confirmada'),
        (STATUS_CANCELADA, 'Cancelada'),
        (STATUS_CONCLUIDA, 'Concluída'),
    ]

    paciente = models.ForeignKey(PerfilPaciente, on_delete=models.CASCADE, related_name='consultas')
    # ForeignKey (e não OneToOne) para que um horário liberado por cancelamento possa ser
    # remarcado; a restrição abaixo impede duas consultas ativas no mesmo horário.
    horario = models.ForeignKey(
        HorarioDisponivel, on_delete=models.CASCADE, related_name='consultas', verbose_name='Horário',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_AGENDADA)
    motivo = models.CharField('Motivo da consulta', max_length=255, blank=True)
    observacoes = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'
        ordering = ['-horario__data', '-horario__hora_inicio']
        constraints = [
            models.UniqueConstraint(
                fields=['horario'],
                condition=~models.Q(status='cancelada'),
                name='uma_consulta_ativa_por_horario',
                violation_error_message='Este horário já possui uma consulta ativa. Escolha outro horário.',
            ),
        ]

    def clean(self):
        if not self.horario_id or self.status == self.STATUS_CANCELADA:
            return
        horario_anterior_id = None
        if self.pk:
            horario_anterior_id = (
                Consulta.objects.filter(pk=self.pk).values_list('horario_id', flat=True).first()
            )
        if self.horario_id == horario_anterior_id:
            return
        horario = self.horario
        ocupado = horario.consultas.exclude(status=self.STATUS_CANCELADA).exclude(pk=self.pk).exists()
        # Se estiver ocupado por outra consulta, a restrição de unicidade já informa o erro.
        if not horario.disponivel and not ocupado:
            raise ValidationError({'horario': 'Este horário está marcado como indisponível.'})

    def validate_constraints(self, exclude=None):
        # Quando 'horario' não está no formulário (ex.: médico editando só o status),
        # o Django pularia a restrição e o banco geraria erro 500 ao reativar uma
        # consulta cujo horário já foi ocupado. Valida sempre.
        if exclude:
            exclude = set(exclude) - {'horario', 'status'}
        super().validate_constraints(exclude=exclude)

    @property
    def pode_cancelar(self):
        return self.status in (self.STATUS_AGENDADA, self.STATUS_CONFIRMADA)

    def __str__(self):
        return f'Consulta de {self.paciente} em {self.horario.data:%d/%m/%Y}'

    @property
    def medico(self):
        return self.horario.medico
