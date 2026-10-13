# Modelo de dados

```mermaid
erDiagram
    IMPORTACOES ||--o{ LINHAS_INVALIDAS : "rejeita"
    IMPORTACOES ||--o{ LINHAS_IMPORTADAS : "aceita"
    CLIENTES ||--o{ LINHAS_IMPORTADAS : "veio de"
    VINCULOS ||--o{ LINHAS_IMPORTADAS : "veio de"
    IMPORTACOES ||--o{ CLIENTES : "origem / última atualização"
    IMPORTACOES ||--o{ EMPRESAS : "origem / última atualização"
    IMPORTACOES ||--o{ VINCULOS : "origem / última atualização"
    IMPORTACOES ||--o{ VINCULO_IMPORTACOES : "trouxe"
    VINCULOS ||--o{ VINCULO_IMPORTACOES : "apareceu em"
    CLIENTES ||--o{ VINCULOS : "tem"
    EMPRESAS ||--o{ VINCULOS : "emprega"
    CLIENTES ||--o{ ALTERACOES_CLIENTE : "histórico"
    IMPORTACOES |o--o{ ALTERACOES_CLIENTE : "causou (SET NULL ao apagar)"

    IMPORTACOES {
        bigint id PK
        varchar arquivo_nome
        char64 arquivo_hash "SHA-256"
        bytea conteudo
        varchar status "PENDENTE | PROCESSANDO | CONCLUIDA | FALHOU"
        int total_linhas
        int processadas "= importadas + invalidas"
        int importadas
        int invalidas
        int proxima_linha "checkpoint da retomada"
        int tentativas
        text erro
        varchar worker_id
        timestamptz heartbeat_em "lease do worker"
        timestamptz criada_em
        timestamptz finalizada_em
    }

    ALTERACOES_CLIENTE {
        bigint id PK
        bigint cliente_id FK "ON DELETE CASCADE"
        varchar origem "IMPORTACAO | EDICAO"
        varchar acao "CRIACAO | ATUALIZACAO"
        bigint importacao_id FK "ON DELETE SET NULL"
        varchar descricao "Importação #N (arquivo)"
        jsonb mudancas "[{campo, rotulo, contexto, antes, depois}]"
        timestamptz criado_em
    }

    VINCULO_IMPORTACOES {
        bigint importacao_id PK "FK, ON DELETE CASCADE"
        bigint vinculo_id PK "FK, ON DELETE CASCADE"
    }

    LINHAS_INVALIDAS {
        bigint id PK
        bigint importacao_id FK "UNIQUE (importacao_id, linha)"
        int linha
        text_array motivos
        varchar cpf "como veio na planilha"
        varchar nome "como veio na planilha"
    }

    LINHAS_IMPORTADAS {
        bigint id PK
        bigint importacao_id FK "UNIQUE (importacao_id, linha)"
        int linha "NULL só em importações antigas"
        bigint cliente_id FK
        bigint vinculo_id FK
        varchar resultado "NOVO_CLIENTE | NOVO_VINCULO | ATUALIZADA | SEM_MUDANCA | REPETIDA"
    }

    CLIENTES {
        bigint id PK
        char11 cpf UK
        varchar nome
        varchar nome_busca "sem acento, minúsculas"
        date data_nascimento
        char1 sexo "F | M"
        varchar estado_civil
        varchar email
        varchar telefone
        char8 cep
        varchar logradouro
        varchar numero
        varchar complemento
        varchar bairro
        varchar cidade
        char2 uf
        bigint importacao_origem_id FK
        bigint ultima_importacao_id FK
        timestamptz ultima_importacao_em
        timestamptz editado_em "edição manual vence a planilha"
        timestamptz excluido_em "exclusão lógica"
    }

    EMPRESAS {
        bigint id PK
        char14 cnpj UK
        varchar razao_social
        varchar nome_fantasia
        varchar setor
        varchar cidade
        char2 uf
        bigint importacao_origem_id FK
        bigint ultima_importacao_id FK
        timestamptz editado_em
    }

    VINCULOS {
        bigint id PK
        bigint cliente_id FK "UNIQUE (cliente_id, empresa_id, matricula)"
        bigint empresa_id FK
        varchar matricula
        varchar cargo
        date data_admissao
        numeric salario_bruto "CHECK >= 0"
        numeric margem_disponivel "CHECK 0 <= margem <= salario"
        bigint importacao_origem_id FK
        bigint ultima_importacao_id FK
    }
```

## Por que este formato

- **`vinculo_importacoes` guarda todas as importações em que cada vínculo apareceu**, não só a primeira e a última. É o que permite apagar uma importação sem levar junto clientes que também vieram de outras planilhas (DECISOES.md, item 10).
- **`linhas_importadas` e `linhas_invalidas` se espelham**: toda linha processada está em uma das duas, então a aba "Aceitas" bate com o contador de importadas (DECISOES.md, item 11).
- **`alteracoes_cliente` guarda o valor antigo e o novo de cada campo que mudou**, por importação ou edição manual. Se a importação for apagada, o histórico fica (DECISOES.md, item 8).
- **Empresa é entidade**, não coluna repetida: aparece em dezenas de linhas e é editada num lugar só.
- **Matrícula, cargo, admissão, salário e margem são do vínculo**, não do cliente: a mesma pessoa pode ter dois empregos ao mesmo tempo, cada um com sua margem.
- **Cidade e UF ficam como texto normalizado** (UF validada contra a lista oficial). Uma tabela de municípios exigiria o código IBGE, que a planilha não traz.

## Constraints no banco

| Regra | Onde |
|---|---|
| CPF e CNPJ só com dígitos e no tamanho certo | `CHECK (cpf ~ '^[0-9]{11}$')`, `CHECK (cnpj ~ '^[0-9]{14}$')` |
| CPF, CNPJ e vínculo únicos | `uq_clientes_cpf`, `uq_empresas_cnpj`, `uq_vinculos_cliente_empresa_matricula` |
| Margem entre zero e o salário | `CHECK (margem_disponivel >= 0)`, `CHECK (margem_disponivel <= salario_bruto)` |
| Contadores coerentes | `CHECK (processadas = importadas + invalidas)`, `CHECK (processadas <= total_linhas)` |
| Status conhecido | `CHECK (status IN (...))` |
| Linha rejeitada ou aceita não duplica na retomada | `uq_linha_invalida`, `uq_linha_importada (importacao_id, linha)` |
| Resultado da linha conhecido | `CHECK (resultado IN (...))` |
| Cada aparição de um vínculo numa importação, uma vez só | PK `vinculo_importacoes (importacao_id, vinculo_id)` |
| Histórico sempre com lista de mudanças; só "criação" pode vir vazia | `CHECK (jsonb_typeof(mudancas) = 'array')`, `CHECK (acao = 'CRIACAO' OR jsonb_array_length(mudancas) > 0)` |
| Integridade referencial | Todas as FKs acima |

Os índices e o motivo de cada um estão em [DECISOES.md, item 7](../DECISOES.md#7-busca-e-índices).
