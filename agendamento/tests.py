import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from usuarios.models import Especialidade, PerfilMedico

from .models import Consulta, HorarioDisponivel


class AdminAgendamentoTests(TestCase):
    def setUp(self):
        especialidade = Especialidade.objects.create(nome='Cardiologia')
        self.medico = PerfilMedico.objects.create(
            usuario=User.objects.create_user('medico', password='senha12345'),
            crm='123', especialidade=especialidade,
        )
        self.outro_medico = PerfilMedico.objects.create(
            usuario=User.objects.create_user('outro', password='senha12345'),
            crm='456', especialidade=especialidade,
        )
        amanha = timezone.localdate() + datetime.timedelta(days=1)
        self.horario = HorarioDisponivel.objects.create(
            medico=self.medico, data=amanha,
            hora_inicio=datetime.time(9), hora_fim=datetime.time(10),
        )
        self.horario_outro = HorarioDisponivel.objects.create(
            medico=self.outro_medico, data=amanha,
            hora_inicio=datetime.time(9), hora_fim=datetime.time(10),
        )

    def test_medico_ve_apenas_os_proprios_horarios_no_admin(self):
        self.client.force_login(self.medico.usuario)
        resposta = self.client.get(reverse('admin:agendamento_horariodisponivel_changelist'))

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(list(resposta.context['cl'].queryset), [self.horario])

    def test_medico_nao_acessa_horario_de_outro_medico(self):
        self.client.force_login(self.medico.usuario)
        resposta = self.client.get(
            reverse('admin:agendamento_horariodisponivel_change', args=[self.horario_outro.id]),
        )
        self.assertNotEqual(resposta.status_code, 200)


class RegrasAgendamentoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        import io
        from django.core.management import call_command
        call_command('seed_dados', stdout=io.StringIO())

    def setUp(self):
        from usuarios.models import PerfilPaciente
        self.paciente = PerfilPaciente.objects.get(usuario__username='paciente')
        self.horarios = list(HorarioDisponivel.objects.filter(medico__usuario__username='dra.ana')[:2])

    def _dados_consulta(self, horario, status='agendada'):
        return {'paciente': self.paciente.pk, 'horario': horario.pk, 'status': status,
                'motivo': '', 'observacoes': ''}

    def test_medico_horario_repetido_mostra_erro_e_nao_500(self):
        self.client.login(username='dra.ana', password='medico12345')
        h = self.horarios[0]
        resposta = self.client.post(reverse('admin:agendamento_horariodisponivel_add'), {
            'data': h.data.isoformat(), 'hora_inicio': h.hora_inicio.strftime('%H:%M'),
            'hora_fim': '23:00', 'disponivel': 'on',
        })
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.context['adminform'].form.errors)

    def test_medico_cadastra_horario_para_si(self):
        self.client.login(username='dra.ana', password='medico12345')
        h = self.horarios[0]
        resposta = self.client.post(reverse('admin:agendamento_horariodisponivel_add'), {
            'data': h.data.isoformat(), 'hora_inicio': '17:00', 'hora_fim': '17:30',
            'disponivel': 'on', 'medico': PerfilMedico.objects.exclude(pk=h.medico_id).first().pk,
        })
        self.assertEqual(resposta.status_code, 302)
        novo = HorarioDisponivel.objects.get(data=h.data, hora_inicio=datetime.time(17))
        self.assertEqual(novo.medico, h.medico)

    def test_horario_sobreposto_e_rejeitado(self):
        self.client.login(username='admin', password='admin12345')
        h = self.horarios[0]  # 09:00-09:30
        resposta = self.client.post(reverse('admin:agendamento_horariodisponivel_add'), {
            'medico': h.medico_id, 'data': h.data.isoformat(), 'hora_inicio': '09:15',
            'hora_fim': '09:45', 'disponivel': 'on',
        })
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'se sobrepõe')

    def test_marcacao_dupla_tem_mensagem_clara(self):
        self.client.login(username='recepcao', password='recepcao12345')
        url = reverse('admin:agendamento_consulta_add')
        self.assertEqual(self.client.post(url, self._dados_consulta(self.horarios[0])).status_code, 302)
        resposta = self.client.post(url, self._dados_consulta(self.horarios[0]))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'já possui uma consulta ativa')
        self.assertEqual(Consulta.objects.count(), 1)

    def test_trocar_horario_libera_o_anterior(self):
        self.client.login(username='recepcao', password='recepcao12345')
        h1, h2 = self.horarios
        self.client.post(reverse('admin:agendamento_consulta_add'), self._dados_consulta(h1))
        consulta = Consulta.objects.get()
        h1.refresh_from_db()
        self.assertFalse(h1.disponivel)
        resposta = self.client.post(
            reverse('admin:agendamento_consulta_change', args=[consulta.pk]), self._dados_consulta(h2),
        )
        self.assertEqual(resposta.status_code, 302)
        h1.refresh_from_db()
        h2.refresh_from_db()
        self.assertTrue(h1.disponivel)
        self.assertFalse(h2.disponivel)

    def test_cancelar_e_excluir_liberam_horario(self):
        h = self.horarios[0]
        consulta = Consulta.objects.create(paciente=self.paciente, horario=h)
        h.refresh_from_db()
        self.assertFalse(h.disponivel)
        consulta.status = Consulta.STATUS_CANCELADA
        consulta.save()
        h.refresh_from_db()
        self.assertTrue(h.disponivel)
        # Uma consulta cancelada excluída não libera horário ocupado por outra ativa.
        Consulta.objects.create(paciente=self.paciente, horario=h)
        Consulta.objects.filter(pk=consulta.pk).delete()
        h.refresh_from_db()
        self.assertFalse(h.disponivel)

    def test_nao_agenda_em_horario_indisponivel(self):
        h = self.horarios[0]
        h.disponivel = False
        h.save()
        self.client.login(username='recepcao', password='recepcao12345')
        resposta = self.client.post(reverse('admin:agendamento_consulta_add'), self._dados_consulta(h))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'marcado como indisponível')

    def test_medico_reativar_consulta_em_horario_ocupado_nao_gera_500(self):
        h = self.horarios[0]
        cancelada = Consulta.objects.create(paciente=self.paciente, horario=h, status='cancelada')
        Consulta.objects.create(paciente=self.paciente, horario=h)
        self.client.login(username='dra.ana', password='medico12345')
        resposta = self.client.post(
            reverse('admin:agendamento_consulta_change', args=[cancelada.pk]),
            {'status': 'agendada', 'observacoes': ''},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'já possui uma consulta ativa')

    def test_autocomplete_de_horario_mostra_apenas_livres(self):
        h = self.horarios[0]
        Consulta.objects.create(paciente=self.paciente, horario=h)
        self.client.login(username='recepcao', password='recepcao12345')
        resposta = self.client.get(reverse('admin:autocomplete'), {
            'app_label': 'agendamento', 'model_name': 'consulta', 'field_name': 'horario', 'term': '',
        })
        self.assertEqual(resposta.status_code, 200)
        ids = [int(r['id']) for r in resposta.json()['results']]
        self.assertNotIn(h.pk, ids)
        self.assertIn(self.horarios[1].pk, ids)

    def test_seletor_de_tema_claro_escuro_visivel(self):
        self.client.login(username='admin', password='admin12345')
        self.assertContains(self.client.get(reverse('admin:index')), 'jazzmin-mode-select')
