# Clínica Vida+ — Sistema de Agendamento de Consultas

Trabalho Prático da disciplina **GAC116 - Programação Web**, desenvolvido com Django.

> **Status: Checkpoint 2** — aplicação concluída: site com login, logout e cadastro, área do paciente
> (Bootstrap, tema claro/escuro) e ambiente administrativo integrado ao banco de dados.

## Integrantes do grupo

- **Heitor Ramos Vieira Rocha** — [@heitor-vieira](https://github.com/heitor-vieira)
- **Helder Jose Avila** — [@helderavila-lab](https://github.com/helderavila-lab)
- **Lucas de Jesus Gonçalves** — [@lucasjesus682](https://github.com/lucasjesus682)

## Descrição do projeto

Aplicação web para gestão de marcações e registos de pacientes em uma clínica. O sistema tem duas áreas,
ambas protegidas por autenticação:

- **Área do paciente** (site em `/`): o paciente se cadastra, faz login, consulta os horários livres
  filtrando por especialidade, médico e data, agenda a consulta, acompanha o histórico e cancela quando precisar.
- **Área administrativa** (`/admin/`): médicos e recepcionistas gerenciam especialidades, médicos, pacientes,
  horários disponíveis e consultas, cada perfil com as suas permissões.

## Tecnologias utilizadas

- [Django](https://www.djangoproject.com/) 6.1
- [django-jazzmin](https://github.com/farridav/django-jazzmin) — tema customizado do Django Admin
- [Bootstrap 5.3](https://getbootstrap.com/) e Bootstrap Icons — interface responsiva do site, com tema claro e escuro
- SQLite — banco de dados relacional (ambiente de desenvolvimento)
- HTML, CSS e JavaScript (templates do Django)

## Modelagem do banco de dados

| Entidade | App | Relacionamentos |
|---|---|---|
| `Especialidade` | usuarios | — |
| `PerfilMedico` | usuarios | OneToOne com `User`, ForeignKey para `Especialidade` |
| `PerfilPaciente` | usuarios | OneToOne com `User` |
| `PerfilRecepcionista` | usuarios | OneToOne com `User` |
| `HorarioDisponivel` | agendamento | ForeignKey para `PerfilMedico` |
| `Consulta` | agendamento | ForeignKey para `PerfilPaciente` e `HorarioDisponivel` |

## Estrutura do projeto

```
sistema-agendamento-consultas/
├── clinica/              # Configurações do projeto (settings, urls)
├── templates/            # Templates globais: base.html (Bootstrap, menu, tema claro/escuro) e _campo.html
├── usuarios/             # App: perfis (Médico, Paciente, Recepcionista), especialidades e autenticação
│   ├── models.py         # Especialidade, PerfilMedico, PerfilPaciente, PerfilRecepcionista
│   ├── forms.py          # Cadastro de perfis com conta, tela "Cadastre-se" e "Meus dados"
│   ├── views.py          # Página inicial, login, logout, cadastro, meus dados e alterar senha
│   ├── urls.py           # Rotas /contas/...
│   ├── templates/usuarios/  # Telas do site (início, entrar, cadastro...)
│   ├── admin.py          # Admin customizado com filtros
│   ├── signals.py        # Criação automática de grupos/permissões por perfil
│   ├── tests.py, tests_site.py   # Testes automatizados
│   └── management/commands/seed_dados.py   # Popula dados de exemplo
├── agendamento/          # App: horários disponíveis e consultas
│   ├── models.py         # HorarioDisponivel, Consulta + regras de negócio
│   ├── forms.py          # Filtro de horários e confirmação de agendamento
│   ├── views.py          # Área do paciente: minhas consultas, horários livres, agendar, cancelar
│   ├── urls.py           # Rotas /paciente/...
│   ├── templates/agendamento/  # Telas da área do paciente
│   ├── admin.py          # Admin customizado com filtros
│   ├── signals.py        # Disponibilidade automática dos horários
│   └── tests.py, tests_site.py   # Testes automatizados
├── manage.py
└── requirements.txt
```

## Rotas principais

| Endereço | Tela | Acesso |
|---|---|---|
| `/` | Página inicial (especialidades e equipe) | Público |
| `/contas/entrar/` | Login | Público |
| `/contas/cadastro/` | Cadastre-se (cria a conta de paciente) | Público |
| `/contas/sair/` | Logout | Logado |
| `/contas/meus-dados/` | Editar os próprios dados | Paciente |
| `/contas/alterar-senha/` | Alterar a senha | Logado |
| `/paciente/` | Minhas consultas (próximas e histórico) | Paciente |
| `/paciente/horarios/` | Horários livres com filtros | Paciente |
| `/paciente/horarios/<id>/agendar/` | Confirmar agendamento | Paciente |
| `/admin/` | Ambiente administrativo (Jazzmin) | Equipe |

## Perfis de usuário

| Perfil | Acesso | Permissões |
|---|---|---|
| **Administrador (superusuário)** | `/admin/` | Acesso total |
| **Médico** | `/admin/` | Gerencia apenas os próprios horários disponíveis e visualiza/atualiza o status das próprias consultas |
| **Recepcionista** | `/admin/` | Gerencia pacientes, horários e consultas; visualiza médicos |
| **Paciente** | Site (`/paciente/`) | Cadastra-se, agenda, acompanha e cancela as próprias consultas; edita os próprios dados |

## Principais funcionalidades

- Site com **login, logout e tela "Cadastre-se"** (validação de CPF, e-mail único, confirmação e regras de senha)
- Após o login, cada perfil vai para a sua área: paciente para o site, equipe para o painel administrativo
- **Área do paciente**: horários livres com filtros por especialidade, médico e data (com paginação),
  agendamento com motivo, lista de próximas consultas e histórico, cancelamento com confirmação
- O paciente não consegue agendar horário passado, ocupado ou que coincida com outra consulta sua
- Edição dos próprios dados e troca de senha
- Interface com **Bootstrap 5**, responsiva, com **tema claro, escuro e automático** (a escolha fica salva no navegador)
- Área administrativa (Django Admin com tema Jazzmin) protegida por autenticação e integrada ao mesmo banco
- Filtros por status, especialidade, médico e data, além de busca e navegação por data
- Grupos e permissões criados automaticamente para cada perfil
- Médicos visualizam e gerenciam apenas os próprios horários e consultas
- Cadastro de médicos, pacientes e recepcionistas já cria a conta de acesso (usuário e senha) no mesmo formulário
- Regras de integridade: um horário não pode ter duas consultas ativas; hora de fim posterior à de início;
  horários do mesmo médico não podem se sobrepor; não é possível agendar em horário indisponível
- Disponibilidade dos horários atualizada automaticamente ao agendar, cancelar, remarcar ou excluir consultas
- Seletor de tema (Claro / Escuro / Automático) no topo do painel

## Instruções para instalação

Pré-requisitos: Python 3.12+ instalado.

```bash
# 1. Clonar o repositório
git clone <URL_DO_REPOSITORIO>
cd sistema-agendamento-consultas

# 2. Criar e ativar o ambiente virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 3. Instalar as dependências
pip install -r requirements.txt

# 4. Aplicar as migrações do banco de dados
python manage.py migrate

# 5. (Opcional) Popular o banco com dados de exemplo
python manage.py seed_dados
```

## Instruções para execução

```bash
python manage.py runserver
```

- Site (área do paciente): http://127.0.0.1:8000/
- Área administrativa: http://127.0.0.1:8000/admin/

Para rodar os testes automatizados:

```bash
python manage.py test
```

### Contas de exemplo (após `seed_dados`)

| Perfil | Usuário | Senha |
|---|---|---|
| Administrador | `admin` | `admin12345` |
| Recepcionista | `recepcao` | `recepcao12345` |
| Médico | `dra.ana` | `medico12345` |
| Paciente | `paciente` | `paciente12345` |

Também é possível criar uma conta nova de paciente pela tela **Cadastre-se**.

## Controle de versão

Este projeto segue o fluxo de branches:
- `main` — versão estável/entregável
- `develop` — integração das funcionalidades em desenvolvimento
- `feature` — desenvolvimento de funcionalidades específicas
