# Matrícula Honrosa — Pré-Matrícula (Projeto)

README rápido e prático para desenvolver, testar e rodar o projeto `matricula_honrosa`.

---

## Visão geral

Aplicação FastAPI + SQLAlchemy que coleta **pré-matrícula** (expectativas) dos alunos, permite cadastro de turmas / salas / professores pela coordenação e gera uma **expectativa perfeita** (placeholder/entrada para o solver). Inclui frontend simples (Jinja2) com interface drag & drop para o aluno.

Principais objetivos:

* Registrar expectativas dos alunos (blocos/horários).
* Permitir à coordenação cadastrar turmas, salas e professores.
* Fornecer um agregador de preferência (API) para alimentar um solver de timetabling.
* UX simples: página `aluno.html` drag & drop para montar carga horária “dos sonhos”.

---

## Estrutura principal do repositório

```
.
├── alembic/                 # migrações (opcional)
├── app/
│   ├── main.py              # app FastAPI
│   ├── database.py         # engine / Session / init_db()
│   ├── models.py           # modelos SQLAlchemy
│   ├── routes/             # endpoints (aluno, coord, professor, view)
│   ├── templates/          # Jinja2 templates (aluno.html, base.html, etc.)
│   └── solver.py           # esqueleto do solver (OR-Tools/OptaPlanner)
├── create_db.py             # (opcional) criar DB
├── seed_db.py               # script idempotente para popular DB (dev)
├── data/
│   └── association_requests.json
├── test.db                  # sqlite local (dev)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── tests/
```

---

## Pré-requisitos (dev)

* Python 3.10+ (use sua venv)
* dependências: `pip install -r requirements.txt`
* (opcional) `sqlite3` CLI para inspeções manuais
* (opcional) Docker + Docker Compose

---

## Instruções rápidas — rodar localmente

1. Ative a virtualenv:

```bash
source .venv/bin/activate
```

2. Instale dependências (se necessário):

```bash
pip install -r requirements.txt
```

3. (Re)crie as tabelas e popule dados de desenvolvimento:

```bash
# cria tabelas (init_db usa app.models.Base.create_all)
python seed_db.py
```

`seed_db.py` é idempotente — roda várias vezes sem duplicar.

4. Rode o servidor:

```bash
uvicorn app.main:app --reload
```

5. Acesse:

* Frontend: `http://127.0.0.1:8000/`
* Aluno (questionário): `http://127.0.0.1:8000/aluno/`
* Coordenação (cadastros): `http://127.0.0.1:8000/coord/`
* Visualização expectativa (HTML): `http://127.0.0.1:8000/view/expectativa/html`
* API docs: `http://127.0.0.1:8000/docs`

---

## Endpoints importantes (exemplos)

**Coordenação**

* `GET /coord/turmas` — listar turmas
* `POST /coord/turmas` — criar turma

  ```json
  { "codigo":"TINF101", "carga_horaria":60, "precisa_computador": true, "sala_id": 1, "semestre":"2025.2" }
  ```
* `GET /coord/professores` — listar professores
* `POST /coord/professores` — criar professor

  ```json
  { "nome":"Prof Teste", "disciplinas_aptas": "TINF101" }
  ```
* `POST /coord/salas` — criar sala

  ```json
  { "nome":"Lab1", "capacidade":30, "tem_computador": true }
  ```
* `POST /coord/requests/review` — aprovar/negaar requests de associação (JSON)

**Professor**

* `GET /professor/?professor_id=1` — página de perfil do professor
* `POST /professor/solicitar` — criar solicitação (salva em `data/association_requests.json`)

**Aluno**

* `GET /aluno/?aluno_id=1` — abre questionário (renderiza `aluno.html`)
* `POST /aluno/salvar` — salva expectativas (JSON):

  ```json
  {
    "aluno_id": 1,
    "disciplinas": [
      { "id": 1, "horarios": ["M12","T34"], "prioridade": 1 }
    ]
  }
  ```
* `GET /aluno/me/{aluno_id}` — retorna preferências atuais (JSON)

**Visualização / Solver**

* `GET /view/expectativa` — agregação de preferências (JSON)
* `GET /view/expectativa/html` — mostra a expectativa perfeita (HTML)

---

## Formato de horários (importante)

O backend valida **blocos UFRN** como `M12`, `M34`, `M56`, `T12`, `T34`, `T56`, `N12`, `N34`, `M1234`, `T1234`, `N1234`, `S12`.
O frontend atual mostra células por dia+turno (`Seg M`, `Ter T` etc.). **Sugestão**:

* alinhar frontend para enviar `M12/T34/...` ou
* mapear no backend `SegM -> M12` (snippet de mapeamento disponível se quiser).

---

## DB — reset rápido (dev)

Para apagar e recriar o DB (Opção A — rápida, útil em dev):

```bash
rm -f test.db
python seed_db.py
```

Ou usar `create_db.py` se disponível (ver repositório).

> **Atenção:** não delete DB em produção.

---

## Migrations

O projeto inclui Alembic (`alembic/` e `alembic.ini`). Para gerenciar migrations (produção/repositório):

```bash
alembic revision --autogenerate -m "msg"
alembic upgrade head
```

(use `DATABASE_URL` correto no alembic.ini ou em variável de ambiente).

---

## Testes

Rodar testes (pytest):

```bash
pytest -q
```

Os testes usam `test.db` ou in-memory DB (ver `tests/`).

---

## Debug & Troubleshooting — erros comuns

* **`GET /aluno/` retorna `{"detail":"Aluno não encontrado"}`**
  → significa que não há `Aluno` com `id=1`. Rode `python seed_db.py` ou insira um `Aluno` via API/SQLite.

* **404 em `/aluno/` ou `/professor/` mas rotas listadas**
  → confirme `uvicorn` está ativo quando você faz `curl`; verifique logs do servidor (traceback).

* **`OperationalError: no such column: ...`**
  → o modelo mudou e o DB não; rode `alembic upgrade head` ou delete `test.db` e recrie (`seed_db.py`) em dev.

* **N+1 queries na agregação** (`view.expectativa`)
  → otimizar pré-carregamento: `db.query(Turma).filter(Turma.id.in_(...)).all()` em vez de `get` por item.

---

## Desenvolvimento / dicas rápidas

* Use `seed_db.py` para popular DB localmente (idempotente).
* Use `uvicorn app.main:app --reload` para reload automático durante dev.
* Para popular via API (testar validações reais), use os endpoints `POST /coord/*`.
* Se alterar `models.py`, crie uma migration Alembic ou recrie o DB em dev.

---

## Docker

Há `Dockerfile` e `docker-compose.yml`. Para rodar com Docker (dev):

```bash
docker-compose build
docker-compose up
```

Verifique se `DATABASE_URL` no compose aponta para volume correto.

---

## Segurança e produção

* Não habilitar `seed_db` automático em produção.
* Usar PostgreSQL (ou outro RDBMS) em produção. Ajuste `DATABASE_URL`.
* Configurar autenticação/ACLs para rotas de coordenação/professor.

---

## Contato / próximos passos sugeridos

* Mapear frontend → backend para o formato de horários (adicionar mapeamento `SegM -> M12` se preferir manter o frontend).
* Integrar solver (OR-Tools / OptaPlanner) em `run_solver.py` com o modelo atual.
* Criar endpoints CRUD para `Aluno` (facilita testes) ou interface de admin.

---

Se quiser eu já:

* **gero o `Makefile`** com `make run`, `make seed`, `make test`;
* ou **adapto o backend** para aceitar os blocos do frontend (`SegM` → `M12`) e te passo o diff.

