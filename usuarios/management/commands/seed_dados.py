import datetime

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from agendamento.models import HorarioDisponivel
from usuarios.models import Especialidade, PerfilMedico, PerfilPaciente, PerfilRecepcionista


class Command(BaseCommand):
    help = 'Popula o banco com dados de exemplo: superusuário, médicos, recepcionista, paciente e horários.'

    def handle(self, *args, **options):
        self._criar_superusuario()
        especialidades = self._criar_especialidades()
        medicos = self._criar_medicos(especialidades)
        self._criar_recepcionista()
        self._criar_paciente_demo()
        self._criar_horarios(medicos)
        self.stdout.write(self.style.SUCCESS('Dados de exemplo criados com sucesso!'))

    def _criar_superusuario(self):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@clinicavida.com', 'admin12345')
            self.stdout.write('Superusuário criado: admin / admin12345')

    def _criar_especialidades(self):
        nomes = ['Cardiologia', 'Dermatologia', 'Pediatria', 'Ortopedia']
        especialidades = []
        for nome in nomes:
            especialidade, _ = Especialidade.objects.get_or_create(
                nome=nome, defaults={'descricao': f'Atendimento especializado em {nome.lower()}.'}
            )
            especialidades.append(especialidade)
        return especialidades

    def _criar_medicos(self, especialidades):
        dados_medicos = [
            ('dra.ana', 'Ana', 'Souza', 'CRM-12345', especialidades[0]),
            ('dr.carlos', 'Carlos', 'Lima', 'CRM-23456', especialidades[1]),
            ('dra.paula', 'Paula', 'Ferreira', 'CRM-34567', especialidades[2]),
        ]
        medicos = []
        for username, nome, sobrenome, crm, especialidade in dados_medicos:
            usuario, criado = User.objects.get_or_create(
                username=username,
                defaults={'first_name': nome, 'last_name': sobrenome, 'email': f'{username}@clinicavida.com'},
            )
            if criado:
                usuario.set_password('medico12345')
                usuario.save()
            perfil, _ = PerfilMedico.objects.get_or_create(
                usuario=usuario, defaults={'crm': crm, 'especialidade': especialidade}
            )
            medicos.append(perfil)
        return medicos

    def _criar_recepcionista(self):
        usuario, criado = User.objects.get_or_create(
            username='recepcao',
            defaults={'first_name': 'Rita', 'last_name': 'Nunes', 'email': 'recepcao@clinicavida.com'},
        )
        if criado:
            usuario.set_password('recepcao12345')
            usuario.save()
        PerfilRecepcionista.objects.get_or_create(usuario=usuario)

    def _criar_paciente_demo(self):
        usuario, criado = User.objects.get_or_create(
            username='paciente',
            defaults={'first_name': 'João', 'last_name': 'Pereira', 'email': 'paciente@exemplo.com'},
        )
        if criado:
            usuario.set_password('paciente12345')
            usuario.save()
        PerfilPaciente.objects.get_or_create(
            usuario=usuario, defaults={'cpf': '000.000.000-00', 'telefone': '(34) 90000-0000'}
        )

    def _criar_horarios(self, medicos):
        hoje = timezone.localdate()
        horas = [datetime.time(9, 0), datetime.time(10, 0), datetime.time(11, 0), datetime.time(14, 0)]
        for medico in medicos:
            for dias_a_frente in range(1, 6):
                data = hoje + datetime.timedelta(days=dias_a_frente)
                for hora_inicio in horas:
                    hora_fim = (datetime.datetime.combine(data, hora_inicio) + datetime.timedelta(minutes=30)).time()
                    HorarioDisponivel.objects.get_or_create(
                        medico=medico, data=data, hora_inicio=hora_inicio,
                        defaults={'hora_fim': hora_fim, 'disponivel': True},
                    )
