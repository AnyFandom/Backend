"""Init

Revision ID: b205a6eb0a83
Revises:
Create Date: 2017-03-30 14:04:12.872287

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b205a6eb0a83'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.get_bind().execute(sa.sql.text("""
        CREATE EXTENSION CITEXT;
        CREATE EXTENSION PGCRYPTO;
    """))


def downgrade():
    op.get_bind().execute(sa.sql.text("""
        DROP EXTENSION CITEXT;
        DROP EXTENSION PGCRYPTO;
    """))
