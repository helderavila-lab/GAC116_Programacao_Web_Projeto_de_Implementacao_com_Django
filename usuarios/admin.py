from django.contrib import admin

from .forms import CAMPOS_USUARIO, PerfilMedicoForm, PerfilPacienteForm, PerfilRecepcionistaForm
from .models import Especialidade, PerfilMedico, PerfilPaciente, PerfilRecepcionista


class PerfilUsuarioAdmin(admin.ModelAdmin):
    """Base dos perfis: o formulário cria/edita também a conta de usuário vinculada."""

    titulo_perfil = 'Dados do perfil'
    campos_perfil = ()

    def get_fieldsets(self, request, obj=None):
        if obj and not self.has_change_permission(request, obj):
            # Somente visualização: mostra o usuário vinculado e os dados do perfil.
            return [(None, {'fields': ('usuario',) + self.campos_perfil})]
        return [
            ('Dados de acesso', {'fields': CAMPOS_USUARIO}),
            (self.titulo_perfil, {'fields': self.campos_perfil}),
        ]


@admin.register(Especialidade)
class EspecialidadeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome',)


@admin.register(PerfilMedico)
class PerfilMedicoAdmin(PerfilUsuarioAdmin):
    form = PerfilMedicoForm
    titulo_perfil = 'Dados do médico'
    campos_perfil = ('crm', 'especialidade', 'telefone', 'biografia')
    list_display = ('usuario', 'crm', 'especialidade', 'telefone')
    list_filter = ('especialidade',)
    search_fields = ('usuario__first_name', 'usuario__last_name', 'usuario__username', 'crm')


@admin.register(PerfilPaciente)
class PerfilPacienteAdmin(PerfilUsuarioAdmin):
    form = PerfilPacienteForm
    titulo_perfil = 'Dados do paciente'
    campos_perfil = ('cpf', 'data_nascimento', 'telefone', 'endereco')
    list_display = ('usuario', 'cpf', 'data_nascimento', 'telefone')
    list_filter = ('data_nascimento',)
    search_fields = ('usuario__first_name', 'usuario__last_name', 'usuario__username', 'cpf')


@admin.register(PerfilRecepcionista)
class PerfilRecepcionistaAdmin(PerfilUsuarioAdmin):
    form = PerfilRecepcionistaForm
    titulo_perfil = 'Dados da recepcionista'
    campos_perfil = ('telefone',)
    list_display = ('usuario', 'telefone')
    search_fields = ('usuario__first_name', 'usuario__last_name', 'usuario__username')
