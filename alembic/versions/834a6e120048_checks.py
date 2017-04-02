"""Checks

Revision ID: 834a6e120048
Revises: feec9225cdfa
Create Date: 2017-04-02 12:30:05.032950

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '834a6e120048'
down_revision = 'feec9225cdfa'
branch_labels = None
depends_on = None


def upgrade():
    op.get_bind().execute(sa.sql.text("""
        DROP FUNCTION users_update_check (BIGINT, BIGINT);
        DROP FUNCTION users_history_check (BIGINT, BIGINT);
        DROP FUNCTION fandoms_create_check (BIGINT);
        DROP FUNCTION fandoms_update_check (BIGINT, BIGINT);
        DROP FUNCTION fandoms_history_check (BIGINT, BIGINT);

        CREATE FUNCTION check_rels (
            v_target_type target_type,
            v_target_id BIGINT,
            v_user_id BIGINT,
            roles varchar(8)[]
        ) RETURNS BOOLEAN AS $$
            SELECT EXISTS(
                SELECT 1 FROM relationships
                 WHERE target_type = v_target_type
                   AND target_id = v_target_id
                   AND user_id = v_user_id
                   AND role = ANY(roles::role_type[])
                   AND until > now()
            )
        $$ LANGUAGE sql;
    """))


def downgrade():
    op.get_bind().execute(sa.sql.text("""
        DROP FUNCTION check_rels (target_type, BIGINT, BIGINT, role_type[]);
        
        CREATE FUNCTION fandoms_history_check (
            f_target_id BIGINT,
            f_user_id   BIGINT
        ) RETURNS VOID AS $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM relationships
                                WHERE target_type = 'fandom'
                                  AND target_id = f_target_id
                                  AND user_id = f_user_id
                                  AND role = 'admin') THEN
                    RAISE EXCEPTION 'FORBIDDEN';
                END IF;
            END;
        $$ LANGUAGE plpgsql;
        
        CREATE FUNCTION fandoms_update_check (
            f_target_id BIGINT,
            f_user_id   BIGINT
        ) RETURNS VOID AS $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM relationships
                                WHERE target_type = 'fandom'
                                  AND target_id = f_target_id
                                  AND user_id = f_user_id
                                  AND role = 'admin') THEN
                    RAISE EXCEPTION 'FORBIDDEN';
                END IF;
            END;
        $$ LANGUAGE plpgsql;
        
        CREATE FUNCTION fandoms_create_check (
            user_id BIGINT
        ) RETURNS VOID AS $$
            BEGIN
                IF user_id = 0 THEN
                    RAISE EXCEPTION 'FORBIDDEN';
                END IF;
            END;
        $$ LANGUAGE plpgsql;
        
        CREATE FUNCTION users_history_check (
            target_id BIGINT,
            user_id   BIGINT
        ) RETURNS VOID AS $$
            BEGIN
                IF target_id != user_id THEN
                    RAISE EXCEPTION 'FORBIDDEN';
                END IF;
            END;
        $$ LANGUAGE plpgsql;
        
        CREATE FUNCTION users_update_check (
            target_id BIGINT,
            user_id   BIGINT
        ) RETURNS VOID AS $$
            BEGIN
                IF target_id != user_id THEN
                    RAISE EXCEPTION 'FORBIDDEN';
                END IF;
            END;
        $$ LANGUAGE plpgsql;
    """))
