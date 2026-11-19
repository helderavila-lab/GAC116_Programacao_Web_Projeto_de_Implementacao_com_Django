"""Rotas do projeto Clínica Vida+.

- /            página inicial pública
- /contas/     login, logout, cadastro e perfil (app usuarios)
- /paciente/   área do paciente: consultas e agendamento (app agendamento)
- /admin/      ambiente administrativo (Django Admin + Jazzmin)
"""
from django.contrib import admin
from django.urls import include, path

from usuarios.views import inicio

urlpatterns = [
    path('', inicio, name='inicio'),
    path('contas/', include('usuarios.urls')),
    path('paciente/', include('agendamento.urls')),
    path('admin/', admin.site.urls),
]
