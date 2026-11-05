# Clínica Vida+ — Sistema de Agendamento de Consultas

Trabalho Prático da disciplina **GAC116 - Programação Web**, desenvolvido com Django.

> **Status: Checkpoint 1** — modelagem do banco de dados e ambiente administrativo.

## Integrantes do grupo

- **Heitor Ramos Vieira Rocha** — [@heitor-vieira](https://github.com/heitor-vieira)
- **Helder Jose Avila** — [@helderavila-lab](https://github.com/helderavila-lab)
- **Lucas de Jesus Gonçalves** — [@lucasjesus682](https://github.com/lucasjesus682)

## Descrição do projeto

Aplicação web para gestão de marcações e registos de pacientes em uma clínica. Médicos e
recepcionistas acessam a área administrativa para gerenciar especialidades, médicos, pacientes,
horários disponíveis e consultas.

## Tecnologias utilizadas

- [Django](https://www.djangoproject.com/) 6.1
- [django-jazzmin](https://github.com/farridav/django-jazzmin) — tema customizado do Django Admin
- SQLite — banco de dados relacional (ambiente de desenvolvimento)

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
├── usuarios/             # App: perfis (Médico, Paciente, Recepcionista) e especialidades
│   ├── models.py         # Especialidade, PerfilMedico, PerfilPaciente, PerfilRecepcionista
│   ├── admin.py          # Admin customizado com filtros
│   ├── signals.py        # Criação automática de grupos/permissões por perfil
│   └── management/commands/seed_dados.py   # Popula dados de exemplo
├── agendamento/          # App: horários disponíveis e consultas
│   ├── models.py         # HorarioDisponivel, Consulta
│   └── admin.py          # Admin customizado com filtros
├── manage.py
└── requirements.txt
```

## Perfis de usuário

| Perfil | Acesso | Permissões |
|---|---|---|
| **Administrador (superusuário)** | `/admin/` | Acesso total |
| **Médico** | `/admin/` | Gerencia apenas os próprios horários disponíveis e visualiza/atualiza o status das próprias consultas |
| **Recepcionista** | `/admin/` | Gerencia pacientes, horários e consultas; visualiza médicos |

## Principais funcionalidades

- Área administrativa (Django Admin com tema Jazzmin) protegida por autenticação
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

Acesse a área administrativa em http://127.0.0.1:8000/admin/

### Contas de exemplo (após `seed_dados`)

| Perfil | Usuário | Senha |
|---|---|---|
| Administrador | `admin` | `admin12345` |
| Recepcionista | `recepcao` | `recepcao12345` |
| Médico | `dra.ana` | `medico12345` |

## Controle de versão

Este projeto segue o fluxo de branches:
- `main` — versão estável/entregável
- `develop` — integração das funcionalidades em desenvolvimento
- `feature` — desenvolvimento de funcionalidades específicas
