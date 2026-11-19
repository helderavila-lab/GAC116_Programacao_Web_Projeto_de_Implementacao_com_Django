"""Testes do site: página inicial, login, logout, cadastro e dados do paciente."""
import io

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .forms import validar_cpf
from .models import PerfilPaciente

DADOS_CADASTRO = {
    'first_name': 'Maria', 'last_name': 'Silva', 'cpf': '529.982.247-25',
    'data_nascimento': '1990-05-10', 'telefone': '(35) 99999-0000', 'endereco': 'Rua A, 10',
    'email': 'maria@exemplo.com', 'username': 'maria', 'password': 'SenhaForte!2026',
    'password2': 'SenhaForte!2026',
}


class SiteAutenticacaoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_dados', stdout=io.StringIO())

    def test_pagina_inicial_publica(self):
        resposta = self.client.get(reverse('inicio'))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Cardiologia')
        self.assertContains(resposta, 'Cadastre-se')
        self.assertContains(resposta, 'bootstrap')

    def test_cadastro_cria_paciente_e_faz_login(self):
        resposta = self.client.post(reverse('usuarios:cadastro'), DADOS_CADASTRO)
        self.assertRedirects(resposta, reverse('agendamento:minhas_consultas'))
        paciente = PerfilPaciente.objects.get(usuario__username='maria')
        self.assertEqual(paciente.cpf, '529.982.247-25')
        self.assertFalse(paciente.usuario.is_staff)
        self.assertTrue(paciente.usuario.groups.filter(name='Pacientes').exists())
        # Já está logado após o cadastro.
        self.assertEqual(self.client.get(reverse('agendamento:minhas_consultas')).status_code, 200)

    def test_cadastro_valida_senhas_cpf_e_email(self):
        dados = dict(DADOS_CADASTRO, password2='OutraSenha!2026', cpf='123.456.789-00',
                     email='paciente@exemplo.com')
        resposta = self.client.post(reverse('usuarios:cadastro'), dados)
        self.assertEqual(resposta.status_code, 200)
        erros = resposta.context['form'].errors
        self.assertIn('password2', erros)
        self.assertIn('cpf', erros)
        self.assertIn('email', erros)
        self.assertFalse(User.objects.filter(username='maria').exists())

    def test_cadastro_recusa_nascimento_no_futuro(self):
        dados = dict(DADOS_CADASTRO, data_nascimento='2999-01-01')
        resposta = self.client.post(reverse('usuarios:cadastro'), dados)
        self.assertEqual(resposta.status_code, 200)
        self.assertIn('data_nascimento', resposta.context['form'].errors)

    def test_validar_cpf_formata(self):
        self.assertEqual(validar_cpf('52998224725'), '529.982.247-25')

    def test_login_paciente_vai_para_area_do_paciente(self):
        resposta = self.client.post(reverse('usuarios:entrar'),
                                    {'username': 'paciente', 'password': 'paciente12345'}, follow=True)
        self.assertRedirects(resposta, reverse('agendamento:minhas_consultas'))

    def test_login_equipe_vai_para_o_admin(self):
        resposta = self.client.post(reverse('usuarios:entrar'),
                                    {'username': 'recepcao', 'password': 'recepcao12345'})
        self.assertRedirects(resposta, reverse('usuarios:painel'), fetch_redirect_response=False)
        self.assertRedirects(self.client.get(reverse('usuarios:painel')), reverse('admin:index'))

    def test_login_com_senha_errada(self):
        resposta = self.client.post(reverse('usuarios:entrar'), {'username': 'paciente', 'password': 'errada'})
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(resposta.context['form'].is_valid())

    def test_logout(self):
        self.client.login(username='paciente', password='paciente12345')
        resposta = self.client.post(reverse('usuarios:sair'))
        self.assertRedirects(resposta, reverse('inicio'))
        resposta = self.client.get(reverse('agendamento:minhas_consultas'))
        self.assertRedirects(resposta, reverse('usuarios:entrar') + '?next=' + reverse('agendamento:minhas_consultas'))

    def test_paciente_edita_os_proprios_dados(self):
        self.client.login(username='paciente', password='paciente12345')
        resposta = self.client.post(reverse('usuarios:meus_dados'), {
            'first_name': 'João', 'last_name': 'Pereira Lima', 'email': 'joao@exemplo.com',
            'data_nascimento': '', 'telefone': '(34) 98888-0000', 'endereco': 'Rua B',
        })
        self.assertRedirects(resposta, reverse('usuarios:meus_dados'))
        paciente = PerfilPaciente.objects.get(usuario__username='paciente')
        self.assertEqual(paciente.usuario.last_name, 'Pereira Lima')
        self.assertEqual(paciente.telefone, '(34) 98888-0000')
