from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from app.config import config as app_config

alembic_config = context.config
if alembic_config.config_file_name:
    fileConfig(alembic_config.config_file_name)


def run_migrations_online() -> None:
    engine = create_engine(app_config.database_url)
    with engine.connect() as conexao:
        context.configure(connection=conexao, target_metadata=None, transaction_per_migration=True)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
