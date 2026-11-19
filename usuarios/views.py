from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone

from agendamento.models import HorarioDisponivel

from .forms import BootstrapMixin, CadastroPacienteForm, MeusDadosForm
from .models import Especialidade, PerfilMedico


def inicio(request):
    """Página inicial pública da clínica."""
    especialidades = Especialidade.objects.annotate(total_medicos=Count('medicos'))
    medicos = PerfilMedico.objects.select_related('usuario', 'especialidade').annotate(
        horarios_livres=Count(
            'horarios',
            filter=Q(horarios__disponivel=True, horarios__data__gte=timezone.localdate()),
        ),
    )
    return render(request, 'usuarios/inicio.html', {
        'especialidades': especialidades,
        'medicos': medicos,
    })


class LoginForm(BootstrapMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Usuário'
        self._aplicar_bootstrap()


class EntrarView(auth_views.LoginView):
    template_name = 'usuarios/entrar.html'
    form_class = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        resposta = super().form_valid(form)
        usuario = form.get_user()
        messages.success(self.request, f'Olá, {usuario.first_name or usuario.username}! Login realizado.')
        return resposta


class SairView(auth_views.LogoutView):
    """Logout (somente via POST, como exige o Django)."""

    def post(self, request, *args, **kwargs):
        messages.info(request, 'Você saiu do sistema.')
        return super().post(request, *args, **kwargs)


def cadastro(request):
    """Tela "Cadastre-se": cria a conta do paciente e já faz o login."""
    if request.user.is_authenticated:
        return redirect('usuarios:painel')
    form = CadastroPacienteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        perfil = form.save()
        login(request, perfil.usuario)
        messages.success(request, 'Cadastro realizado com sucesso! Agora você já pode agendar sua consulta.')
        return redirect('agendamento:minhas_consultas')
    return render(request, 'usuarios/cadastro.html', {'form': form})


@login_required
def painel(request):
    """Após o login, envia cada perfil para a sua área."""
    usuario = request.user
    if usuario.is_staff:
        return redirect('admin:index')
    if hasattr(usuario, 'perfil_paciente'):
        return redirect('agendamento:minhas_consultas')
    messages.warning(request, 'Sua conta ainda não possui um perfil de acesso. Procure a recepção.')
    return redirect('inicio')


@login_required
def meus_dados(request):
    perfil = getattr(request.user, 'perfil_paciente', None)
    if perfil is None:
        return redirect('usuarios:painel')
    form = MeusDadosForm(request.POST or None, instance=perfil)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Seus dados foram atualizados.')
        return redirect('usuarios:meus_dados')
    return render(request, 'usuarios/meus_dados.html', {'form': form, 'perfil': perfil})


class SenhaForm(BootstrapMixin, PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aplicar_bootstrap()


class AlterarSenhaView(auth_views.PasswordChangeView):
    template_name = 'usuarios/alterar_senha.html'
    form_class = SenhaForm
    success_url = reverse_lazy('usuarios:meus_dados')

    def form_valid(self, form):
        messages.success(self.request, 'Senha alterada com sucesso.')
        return super().form_valid(form)
