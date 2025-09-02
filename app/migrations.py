from alembic import config, command
from alembic.runtime import migration

def apply_migrations():
    alembic_cfg = config.Config("./alembic.ini")
    command.upgrade(alembic_cfg, "head")