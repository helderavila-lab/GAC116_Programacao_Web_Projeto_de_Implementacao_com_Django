import datetime
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import AgendarConsultaForm, FiltroHorariosForm
from .models import Consulta, HorarioDisponivel

STATUS_ATIVOS = [Consulta.STATUS_AGENDADA, Consulta.STATUS_CONFIRMADA]


def paciente_required(view):
    """Permite o acesso apenas a usuários logados que possuem perfil de paciente."""

    @login_required
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        perfil = getattr(request.user, 'perfil_paciente', None)
        if perfil is None:
            messages.warning(request, 'A área do paciente é exclusiva para pacientes cadastrados.')
            return redirect('usuarios:painel')
        request.paciente = perfil
        return view(request, *args, **kwargs)

    return wrapper


def _horarios_futuros():
    """Horários livres que ainda não começaram."""
    agora = timezone.localtime()
    return (
        HorarioDisponivel.objects
        .filter(disponivel=True)
        .filter(Q(data__gt=agora.date()) | Q(data=agora.date(), hora_inicio__gt=agora.time()))
        .select_related('medico__usuario', 'medico__especialidade')
    )


def _ja_comecou(horario):
    inicio = timezone.make_aware(datetime.datetime.combine(horario.data, horario.hora_inicio))
    return inicio <= timezone.now()


@paciente_required
def minhas_consultas(request):
    hoje = timezone.localdate()
    consultas = request.paciente.consultas.select_related(
        'horario__medico__usuario', 'horario__medico__especialidade',
    )
    proximas = consultas.filter(status__in=STATUS_ATIVOS, horario__data__gte=hoje).order_by(
        'horario__data', 'horario__hora_inicio',
    )
    historico = consultas.exclude(pk__in=proximas.values('pk'))
    return render(request, 'agendamento/minhas_consultas.html', {
        'proximas': proximas,
        'historico': historico,
        'total_concluidas': consultas.filter(status=Consulta.STATUS_CONCLUIDA).count(),
    })


@paciente_required
def horarios_livres(request):
    filtro = FiltroHorariosForm(request.GET or None)
    horarios = _horarios_futuros()
    if filtro.is_valid():
        if filtro.cleaned_data['especialidade']:
            horarios = horarios.filter(medico__especialidade=filtro.cleaned_data['especialidade'])
        if filtro.cleaned_data['medico']:
            horarios = horarios.filter(medico=filtro.cleaned_data['medico'])
        if filtro.cleaned_data['data']:
            horarios = horarios.filter(data=filtro.cleaned_data['data'])
    horarios = horarios.order_by('data', 'hora_inicio', 'medico__usuario__first_name')

    pagina = Paginator(horarios, 12).get_page(request.GET.get('pagina'))
    parametros = request.GET.copy()
    parametros.pop('pagina', None)
    return render(request, 'agendamento/horarios_livres.html', {
        'filtro': filtro,
        'pagina': pagina,
        'parametros': parametros.urlencode(),
    })


@paciente_required
def agendar(request, horario_id):
    horario = get_object_or_404(
        HorarioDisponivel.objects.select_related('medico__usuario', 'medico__especialidade'), pk=horario_id,
    )
    if not horario.disponivel or _ja_comecou(horario):
        messages.error(request, 'Este horário não está mais disponível. Escolha outro.')
        return redirect('agendamento:horarios_livres')

    form = AgendarConsultaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        conflito = request.paciente.consultas.filter(
            status__in=STATUS_ATIVOS,
            horario__data=horario.data,
            horario__hora_inicio__lt=horario.hora_fim,
            horario__hora_fim__gt=horario.hora_inicio,
        ).exists()
        if conflito:
            messages.error(request, 'Você já tem uma consulta marcada que coincide com este horário.')
            return redirect('agendamento:horarios_livres')

        consulta = form.save(commit=False)
        consulta.paciente = request.paciente
        consulta.horario = horario
        try:
            with transaction.atomic():
                consulta.full_clean()
                consulta.save()
        except (ValidationError, IntegrityError):
            # Outra pessoa pode ter ocupado o horário enquanto o paciente confirmava.
            messages.error(request, 'Este horário acabou de ser ocupado. Escolha outro horário.')
            return redirect('agendamento:horarios_livres')

        messages.success(
            request,
            f'Consulta agendada com {horario.medico} em {horario.data:%d/%m/%Y} às {horario.hora_inicio:%H:%M}.',
        )
        return redirect('agendamento:minhas_consultas')

    return render(request, 'agendamento/agendar.html', {'horario': horario, 'form': form})


@require_POST
@paciente_required
def cancelar(request, consulta_id):
    consulta = get_object_or_404(request.paciente.consultas.select_related('horario'), pk=consulta_id)
    if not consulta.pode_cancelar or _ja_comecou(consulta.horario):
        messages.error(request, 'Esta consulta não pode mais ser cancelada.')
    else:
        consulta.status = Consulta.STATUS_CANCELADA
        consulta.save(update_fields=['status', 'atualizado_em'])  # o sinal libera o horário
        messages.success(request, 'Consulta cancelada. O horário foi liberado para outros pacientes.')
    return redirect('agendamento:minhas_consultas')
