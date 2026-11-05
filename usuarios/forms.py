from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError

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


class PerfilPacienteForm(PerfilUsuarioForm):
    class Meta:
        model = PerfilPaciente
        fields = ('cpf', 'data_nascimento', 'telefone', 'endereco')


class PerfilRecepcionistaForm(PerfilUsuarioForm):
    class Meta:
        model = PerfilRecepcionista
        fields = ('telefone',)
