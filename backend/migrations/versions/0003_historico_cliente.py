from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE alteracoes_cliente (
            id             bigserial    PRIMARY KEY,
            cliente_id     bigint       NOT NULL REFERENCES clientes (id) ON DELETE CASCADE,
            origem         varchar(10)  NOT NULL CHECK (origem IN ('IMPORTACAO', 'EDICAO')),
            acao           varchar(12)  NOT NULL CHECK (acao IN ('CRIACAO', 'ATUALIZACAO')),
            importacao_id  bigint       REFERENCES importacoes (id) ON DELETE SET NULL,
            descricao      varchar(300) NOT NULL,
            mudancas       jsonb        NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(mudancas) = 'array'),
            criado_em      timestamptz  NOT NULL DEFAULT now(),
            CHECK (acao = 'CRIACAO' OR jsonb_array_length(mudancas) > 0)
        )
        """
    )
    op.execute("CREATE INDEX ix_alteracoes_cliente ON alteracoes_cliente (cliente_id, criado_em DESC, id DESC)")

    op.execute(
        """
        INSERT INTO alteracoes_cliente (cliente_id, origem, acao, importacao_id, descricao, criado_em)
        SELECT c.id, 'IMPORTACAO', 'CRIACAO', i.id,
               'Importação #' || i.id || ' (' || i.arquivo_nome || ')', c.criado_em
          FROM clientes c
          JOIN importacoes i ON i.id = c.importacao_origem_id
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE alteracoes_cliente")
