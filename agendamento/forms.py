from django import forms

from usuarios.forms import BootstrapMixin
from usuarios.models import Especialidade, PerfilMedico

from .models import Consulta


class FiltroHorariosForm(BootstrapMixin, forms.Form):
    """Filtros da tela de horários livres (todos opcionais)."""

    especialidade = forms.ModelChoiceField(
        queryset=Especialidade.objects.all(), required=False, empty_label='Todas',
    )
    medico = forms.ModelChoiceField(
        label='Médico', queryset=PerfilMedico.objects.select_related('usuario'),
        required=False, empty_label='Todos',
    )
    data = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aplicar_bootstrap()


class AgendarConsultaForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = Consulta
        fields = ('motivo',)
        widgets = {
            'motivo': forms.TextInput(attrs={'placeholder': 'Ex.: consulta de rotina, dor no joelho...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aplicar_bootstrap()
