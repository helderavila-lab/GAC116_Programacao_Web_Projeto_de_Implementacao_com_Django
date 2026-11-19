from django.urls import path

from . import views

app_name = 'agendamento'

urlpatterns = [
    path('', views.minhas_consultas, name='minhas_consultas'),
    path('horarios/', views.horarios_livres, name='horarios_livres'),
    path('horarios/<int:horario_id>/agendar/', views.agendar, name='agendar'),
    path('consultas/<int:consulta_id>/cancelar/', views.cancelar, name='cancelar'),
]
