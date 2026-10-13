# Carteira de clientes 39A

Ferramenta interna para importar as planilhas dos parceiros, buscar clientes por nome, CPF ou CNPJ e ver a ficha do cliente com os vínculos, o histórico de alterações (valor antigo e novo de cada campo) e a proposta de crédito.

| Parte | Tecnologia |
|---|---|
| Front-end | React 18, TypeScript (strict), Vite 8, React Router 7, TanStack Query 5 |
| Back-end | Python 3.13, FastAPI, SQLAlchemy 2, Alembic, Pydantic 2 |
| Banco | PostgreSQL 16 (extensão `pg_trgm`) |
| Importação | Worker em processo separado, fila na própria tabela do PostgreSQL |

Documentos:
- [`DECISOES.md`](DECISOES.md): decisões técnicas e trade-offs
- [`docs/modelo-de-dados.md`](docs/modelo-de-dados.md): diagrama do modelo de dados e constraints
- [`frontend/README.md`](frontend/README.md): estrutura e decisões do front

---

## Como rodar com Docker (recomendado)

Pré-requisitos: Docker 24+ com Docker Compose v2.

```bash
docker compose up --build
```

Isso sobe, em ordem: o banco, as migrations (rodam uma vez e terminam), a API, o worker e o front.

| O quê | Endereço |
|---|---|
| Aplicação | http://localhost:8080 |
| API | http://localhost:8000/api |
| Documentação interativa da API | http://localhost:8000/docs |
| PostgreSQL | `localhost:5432`, usuário `carteira`, senha `carteira` |

Não há variáveis de ambiente para configurar: o `docker-compose.yml` já define tudo. Para mudar algo, as opções estão em [`backend/.env.example`](backend/.env.example).

### Importar o arquivo de exemplo

Pela tela: abra http://localhost:8080, clique em **Importar planilha** e escolha `backend/exemplos/exemplo-carga-clientes.xlsx` (ou o `.csv`).

Ou pela linha de comando (seed):

```bash
docker compose exec api python -m app.seed exemplos/exemplo-carga-clientes.xlsx
```

**Resultado esperado:** 116 linhas, **98 importadas e 18 rejeitadas**, que geram 97 clientes, 8 empresas e 97 vínculos. A linha 103 é cópia exata da 12, por isso há uma importada a mais que clientes. Na tela da importação, a aba **Aceitas** mostra cada linha aceita e o que ela fez (a linha 103 aparece como "Repetida no arquivo"), e a aba **Rejeitadas** mostra o motivo de cada rejeição (explicados em [DECISOES.md, item 5](DECISOES.md#5-regras-de-validação-além-das-listadas)). Importar o mesmo arquivo de novo dá o mesmo resultado e não duplica nada.

### Rodar os testes

```bash
docker compose exec api python -m pytest        # back-end, no banco carteira_teste (separado do da aplicação)
```

A imagem final do front é só o nginx com os arquivos prontos, sem Node. Para rodar os testes do front, use `npm test` (passo a passo sem Docker, abaixo).

---

## Como rodar sem Docker

Pré-requisitos: Python 3.13, Node 20+ (testado com 22) e PostgreSQL 16 com a extensão `pg_trgm` (vem no pacote `postgresql-contrib`).

### 1. Banco

```bash
createdb carteira
createdb carteira_teste
```

### 2. Back-end

```bash
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                 # ajuste DATABASE_URL para o seu usuário e senha

alembic upgrade head                 # cria as tabelas
uvicorn app.main:app --port 8000     # API em http://localhost:8000
```

Em outro terminal, com o mesmo ambiente ativado:

```bash
cd backend && source .venv/bin/activate
python -m app.worker                 # processa as importações
```

Seed (opcional): `python -m app.seed exemplos/exemplo-carga-clientes.xlsx`

### 3. Front-end

```bash
cd frontend
npm install
npm run dev                          # http://localhost:5173 (o /api vai para a porta 8000)
```

### 4. Testes

```bash
cd backend && python -m pytest       # 83 testes; precisa do banco carteira_teste
cd frontend && npm test              # 17 testes
```

Se o banco de testes estiver em outro endereço, use `TEST_DATABASE_URL=postgresql+psycopg://usuario:senha@host:5432/carteira_teste`. A suíte apaga e recria o schema desse banco, por isso ela **nunca** usa o `DATABASE_URL` da aplicação.

---

## O que os testes cobrem

| Área | Arquivo |
|---|---|
| Normalização: CPF e CNPJ com e sem máscara, datas mistas e seriais do Excel, valores `R$ 4.519,96` e `4519.96`, nomes | `backend/tests/test_normalizacao.py` |
| Validação de linha: cada regra da 3.3, todos os motivos juntos, arquivo de exemplo `.csv` e `.xlsx` | `backend/tests/test_validacao.py` |
| Importação de ponta a ponta: API, worker e banco, linhas inválidas, reimportação sem duplicar, **queda no meio e retomada por outro worker**, edição manual x reimportação, cliente excluído | `backend/tests/test_importacao.py` |
| Busca: nome sem acento, CPF com e sem máscara, CNPJ, filtros combinados, ordenação e paginação; ficha da empresa | `backend/tests/test_busca.py` |
| Linhas aceitas: resultado de cada linha (cliente novo, vínculo novo, atualizou, sem mudança, repetida), filtro e contagem | `backend/tests/test_linhas_importadas.py` |
| Apagar uma importação: prévia, cliente que está em duas planilhas, empresa que fica sem vínculo, em andamento | `backend/tests/test_exclusao.py` |
| Histórico do cliente: criação, valores antigos e novos, vínculo novo, reimportação sem mudança, edição manual, importação apagada | `backend/tests/test_historico.py` |
| Motor: determinismo, faixas, janela deslizante e 429 com `Retry-After` | `backend/tests/test_motor.py` |
| Cálculo da parcela e comparação com a margem | `frontend/src/__tests__/parcela.test.ts` |
| Cliente HTTP: 429, 422 com erros por campo, falha de rede | `frontend/src/__tests__/http.test.ts` |
| Formatação pt-BR: CPF, CNPJ, moeda, datas sem deslocamento de fuso | `frontend/src/__tests__/format.test.ts` |
| Valores do histórico formatados por campo | `frontend/src/__tests__/historico.test.ts` |

---

## Estrutura

```
backend/
  app/
    main.py                 API (FastAPI) e tratamento de erros
    worker.py               processo que consome a fila de importações
    seed.py                 importação pela linha de comando
    historico.py            diff antes/depois e gravação do histórico do cliente
    importacao/
      leitura.py            XLSX e CSV -> linhas
      normalizacao.py       funções puras: CPF, datas, valores, nomes...
      validacao.py          regras da seção 3.3 para uma linha
      processador.py        fila, lotes, checkpoint, upserts, conflitos
    motor/                  motor de proposta simulado e rate limit
    rotas/                  endpoints de clientes, empresas, importações e resumo
  migrations/               Alembic (schema, constraints e índices)
  tests/
  exemplos/                 arquivos de exemplo do case
frontend/
  src/api/                  único ponto que fala com a API
  src/pages/                uma tela por rota
docker-compose.yml
DECISOES.md
docs/modelo-de-dados.md
```

## API

| Método | Rota | O que faz |
|---|---|---|
| POST | `/api/importacoes` | Recebe o arquivo (`multipart`, campo `arquivo`) e responde `202` na hora |
| GET | `/api/importacoes` | Histórico, paginado |
| GET | `/api/importacoes/{id}/exclusao` | Prévia do que sai ao apagar a importação (não apaga nada) |
| DELETE | `/api/importacoes/{id}` | Apaga a importação e só o que existia apenas nela; `409` se estiver em andamento |
| GET | `/api/importacoes/{id}` | Status e progresso |
| GET | `/api/importacoes/{id}/linhas-importadas?resultado=&pagina=` | Linhas aceitas: cliente, empresa, matrícula e o que cada uma fez (cliente novo, vínculo novo, atualizou, sem mudança, repetida), com contagem por resultado |
| GET | `/api/importacoes/{id}/linhas-invalidas` | Linhas rejeitadas com motivos, paginado |
| GET | `/api/clientes?nome=&documento=&ordem=nome\|importacao&direcao=asc\|desc&pagina=&tamanho=` | Busca |
| GET / PUT / DELETE | `/api/clientes/{id}` | Ficha, edição, exclusão lógica |
| GET | `/api/clientes/{id}/historico?pagina=` | Histórico de alterações do cliente (mais recente primeiro), paginado |
| GET | `/api/empresas?busca=&pagina=` | Lista de empresas |
| GET / PUT | `/api/empresas/{id}` | Empresa (com total de vínculos e margem somada), edição |
| GET | `/api/empresas/{id}/vinculos?nome=&pagina=` | Clientes vinculados à empresa, paginado |
| GET | `/api/resumo` | Totais do painel |
| GET | `/api/motor/proposta?cpf=` | Proposta; `429` com `Retry-After` acima de 10 consultas por minuto |

Todo erro volta como `{"mensagem": "...", "erros": {"campo": "..."}}`. Campos aninhados usam ponto (`endereco.cep`), e a tela mostra cada um no campo certo. Detalhes em http://localhost:8000/docs.
