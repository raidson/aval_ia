# SIMPA — Sistema Inteligente de Monitoramento e Predição Acadêmica

Projeto Integrador — 2º Período | Curso de Inteligência Artificial | UniEvangélica  
Prof. Henrique Lima

---

## Estrutura do Projeto

```
simpa/
├── models/              # Entidades do domínio (Aluno, Turma, Indicador, Usuario)
├── services/            # Regras de negócio e persistência
├── api/                 # Rotas Flask (REST API)
├── data/                # Arquivos JSON + script de seed
├── notebooks/           # Análises exploratórias (Ciclo 2)
├── docs/                # Documentação e diagramas UML
├── tests/               # Testes unitários
└── requirements.txt
```

---

## Como Executar

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Popular o banco com dados simulados
```bash
python data/seed.py
```

### 3. Iniciar a API
```bash
python api/app.py
```
A API estará disponível em `http://localhost:5000`

### 4. Rodar os testes
```bash
python -m pytest tests/ -v
```

---

## Endpoints da API

| Método | Rota | Descrição | Permissão |
|--------|------|-----------|-----------|
| GET | `/` | Healthcheck | Pública |
| POST | `/auth/login` | Login | Pública |
| POST | `/auth/logout` | Logout | Autenticado |
| GET | `/alunos` | Listar alunos | Autenticado |
| GET | `/alunos/<id>` | Buscar aluno | Autenticado |
| POST | `/alunos` | Cadastrar aluno | escrita |
| POST | `/alunos/<id>/notas` | Registrar nota | escrita |
| POST | `/alunos/<id>/frequencias` | Registrar frequência | escrita |
| GET | `/indicadores/<aluno_id>` | Listar indicadores | Autenticado |
| POST | `/indicadores/<aluno_id>/gerar` | Gerar indicadores | escrita |
| GET | `/indicadores/<aluno_id>/risco` | Classificar risco | Autenticado |
| GET | `/relatorios/turma` | Relatório consolidado | relatorios |

### Autenticação
Todas as rotas protegidas exigem o header:
```
Authorization: Bearer <token>
```

O token é obtido no endpoint `/auth/login`.

---

## Exemplo de Uso

```bash
# Login
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@simpa.edu","senha":"admin123"}'

# Listar alunos (com o token obtido)
curl http://localhost:5000/alunos \
  -H "Authorization: Bearer <TOKEN>"

# Gerar indicadores de um aluno
curl -X POST http://localhost:5000/indicadores/<ALUNO_ID>/gerar \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"periodo": 2}'
```

---

## Marcos do Projeto

| Marco | Semanas | Entrega |
|-------|---------|---------|
| Marco 1 | 1–7 | Arquitetura + API básica funcional ✓ |
| Marco 2 | 8–13 | Módulo analítico + visualizações |
| Marco 3 | 14–19 | Segurança completa + testes + documentação |

---

## Níveis de Execução

- **Nível 1 (obrigatório):** arquitetura POO, API funcional, dados simulados, segurança básica
- **Nível 2 (aprofundamento):** predição por regressão, correlação, padrões de projeto, logs completos
