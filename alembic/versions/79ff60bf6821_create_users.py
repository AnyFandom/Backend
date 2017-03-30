"""Create users

Revision ID: 79ff60bf6821
Revises: b205a6eb0a83
Create Date: 2017-03-30 14:20:13.621505

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '79ff60bf6821'
down_revision = 'b205a6eb0a83'
branch_labels = None
depends_on = None


def upgrade():
    op.get_bind().execute(sa.sql.text("""
        CREATE TABLE auth (
            PRIMARY KEY (id),
            UNIQUE (username),

            id            BIGINT                         NOT NULL,
            username      CITEXT                         NOT NULL,
            password_hash VARCHAR(130)                   NOT NULL,
            random        UUID DEFAULT gen_random_uuid() NOT NULL
        );
    
        CREATE SEQUENCE us_id_seq;
        CREATE TABLE user_statics (
            PRIMARY KEY (id),
            UNIQUE (username),
            
            id         BIGINT                    NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
            username   CITEXT                    NOT NULL
        );
        
        CREATE TABLE user_versions (
            PRIMARY KEY (id, edited_at),
            
            id          BIGINT                    NOT NULL,
            edited_at   TIMESTAMPTZ DEFAULT now() NOT NULL,
            edited_by   BIGINT                    NOT NULL,
            description TEXT DEFAULT ''           NOT NULL,
            avatar      VARCHAR(64) DEFAULT ''    NOT NULL
        );
        
        CREATE VIEW users AS (
            SELECT us.id, us.created_at, uv.edited_at, uv.edited_by,
                   us.username, uv.description, uv.avatar
              FROM user_statics AS us
                   INNER JOIN user_versions AS uv
                   ON uv.id = us.id
                      AND uv.edited_at =
                          (SELECT max(uv2.edited_at)
                             FROM user_versions AS uv2
                            WHERE uv2.id = us.id)
        );
        
        CREATE FUNCTION users_functions () RETURNS TRIGGER AS $$
            BEGIN
                IF TG_OP = 'INSERT' THEN
                    
                    INSERT INTO user_statics (id, created_at, username)
                    VALUES (NEW.id, NEW.created_at, NEW.username);
                    
                    INSERT INTO user_versions (id, edited_at, edited_by)
                    VALUES (NEW.id, NEW.created_at, NEW.id);
                    
                    RETURN NEW;
                    
                ELSIF TG_OP = 'UPDATE' THEN
                    
                    NEW.description = COALESCE(NEW.description, OLD.description);
                    NEW.avatar = COALESCE(NEW.avatar, OLD.avatar);
                    
                    IF (NEW.description, NEW.avatar) = (OLD.description, OLD.avatar) THEN
                        RETURN NULL;
                    END IF;
                    
                    INSERT INTO user_versions (id, edited_at, edited_by, description, avatar)
                    VALUES (OLD.id, now(), NEW.edited_by, NEW.description, NEW.avatar);
                    
                    RETURN NEW;
                    
                ELSIF TG_OP = 'DELETE' THEN
                    RETURN NULL;
                END IF;
            END;
        $$ LANGUAGE plpgsql;
        
        CREATE TRIGGER users_trig INSTEAD OF INSERT OR UPDATE OR DELETE 
        ON users FOR EACH ROW EXECUTE PROCEDURE users_functions ();
        
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
        
        CREATE FUNCTION users_create (
            username      VARCHAR(120),
            password_hash VARCHAR(130)
        ) RETURNS BIGINT AS $$
            BEGIN
                INSERT INTO users (id, created_at, username)
                VALUES (nextval('us_id_seq'), now(), username);
                
                INSERT INTO auth (id, username, password_hash)
                VALUES (currval('us_id_seq'), username, password_hash);
                
                RETURN currval('us_id_seq');
            END;
        $$ LANGUAGE plpgsql;
        
        CREATE FUNCTION users_history (
            target_id BIGINT
        ) RETURNS SETOF users AS $$
            SELECT us.id, us.created_at, uv.edited_at, uv.edited_by,
                   us.username, uv.description, uv.avatar
              FROM user_statics as us
                   INNER JOIN user_versions as uv
                   ON uv.id = us.id
             WHERE us.id = target_id;
         $$ LANGUAGE sql;
    """))


def downgrade():
    op.get_bind().execute(sa.sql.text("""
        DROP FUNCTION users_history (BIGINT);
        DROP FUNCTION users_create (VARCHAR, VARCHAR);
        DROP FUNCTION users_history_check (BIGINT, BIGINT);
        DROP FUNCTION users_update_check (BIGINT, BIGINT);
        DROP TRIGGER users_trig ON users;
        DROP FUNCTION users_functions ();
        DROP VIEW users;
        DROP SEQUENCE us_id_seq;
        DROP TABLE user_statics;
        DROP TABLE user_versions;
        DROP TABLE auth;
    """))
