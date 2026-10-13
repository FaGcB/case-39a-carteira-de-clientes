from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.execute(
        """
        CREATE TABLE importacoes (
            id              bigserial PRIMARY KEY,
            arquivo_nome    varchar(255) NOT NULL,
            arquivo_hash    char(64)     NOT NULL,
            conteudo        bytea        NOT NULL,
            status          varchar(12)  NOT NULL DEFAULT 'PENDENTE'
                            CHECK (status IN ('PENDENTE', 'PROCESSANDO', 'CONCLUIDA', 'FALHOU')),
            total_linhas    integer      CHECK (total_linhas >= 0),
            processadas     integer      NOT NULL DEFAULT 0 CHECK (processadas >= 0),
            importadas      integer      NOT NULL DEFAULT 0 CHECK (importadas >= 0),
            invalidas       integer      NOT NULL DEFAULT 0 CHECK (invalidas >= 0),
            proxima_linha   integer      NOT NULL DEFAULT 0 CHECK (proxima_linha >= 0),
            tentativas      integer      NOT NULL DEFAULT 0,
            erro            text,
            worker_id       varchar(64),
            heartbeat_em    timestamptz,
            criada_em       timestamptz  NOT NULL DEFAULT now(),
            iniciada_em     timestamptz,
            finalizada_em   timestamptz,
            CHECK (processadas = importadas + invalidas),
            CHECK (total_linhas IS NULL OR processadas <= total_linhas)
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_importacoes_fila ON importacoes (status, heartbeat_em) "
        "WHERE status IN ('PENDENTE', 'PROCESSANDO')"
    )

    op.execute(
        """
        CREATE TABLE linhas_invalidas (
            id             bigserial PRIMARY KEY,
            importacao_id  bigint  NOT NULL REFERENCES importacoes (id) ON DELETE CASCADE,
            linha          integer NOT NULL CHECK (linha > 0),
            motivos        text[]  NOT NULL CHECK (cardinality(motivos) > 0),
            cpf            varchar(32),
            nome           varchar(255),
            CONSTRAINT uq_linha_invalida UNIQUE (importacao_id, linha)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE empresas (
            id                    bigserial PRIMARY KEY,
            cnpj                  char(14)     NOT NULL CHECK (cnpj ~ '^[0-9]{14}$'),
            razao_social          varchar(150) NOT NULL CHECK (btrim(razao_social) <> ''),
            nome_fantasia         varchar(150) NOT NULL,
            setor                 varchar(100) NOT NULL,
            cidade                varchar(100) NOT NULL,
            uf                    char(2)      NOT NULL CHECK (uf ~ '^[A-Z]{2}$'),
            importacao_origem_id  bigint REFERENCES importacoes (id),
            ultima_importacao_id  bigint REFERENCES importacoes (id),
            editado_em            timestamptz,
            criado_em             timestamptz  NOT NULL DEFAULT now(),
            atualizado_em         timestamptz  NOT NULL DEFAULT now(),
            CONSTRAINT uq_empresas_cnpj UNIQUE (cnpj)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE clientes (
            id                    bigserial PRIMARY KEY,
            cpf                   char(11)     NOT NULL CHECK (cpf ~ '^[0-9]{11}$'),
            nome                  varchar(150) NOT NULL CHECK (btrim(nome) <> ''),
            nome_busca            varchar(150) NOT NULL,
            data_nascimento       date         NOT NULL,
            sexo                  char(1)      CHECK (sexo IN ('F', 'M')),
            estado_civil          varchar(30),
            email                 varchar(150),
            telefone              varchar(11)  CHECK (telefone ~ '^[0-9]{10,11}$'),
            cep                   char(8)      CHECK (cep ~ '^[0-9]{8}$'),
            logradouro            varchar(150),
            numero                varchar(20),
            complemento           varchar(100),
            bairro                varchar(100),
            cidade                varchar(100),
            uf                    char(2)      CHECK (uf ~ '^[A-Z]{2}$'),
            importacao_origem_id  bigint REFERENCES importacoes (id),
            ultima_importacao_id  bigint REFERENCES importacoes (id),
            ultima_importacao_em  timestamptz,
            editado_em            timestamptz,
            excluido_em           timestamptz,
            criado_em             timestamptz  NOT NULL DEFAULT now(),
            atualizado_em         timestamptz  NOT NULL DEFAULT now(),
            CONSTRAINT uq_clientes_cpf UNIQUE (cpf)
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_clientes_nome_busca_trgm ON clientes "
        "USING gin (nome_busca gin_trgm_ops) WHERE excluido_em IS NULL"
    )
    op.execute("CREATE INDEX ix_clientes_cpf_prefixo ON clientes (cpf bpchar_pattern_ops) WHERE excluido_em IS NULL")
    op.execute("CREATE INDEX ix_clientes_ordem_nome ON clientes (nome_busca, id) WHERE excluido_em IS NULL")
    op.execute(
        "CREATE INDEX ix_clientes_ordem_importacao ON clientes (ultima_importacao_em, id) WHERE excluido_em IS NULL"
    )

    op.execute(
        """
        CREATE TABLE vinculos (
            id                    bigserial PRIMARY KEY,
            cliente_id            bigint        NOT NULL REFERENCES clientes (id),
            empresa_id            bigint        NOT NULL REFERENCES empresas (id),
            matricula             varchar(30)   NOT NULL CHECK (btrim(matricula) <> ''),
            cargo                 varchar(100)  NOT NULL,
            data_admissao         date          NOT NULL,
            salario_bruto         numeric(12,2) NOT NULL CHECK (salario_bruto >= 0),
            margem_disponivel     numeric(12,2) NOT NULL CHECK (margem_disponivel >= 0),
            importacao_origem_id  bigint REFERENCES importacoes (id),
            ultima_importacao_id  bigint REFERENCES importacoes (id),
            criado_em             timestamptz   NOT NULL DEFAULT now(),
            atualizado_em         timestamptz   NOT NULL DEFAULT now(),
            CHECK (margem_disponivel <= salario_bruto),
            CONSTRAINT uq_vinculos_cliente_empresa_matricula UNIQUE (cliente_id, empresa_id, matricula)
        )
        """
    )
    op.execute("CREATE INDEX ix_vinculos_empresa ON vinculos (empresa_id, cliente_id)")


def downgrade() -> None:
    op.execute("DROP TABLE vinculos")
    op.execute("DROP TABLE clientes")
    op.execute("DROP TABLE empresas")
    op.execute("DROP TABLE linhas_invalidas")
    op.execute("DROP TABLE importacoes")
