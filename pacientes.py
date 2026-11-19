"""
Popula o banco com pacientes e consultas de exemplo para a apresentação.

Como usar (na pasta do projeto, com o ambiente virtual ativado):
    python pacientes.py

- Roda o seed_dados antes (médicos, horários, admin, recepção...).
- Pode ser rodado mais de uma vez: não duplica pacientes nem consultas.
- Todos os pacientes criados usam a senha: paciente12345
"""
import datetime
import os
import sys

# A pasta do projeto é a mesma deste arquivo (onde fica o manage.py).
projeto = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, projeto)
os.chdir(projeto)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinica.settings')

import django  # noqa: E402

django.setup()

from django.contrib.auth.models import User  # noqa: E402
from django.core.management import call_command  # noqa: E402
from django.utils import timezone  # noqa: E402

from agendamento.models import Consulta, HorarioDisponivel  # noqa: E402
from usuarios.models import PerfilMedico, PerfilPaciente  # noqa: E402

SENHA = 'paciente12345'


def gerar_cpf(base9):
    """Completa 9 dígitos com os dígitos verificadores e devolve 000.000.000-00."""
    d = [int(c) for c in base9]
    for tamanho in (9, 10):
        soma = sum(n * p for n, p in zip(d, range(tamanho + 1, 1, -1)))
        d.append((soma * 10) % 11 % 10)
    s = ''.join(map(str, d))
    return f'{s[:3]}.{s[3:6]}.{s[6:9]}-{s[9:]}'


PACIENTES = [
    # usuário, nome, sobrenome, base do CPF, nascimento, telefone, endereço
    ('maria.silva', 'Maria', 'Silva', '123456789', datetime.date(1985, 3, 12), '(35) 99811-2233', 'Rua das Flores, 120 - Lavras/MG'),
    ('pedro.santos', 'Pedro', 'Santos', '234567891', datetime.date(1992, 7, 25), '(35) 99722-3344', 'Av. Dr. Sílvio Menicucci, 455 - Lavras/MG'),
    ('juliana.costa', 'Juliana', 'Costa', '345678912', datetime.date(2001, 11, 3), '(35) 99633-4455', 'Rua Santana, 78 - Lavras/MG'),
    ('roberto.almeida', 'Roberto', 'Almeida', '456789123', datetime.date(1968, 1, 30), '(35) 99544-5566', 'Rua Costa Pereira, 300 - Lavras/MG'),
    ('fernanda.lima', 'Fernanda', 'Lima', '567891234', datetime.date(1979, 9, 18), '(35) 99455-6677', 'Praça Dr. Augusto Silva, 15 - Lavras/MG'),
    ('lucas.oliveira', 'Lucas', 'Oliveira', '678912345', datetime.date(2015, 5, 8), '(35) 99366-7788', 'Rua Francisco Sales, 52 - Lavras/MG'),
]


def criar_pacientes():
    perfis = {}
    for usuario_nome, nome, sobrenome, base_cpf, nascimento, telefone, endereco in PACIENTES:
        usuario, criado = User.objects.get_or_create(
            username=usuario_nome,
            defaults={'first_name': nome, 'last_name': sobrenome, 'email': f'{usuario_nome}@exemplo.com'},
        )
        if criado:
            usuario.set_password(SENHA)
            usuario.save()
        perfil, _ = PerfilPaciente.objects.get_or_create(
            usuario=usuario,
            defaults={'cpf': gerar_cpf(base_cpf), 'data_nascimento': nascimento,
                      'telefone': telefone, 'endereco': endereco},
        )
        perfis[usuario_nome] = perfil
    # O paciente do seed_dados também ganha histórico, para a conta "paciente" não ficar vazia.
    perfis['paciente'] = PerfilPaciente.objects.get(usuario__username='paciente')
    return perfis


def horario(medico, dias, hora):
    """Horário de 30 min do médico (cria se não existir, inclusive no passado)."""
    data = timezone.localdate() + datetime.timedelta(days=dias)
    inicio = datetime.time(hora, 0)
    fim = datetime.time(hora, 30)
    obj, _ = HorarioDisponivel.objects.get_or_create(
        medico=medico, data=data, hora_inicio=inicio, defaults={'hora_fim': fim, 'disponivel': True},
    )
    return obj


def marcar(paciente, h, status, motivo, observacoes=''):
    if Consulta.objects.filter(paciente=paciente, horario=h).exists():
        return False
    if status != Consulta.STATUS_CANCELADA and h.consultas.exclude(status=Consulta.STATUS_CANCELADA).exists():
        return False  # horário já ocupado por outra pessoa (ex.: agendado ao vivo)
    Consulta.objects.create(paciente=paciente, horario=h, status=status, motivo=motivo, observacoes=observacoes)
    return True


def criar_consultas(p):
    ana = PerfilMedico.objects.get(usuario__username='dra.ana')        # Cardiologia
    carlos = PerfilMedico.objects.get(usuario__username='dr.carlos')   # Dermatologia
    paula = PerfilMedico.objects.get(usuario__username='dra.paula')    # Pediatria
    A, C, X, K = (Consulta.STATUS_AGENDADA, Consulta.STATUS_CONFIRMADA,
                  Consulta.STATUS_CANCELADA, Consulta.STATUS_CONCLUIDA)

    # (paciente, médico, dias a partir de hoje, hora, status, motivo, observações)
    # Passado: 15h e 16h (não coincidem com os horários do seed). Futuro: horários do seed.
    consultas = [
        # Histórico (consultas que já aconteceram)
        ('maria.silva', ana, -20, 15, K, 'Check-up cardiológico anual', 'Pressão 12x8. Retorno em 1 ano.'),
        ('pedro.santos', carlos, -15, 16, K, 'Manchas na pele', 'Prescrito protetor solar FPS 50.'),
        ('roberto.almeida', ana, -10, 16, K, 'Dor no peito ao fazer esforço', 'Solicitado teste ergométrico.'),
        ('lucas.oliveira', paula, -7, 15, K, 'Consulta de rotina', 'Vacinação em dia.'),
        ('paciente', carlos, -5, 15, K, 'Acne', 'Iniciado tratamento tópico.'),
        ('fernanda.lima', ana, -3, 15, X, 'Palpitações', ''),
        # Próximas consultas
        ('roberto.almeida', ana, 1, 9, C, 'Retorno com o resultado do teste ergométrico', ''),
        ('maria.silva', carlos, 1, 10, A, 'Avaliação de pinta nas costas', ''),
        ('lucas.oliveira', paula, 2, 9, A, 'Febre e dor de garganta', ''),
        ('juliana.costa', ana, 2, 11, A, 'Exame admissional', ''),
        ('fernanda.lima', ana, 3, 10, C, 'Palpitações (remarcada)', ''),
        ('paciente', paula, 3, 14, A, 'Consulta de acompanhamento', ''),
        ('pedro.santos', carlos, 4, 11, X, 'Retorno dermatologia', ''),
    ]
    novas = 0
    for usuario, medico, dias, hora, status, motivo, obs in consultas:
        novas += marcar(p[usuario], horario(medico, dias, hora), status, motivo, obs)
    return novas


if __name__ == '__main__':
    call_command('seed_dados')
    perfis = criar_pacientes()
    novas = criar_consultas(perfis)
    print(f'\nPacientes de exemplo prontos ({len(PACIENTES)}) e {novas} consulta(s) nova(s) criada(s).')
    print(f'Todos entram com a senha: {SENHA}\n')
    print(f'{"Usuário":<18}{"Nome":<20}{"Consultas"}')
    for usuario in ['paciente'] + [linha[0] for linha in PACIENTES]:
        perfil = perfis[usuario]
        print(f'{usuario:<18}{perfil.usuario.get_full_name():<20}{perfil.consultas.count()}')
