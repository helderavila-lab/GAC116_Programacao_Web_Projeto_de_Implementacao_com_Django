import io

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Especialidade, PerfilPaciente


class CadastroPerfisTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_dados', stdout=io.StringIO())

    def test_recepcionista_cadastra_paciente_com_usuario(self):
        self.client.login(username='recepcao', password='recepcao12345')
        resposta = self.client.post(reverse('admin:usuarios_perfilpaciente_add'), {
            'first_name': 'Maria', 'last_name': 'Silva', 'username': 'maria.silva',
            'email': 'maria@exemplo.com', 'password': 'SenhaForte!2026',
            'cpf': '111.222.333-44', 'telefone': '(35) 99999-0000', 'endereco': '',
            'data_nascimento': '',
        })
        self.assertEqual(resposta.status_code, 302)
        paciente = PerfilPaciente.objects.get(cpf='111.222.333-44')
        self.assertEqual(paciente.usuario.username, 'maria.silva')
        self.assertTrue(paciente.usuario.check_password('SenhaForte!2026'))
        self.assertFalse(paciente.usuario.is_staff)
        self.assertTrue(paciente.usuario.groups.filter(name='Pacientes').exists())

    def test_cadastro_exige_senha_e_usuario_unico(self):
        self.client.login(username='recepcao', password='recepcao12345')
        resposta = self.client.post(reverse('admin:usuarios_perfilpaciente_add'), {
            'first_name': 'Outro', 'username': 'paciente', 'password': '', 'cpf': '999',
        })
        self.assertEqual(resposta.status_code, 200)
        erros = resposta.context['adminform'].form.errors
        self.assertIn('username', erros)
        self.assertIn('password', erros)

    def test_editar_paciente_sem_trocar_senha(self):
        self.client.login(username='recepcao', password='recepcao12345')
        paciente = PerfilPaciente.objects.get(usuario__username='paciente')
        resposta = self.client.post(reverse('admin:usuarios_perfilpaciente_change', args=[paciente.pk]), {
            'first_name': 'João Carlos', 'last_name': 'Pereira', 'username': 'paciente',
            'email': '', 'password': '', 'cpf': paciente.cpf, 'telefone': '', 'endereco': '',
            'data_nascimento': '',
        })
        self.assertEqual(resposta.status_code, 302)
        usuario = User.objects.get(username='paciente')
        self.assertEqual(usuario.first_name, 'João Carlos')
        self.assertTrue(usuario.check_password('paciente12345'))

    def test_medico_apenas_visualiza_paciente(self):
        self.client.login(username='dra.ana', password='medico12345')
        paciente = PerfilPaciente.objects.get(usuario__username='paciente')
        resposta = self.client.get(reverse('admin:usuarios_perfilpaciente_change', args=[paciente.pk]))
        self.assertEqual(resposta.status_code, 200)
        self.assertNotContains(resposta, 'name="password"')

    def test_superusuario_cadastra_medico(self):
        self.client.login(username='admin', password='admin12345')
        resposta = self.client.post(reverse('admin:usuarios_perfilmedico_add'), {
            'first_name': 'Bruno', 'last_name': 'Alves', 'username': 'dr.bruno', 'email': '',
            'password': 'SenhaForte!2026', 'crm': 'CRM-99999', 'especialidade': Especialidade.objects.first().pk,
            'telefone': '', 'biografia': '',
        })
        self.assertEqual(resposta.status_code, 302)
        usuario = User.objects.get(username='dr.bruno')
        self.assertTrue(usuario.is_staff)
        self.assertTrue(usuario.groups.filter(name='Médicos').exists())
