from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE linhas_importadas (
            id             bigserial    PRIMARY KEY,
            importacao_id  bigint       NOT NULL REFERENCES importacoes (id) ON DELETE CASCADE,
            linha          integer      CHECK (linha >= 2),
            cliente_id     bigint       NOT NULL REFERENCES clientes (id) ON DELETE CASCADE,
            vinculo_id     bigint       NOT NULL REFERENCES vinculos (id) ON DELETE CASCADE,
            resultado      varchar(14)  CHECK (resultado IN
                               ('NOVO_CLIENTE', 'NOVO_VINCULO', 'ATUALIZADA', 'SEM_MUDANCA', 'REPETIDA')),
            CONSTRAINT uq_linha_importada UNIQUE (importacao_id, linha)
        )
        """
    )
    op.execute("CREATE INDEX ix_linhas_importadas ON linhas_importadas (importacao_id, resultado, linha)")
    op.execute("CREATE INDEX ix_linhas_importadas_cliente ON linhas_importadas (cliente_id)")
    op.execute("CREATE INDEX ix_linhas_importadas_vinculo ON linhas_importadas (vinculo_id)")

    op.execute(
        """
        INSERT INTO linhas_importadas (importacao_id, cliente_id, vinculo_id)
        SELECT vi.importacao_id, v.cliente_id, v.id
          FROM vinculo_importacoes vi
          JOIN vinculos v ON v.id = vi.vinculo_id
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE linhas_importadas")
