from django.urls import path

from . import views

app_name = 'usuarios'

urlpatterns = [
    path('entrar/', views.EntrarView.as_view(), name='entrar'),
    path('sair/', views.SairView.as_view(), name='sair'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('painel/', views.painel, name='painel'),
    path('meus-dados/', views.meus_dados, name='meus_dados'),
    path('alterar-senha/', views.AlterarSenhaView.as_view(), name='alterar_senha'),
]
