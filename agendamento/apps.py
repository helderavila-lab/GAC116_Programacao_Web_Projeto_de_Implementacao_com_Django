from django.apps import AppConfig


class AgendamentoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'agendamento'
    verbose_name = 'Agendamento'

    def ready(self):
        import agendamento.signals  # noqa: F401
