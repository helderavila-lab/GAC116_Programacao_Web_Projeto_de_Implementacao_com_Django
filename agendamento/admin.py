from django.contrib import admin
from django.utils import timezone

from usuarios.models import PerfilMedico

from .models import Consulta, HorarioDisponivel


def _perfil_medico(request):
    """Retorna o perfil de médico do usuário logado (exceto superusuários), ou None."""
    if request.user.is_superuser:
        return None
    return getattr(request.user, 'perfil_medico', None)


@admin.register(HorarioDisponivel)
class HorarioDisponivelAdmin(admin.ModelAdmin):
    list_display = ('medico', 'data', 'hora_inicio', 'hora_fim', 'disponivel')
    list_filter = ('disponivel', 'medico__especialidade', 'medico', 'data')
    search_fields = ('medico__usuario__first_name', 'medico__usuario__last_name')
    date_hierarchy = 'data'
    autocomplete_fields = ('medico',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        medico = _perfil_medico(request)
        if medico:
            queryset = queryset.filter(medico=medico)
        return queryset

    def get_autocomplete_fields(self, request):
        if _perfil_medico(request):
            return ()
        return super().get_autocomplete_fields(request)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        medico = _perfil_medico(request)
        if medico and db_field.name == 'medico':
            # Médicos só cadastram horários para si mesmos: o campo aparece preenchido e
            # bloqueado (continua no formulário para validar horários repetidos).
            kwargs['queryset'] = PerfilMedico.objects.filter(pk=medico.pk)
            kwargs['initial'] = medico
            kwargs['disabled'] = True
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_list_filter(self, request):
        if _perfil_medico(request):
            return ('disponivel', 'data')
        return super().get_list_filter(request)

    def get_search_results(self, request, queryset, search_term):
        queryset, may_have_duplicates = super().get_search_results(request, queryset, search_term)
        # No campo "horário" da consulta, sugere apenas horários livres a partir de hoje.
        if request.GET.get('model_name') == 'consulta' and request.GET.get('field_name') == 'horario':
            queryset = queryset.filter(disponivel=True, data__gte=timezone.localdate())
        return queryset, may_have_duplicates

    def save_model(self, request, obj, form, change):
        medico = _perfil_medico(request)
        if medico:
            obj.medico = medico
        super().save_model(request, obj, form, change)


@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'exibir_medico', 'exibir_data', 'status')
    list_filter = ('status', 'horario__medico__especialidade', 'horario__medico')
    search_fields = (
        'paciente__usuario__first_name', 'paciente__usuario__last_name',
        'horario__medico__usuario__first_name', 'horario__medico__usuario__last_name',
    )
    date_hierarchy = 'horario__data'
    autocomplete_fields = ('paciente', 'horario')
    list_editable = ('status',)

    # A disponibilidade do horário é sincronizada por sinais (agendamento/signals.py),
    # inclusive em exclusões em massa e troca de horário.

    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related('horario__medico__usuario', 'paciente__usuario')
        medico = _perfil_medico(request)
        if medico:
            queryset = queryset.filter(horario__medico=medico)
        return queryset

    def get_list_filter(self, request):
        if _perfil_medico(request):
            return ('status',)
        return super().get_list_filter(request)

    def get_readonly_fields(self, request, obj=None):
        # Médicos apenas atualizam status e observações das suas consultas.
        if _perfil_medico(request):
            return ('paciente', 'horario', 'motivo')
        return super().get_readonly_fields(request, obj)

    @admin.display(description='Médico')
    def exibir_medico(self, obj):
        return obj.horario.medico

    @admin.display(description='Data/Hora')
    def exibir_data(self, obj):
        return f'{obj.horario.data:%d/%m/%Y} {obj.horario.hora_inicio:%H:%M}'
