from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import PerfilMedico, PerfilPaciente, PerfilRecepcionista

CAMPOS_USUARIO = ('first_name', 'last_name', 'username', 'email', 'password')


class PerfilUsuarioForm(forms.ModelForm):
    """Formulário de perfil que já cria/edita a conta de usuário (User) vinculada.

    Assim a recepcionista consegue cadastrar um paciente completo sem precisar de
    permissões sobre a tabela de usuários do Django.
    """

    first_name = forms.CharField(label='Nome', max_length=150)
    last_name = forms.CharField(label='Sobrenome', max_length=150, required=False)
    username = forms.CharField(
        label='Usuário', max_length=150, validators=[UnicodeUsernameValidator()],
        help_text='Usado para entrar no sistema. Letras, números e @/./+/-/_ apenas.',
    )
    email = forms.EmailField(label='E-mail', required=False)
    password = forms.CharField(
        label='Senha', required=False, strip=False,
        widget=forms.PasswordInput(render_value=False),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        usuario = self._usuario_existente()
        if usuario:
            for campo in CAMPOS_USUARIO[:-1]:
                if campo in self.fields:
                    self.fields[campo].initial = getattr(usuario, campo)
            self.fields['password'].help_text = 'Deixe em branco para manter a senha atual.'
        else:
            self.fields['password'].required = True

    def _usuario_existente(self):
        return self.instance.usuario if self.instance.pk else None

    def clean_username(self):
        username = self.cleaned_data['username']
        existentes = User.objects.filter(username=username)
        usuario = self._usuario_existente()
        if usuario:
            existentes = existentes.exclude(pk=usuario.pk)
        if existentes.exists():
            raise ValidationError('Já existe um usuário com este nome de usuário.')
        return username

    def clean(self):
        dados = super().clean()
        senha = dados.get('password')
        if senha:
            usuario_temporario = User(
                username=dados.get('username', ''), first_name=dados.get('first_name', ''),
                last_name=dados.get('last_name', ''), email=dados.get('email', ''),
            )
            try:
                validate_password(senha, usuario_temporario)
            except ValidationError as erro:
                self.add_error('password', erro)
        return dados

    def save(self, commit=True):
        usuario = self._usuario_existente() or User()
        for campo in CAMPOS_USUARIO[:-1]:
            setattr(usuario, campo, self.cleaned_data[campo])
        if self.cleaned_data.get('password'):
            usuario.set_password(self.cleaned_data['password'])
        usuario.save()
        self.instance.usuario = usuario
        return super().save(commit)


class PerfilMedicoForm(PerfilUsuarioForm):
    class Meta:
        model = PerfilMedico
        fields = ('crm', 'especialidade', 'telefone', 'biografia')


def validar_data_nascimento(data):
    if data and data > timezone.localdate():
        raise ValidationError('A data de nascimento não pode estar no futuro.')
    return data


class PerfilPacienteForm(PerfilUsuarioForm):
    class Meta:
        model = PerfilPaciente
        fields = ('cpf', 'data_nascimento', 'telefone', 'endereco')

    def clean_data_nascimento(self):
        return validar_data_nascimento(self.cleaned_data.get('data_nascimento'))


class PerfilRecepcionistaForm(PerfilUsuarioForm):
    class Meta:
        model = PerfilRecepcionista
        fields = ('telefone',)


# ---------------------------------------------------------------------------
# Formulários do site (área pública e área do paciente)
# ---------------------------------------------------------------------------

class BootstrapMixin:
    """Aplica as classes do Bootstrap aos campos do formulário."""

    def _aplicar_bootstrap(self):
        for campo in self.fields.values():
            widget = campo.widget
            if isinstance(widget, (forms.CheckboxInput, forms.RadioSelect)):
                classe = 'form-check-input'
            elif isinstance(widget, forms.Select):
                classe = 'form-select'
            else:
                classe = 'form-control'
            widget.attrs['class'] = f"{widget.attrs.get('class', '')} {classe}".strip()

    def full_clean(self):
        super().full_clean()
        # Destaca em vermelho os campos com erro.
        for nome in self.errors:
            if nome in self.fields:
                widget = self.fields[nome].widget
                widget.attrs['class'] = f"{widget.attrs.get('class', '')} is-invalid".strip()


def validar_cpf(valor):
    """Valida o CPF (dígitos verificadores) e devolve no formato 000.000.000-00."""
    digitos = ''.join(c for c in valor if c.isdigit())
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        raise ValidationError('Informe um CPF válido com 11 dígitos.')
    for tamanho in (9, 10):
        soma = sum(int(d) * peso for d, peso in zip(digitos[:tamanho], range(tamanho + 1, 1, -1)))
        digito = (soma * 10) % 11 % 10
        if digito != int(digitos[tamanho]):
            raise ValidationError('CPF inválido. Confira os números digitados.')
    return f'{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}'


class CadastroPacienteForm(BootstrapMixin, PerfilPacienteForm):
    """Tela "Cadastre-se": o próprio paciente cria a conta e o perfil."""

    password2 = forms.CharField(
        label='Confirme a senha', strip=False, widget=forms.PasswordInput(render_value=False),
    )

    class Meta(PerfilPacienteForm.Meta):
        widgets = {'data_nascimento': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')}

    field_order = [
        'first_name', 'last_name', 'cpf', 'data_nascimento', 'telefone', 'endereco',
        'email', 'username', 'password', 'password2',
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['last_name'].required = True
        self.fields['cpf'].help_text = 'Somente números ou no formato 000.000.000-00.'
        self.fields['telefone'].widget.attrs['placeholder'] = '(00) 00000-0000'
        self._aplicar_bootstrap()

    def clean_cpf(self):
        cpf = validar_cpf(self.cleaned_data['cpf'])
        if PerfilPaciente.objects.filter(cpf=cpf).exists():
            raise ValidationError('Já existe um paciente cadastrado com este CPF.')
        return cpf

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Este e-mail já está em uso.')
        return email

    def clean(self):
        dados = super().clean()
        if dados.get('password') and dados.get('password2') and dados['password'] != dados['password2']:
            self.add_error('password2', 'As senhas não conferem.')
        return dados


class MeusDadosForm(BootstrapMixin, forms.ModelForm):
    """Paciente edita os próprios dados (o CPF e o usuário não mudam)."""

    first_name = forms.CharField(label='Nome', max_length=150)
    last_name = forms.CharField(label='Sobrenome', max_length=150)
    email = forms.EmailField(label='E-mail')

    class Meta:
        model = PerfilPaciente
        fields = ('data_nascimento', 'telefone', 'endereco')
        widgets = {'data_nascimento': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')}

    field_order = ['first_name', 'last_name', 'email', 'data_nascimento', 'telefone', 'endereco']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        usuario = self.instance.usuario
        for campo in ('first_name', 'last_name', 'email'):
            self.fields[campo].initial = getattr(usuario, campo)
        self._aplicar_bootstrap()

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.usuario_id).exists():
            raise ValidationError('Este e-mail já está em uso.')
        return email

    def clean_data_nascimento(self):
        return validar_data_nascimento(self.cleaned_data.get('data_nascimento'))

    def save(self, commit=True):
        usuario = self.instance.usuario
        for campo in ('first_name', 'last_name', 'email'):
            setattr(usuario, campo, self.cleaned_data[campo])
        usuario.save()
        return super().save(commit)
