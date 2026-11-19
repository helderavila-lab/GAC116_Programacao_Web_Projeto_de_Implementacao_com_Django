"""Testes da área do paciente: horários livres, agendamento e cancelamento."""
import datetime
import io

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from usuarios.models import PerfilPaciente

from .models import Consulta, HorarioDisponivel


class AreaPacienteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_dados', stdout=io.StringIO())

    def setUp(self):
        self.paciente = PerfilPaciente.objects.get(usuario__username='paciente')
        Consulta.objects.all().delete()
        self.horario = HorarioDisponivel.objects.filter(
            medico__usuario__username='dra.ana', disponivel=True,
        ).order_by('data', 'hora_inicio').first()
        self.client.login(username='paciente', password='paciente12345')

    def test_area_do_paciente_exige_login(self):
        self.client.logout()
        url = reverse('agendamento:horarios_livres')
        self.assertRedirects(self.client.get(url), reverse('usuarios:entrar') + '?next=' + url)

    def test_equipe_nao_usa_area_do_paciente(self):
        self.client.login(username='recepcao', password='recepcao12345')
        resposta = self.client.get(reverse('agendamento:minhas_consultas'))
        self.assertRedirects(resposta, reverse('usuarios:painel'), fetch_redirect_response=False)

    def test_lista_e_filtra_horarios_livres(self):
        resposta = self.client.get(reverse('agendamento:horarios_livres'),
                                   {'medico': self.horario.medico_id, 'data': self.horario.data.isoformat()})
        self.assertEqual(resposta.status_code, 200)
        horarios = list(resposta.context['pagina'])
        self.assertIn(self.horario, horarios)
        self.assertTrue(all(h.medico_id == self.horario.medico_id for h in horarios))

    def test_paciente_agenda_consulta(self):
        resposta = self.client.post(reverse('agendamento:agendar', args=[self.horario.pk]), {'motivo': 'Rotina'})
        self.assertRedirects(resposta, reverse('agendamento:minhas_consultas'))
        consulta = Consulta.objects.get()
        self.assertEqual(consulta.paciente, self.paciente)
        self.assertEqual(consulta.motivo, 'Rotina')
        self.horario.refresh_from_db()
        self.assertFalse(self.horario.disponivel)
        # O horário ocupado some da lista de horários livres.
        resposta = self.client.get(reverse('agendamento:horarios_livres'))
        self.assertNotIn(self.horario, resposta.context['pagina'].paginator.object_list)

    def test_nao_agenda_horario_ocupado(self):
        Consulta.objects.create(paciente=self.paciente, horario=self.horario)
        resposta = self.client.post(reverse('agendamento:agendar', args=[self.horario.pk]), {'motivo': ''})
        self.assertRedirects(resposta, reverse('agendamento:horarios_livres'))
        self.assertEqual(Consulta.objects.count(), 1)

    def test_nao_agenda_horario_passado(self):
        ontem = timezone.localdate() - datetime.timedelta(days=1)
        passado = HorarioDisponivel.objects.create(
            medico=self.horario.medico, data=ontem, hora_inicio=datetime.time(9), hora_fim=datetime.time(9, 30),
        )
        resposta = self.client.post(reverse('agendamento:agendar', args=[passado.pk]), {'motivo': ''})
        self.assertRedirects(resposta, reverse('agendamento:horarios_livres'))
        self.assertFalse(Consulta.objects.exists())

    def test_nao_agenda_duas_consultas_no_mesmo_horario(self):
        Consulta.objects.create(paciente=self.paciente, horario=self.horario)
        outro = HorarioDisponivel.objects.filter(
            data=self.horario.data, hora_inicio=self.horario.hora_inicio, disponivel=True,
        ).exclude(medico=self.horario.medico).first()
        resposta = self.client.post(reverse('agendamento:agendar', args=[outro.pk]), {'motivo': ''})
        self.assertRedirects(resposta, reverse('agendamento:horarios_livres'))
        self.assertEqual(Consulta.objects.count(), 1)

    def test_paciente_cancela_e_libera_horario(self):
        consulta = Consulta.objects.create(paciente=self.paciente, horario=self.horario)
        self.assertEqual(self.client.get(reverse('agendamento:cancelar', args=[consulta.pk])).status_code, 405)
        resposta = self.client.post(reverse('agendamento:cancelar', args=[consulta.pk]))
        self.assertRedirects(resposta, reverse('agendamento:minhas_consultas'))
        consulta.refresh_from_db()
        self.horario.refresh_from_db()
        self.assertEqual(consulta.status, Consulta.STATUS_CANCELADA)
        self.assertTrue(self.horario.disponivel)

    def test_paciente_nao_cancela_consulta_de_outro(self):
        from django.contrib.auth.models import User
        outro = PerfilPaciente.objects.create(
            usuario=User.objects.create_user('outro', password='SenhaForte!2026'), cpf='111',
        )
        consulta = Consulta.objects.create(paciente=outro, horario=self.horario)
        resposta = self.client.post(reverse('agendamento:cancelar', args=[consulta.pk]))
        self.assertEqual(resposta.status_code, 404)

    def test_minhas_consultas_mostra_proximas(self):
        Consulta.objects.create(paciente=self.paciente, horario=self.horario, motivo='Check-up')
        resposta = self.client.get(reverse('agendamento:minhas_consultas'))
        self.assertContains(resposta, 'Check-up')
        self.assertContains(resposta, 'Cancelar consulta')
