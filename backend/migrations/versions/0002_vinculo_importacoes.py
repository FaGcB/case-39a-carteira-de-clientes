from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE vinculo_importacoes (
            importacao_id  bigint NOT NULL REFERENCES importacoes (id) ON DELETE CASCADE,
            vinculo_id     bigint NOT NULL REFERENCES vinculos (id) ON DELETE CASCADE,
            PRIMARY KEY (importacao_id, vinculo_id)
        )
        """
    )
    op.execute("CREATE INDEX ix_vinculo_importacoes_vinculo ON vinculo_importacoes (vinculo_id, importacao_id)")

    op.execute(
        """
        INSERT INTO vinculo_importacoes (importacao_id, vinculo_id)
        SELECT importacao_origem_id, id FROM vinculos WHERE importacao_origem_id IS NOT NULL
        UNION
        SELECT ultima_importacao_id, id FROM vinculos WHERE ultima_importacao_id IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE vinculo_importacoes")
