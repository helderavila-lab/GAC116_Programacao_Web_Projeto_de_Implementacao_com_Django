from django.contrib.auth.models import User
from django.db import models


class Especialidade(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Especialidade'
        verbose_name_plural = 'Especialidades'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class PerfilMedico(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_medico')
    crm = models.CharField('CRM', max_length=20, unique=True)
    especialidade = models.ForeignKey(
        Especialidade, on_delete=models.PROTECT, related_name='medicos'
    )
    telefone = models.CharField(max_length=20, blank=True)
    biografia = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Médico'
        verbose_name_plural = 'Médicos'
        ordering = ['usuario__first_name']

    def __str__(self):
        nome = self.usuario.get_full_name() or self.usuario.username
        return f'Dr(a). {nome}'


class PerfilPaciente(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_paciente')
    cpf = models.CharField('CPF', max_length=14, unique=True)
    data_nascimento = models.DateField('Data de nascimento', null=True, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    endereco = models.CharField('Endereço', max_length=255, blank=True)

    class Meta:
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        ordering = ['usuario__first_name']

    def __str__(self):
        return self.usuario.get_full_name() or self.usuario.username


class PerfilRecepcionista(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_recepcionista')
    telefone = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = 'Recepcionista'
        verbose_name_plural = 'Recepcionistas'
        ordering = ['usuario__first_name']

    def __str__(self):
        return self.usuario.get_full_name() or self.usuario.username
