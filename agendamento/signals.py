from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from .models import PerfilMedico, PerfilPaciente, PerfilRecepcionista

# Permissões padrão atribuídas a cada grupo (perfil) de usuário.
GRUPOS_PERMISSOES = {
    'Médicos': [
        ('usuarios', 'perfilpaciente', ['view_perfilpaciente']),
        ('agendamento', 'horariodisponivel', [
            'add_horariodisponivel', 'change_horariodisponivel',
            'delete_horariodisponivel', 'view_horariodisponivel',
        ]),
        ('agendamento', 'consulta', ['view_consulta', 'change_consulta']),
    ],
    'Recepcionistas': [
        ('usuarios', 'perfilpaciente', [
            'add_perfilpaciente', 'change_perfilpaciente',
            'delete_perfilpaciente', 'view_perfilpaciente',
        ]),
        ('usuarios', 'perfilmedico', ['view_perfilmedico']),
        ('agendamento', 'horariodisponivel', [
            'add_horariodisponivel', 'change_horariodisponivel',
            'delete_horariodisponivel', 'view_horariodisponivel',
        ]),
        ('agendamento', 'consulta', [
            'add_consulta', 'change_consulta', 'delete_consulta', 'view_consulta',
        ]),
    ],
    'Pacientes': [],
}


@receiver(post_migrate)
def criar_grupos_padrao(sender, **kwargs):
    """Cria os grupos de perfis e concede as permissões padrão após as migrações."""
    # Executa também após o app 'agendamento', pois as permissões de cada app só
    # existem depois do post_migrate daquele app (que roda depois de 'usuarios').
    if sender.name not in ('usuarios', 'agendamento'):
        return

    for nome_grupo, permissoes in GRUPOS_PERMISSOES.items():
        grupo, _ = Group.objects.get_or_create(name=nome_grupo)
        for app_label, model_name, codenames in permissoes:
            for codename in codenames:
                try:
                    permissao = Permission.objects.get(
                        content_type__app_label=app_label,
                        content_type__model=model_name,
                        codename=codename,
                    )
                except Permission.DoesNotExist:
                    continue
                grupo.permissions.add(permissao)


def _vincular_grupo(usuario, nome_grupo, tornar_staff):
    grupo, _ = Group.objects.get_or_create(name=nome_grupo)
    usuario.groups.add(grupo)
    if tornar_staff and not usuario.is_staff:
        usuario.is_staff = True
        usuario.save(update_fields=['is_staff'])


@receiver(post_save, sender=PerfilMedico)
def ao_criar_perfil_medico(sender, instance, created, **kwargs):
    if created:
        _vincular_grupo(instance.usuario, 'Médicos', tornar_staff=True)


@receiver(post_save, sender=PerfilRecepcionista)
def ao_criar_perfil_recepcionista(sender, instance, created, **kwargs):
    if created:
        _vincular_grupo(instance.usuario, 'Recepcionistas', tornar_staff=True)


@receiver(post_save, sender=PerfilPaciente)
def ao_criar_perfil_paciente(sender, instance, created, **kwargs):
    if created:
        _vincular_grupo(instance.usuario, 'Pacientes', tornar_staff=False)
