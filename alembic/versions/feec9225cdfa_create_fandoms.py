"""Create fandoms

Revision ID: feec9225cdfa
Revises: 79ff60bf6821
Create Date: 2017-03-30 16:53:05.346361

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'feec9225cdfa'
down_revision = '79ff60bf6821'
branch_labels = None
depends_on = None


def upgrade():
    op.get_bind().execute(sa.sql.text("""
        CREATE TYPE target_type AS ENUM (
            'site', 'fandom', 'blog', 'post', 'comment'
        );
        
        CREATE TYPE role_type AS ENUM (
            'owner', 'admin', 'moder', 'writer', 'sub', 'banned'
        );
        
        CREATE TABLE relationships (
            PRIMARY KEY (user_id, target_id, target_type),
            
            user_id     BIGINT                         NOT NULL,
            target_id   BIGINT                         NOT NULL,
            target_type target_type                    NOT NULL,
            role        role_type                      NOT NULL,
            set_by      BIGINT                         NOT NULL,
            note        VARCHAR(64) DEFAULT ''         NOT NULL,
            until       TIMESTAMPTZ DEFAULT 'infinity' NOT NULL
        );
    
        CREATE SEQUENCE fs_id_seq;
        CREATE TABLE fandom_statics (
            PRIMARY KEY (id),
            UNIQUE (url),
            
            id         BIGINT                    NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
            url        CITEXT                    NOT NULL
        );
        
        CREATE TABLE fandom_versions (
            PRIMARY KEY (id, edited_at),
            
            id          BIGINT                    NOT NULL,
            edited_at   TIMESTAMPTZ DEFAULT now() NOT NULL,
            edited_by   BIGINT                    NOT NULL,
            title       VARCHAR(120)              NOT NULL,
            description TEXT DEFAULT ''           NOT NULL,
            avatar      VARCHAR(64) DEFAULT ''    NOT NULL
        );
        
        CREATE VIEW fandoms AS (
            SELECT fs.id, fs.created_at, fv.edited_at, fv.edited_by,
                   fv.title, fs.url, fv.description, fv.avatar
              FROM fandom_statics as fs
                   INNER JOIN fandom_versions AS fv
                   ON fv.id = fs.id
                      AND fv.edited_at =
                          (SELECT max(fv2.edited_at)
                             FROM fandom_versions AS fv2
                            WHERE fv2.id = fs.id)
        );
        
        CREATE FUNCTION fandoms_functions () RETURNS TRIGGER AS $$
            BEGIN
                IF TG_OP = 'INSERT' THEN
                
                    INSERT INTO fandom_statics (id, created_at, url)
                    VALUES (NEW.id, NEW.created_at, NEW.url);
                    
                    INSERT INTO fandom_versions (id, edited_at, edited_by, title, description, avatar)
                    VALUES (NEW.id, NEW.created_at, NEW.id, NEW.title, NEW.description, NEW.avatar);
                    
                    RETURN NEW;
                    
                ELSIF TG_OP = 'UPDATE' THEN
                    
                    NEW.title = COALESCE(NEW.title, OLD.title);
                    NEW.description = COALESCE(NEW.description, OLD.description);
                    NEW.avatar = COALESCE(NEW.avatar, OLD.avatar);
                    
                    IF (NEW.title, NEW.description, NEW.avatar) = (OLD.title, OLD.description, OLD.avatar) THEN
                        RETURN NULL;
                    END IF;
                    
                    INSERT INTO fandom_versions (id, edited_at, edited_by, title, description, avatar)
                    VALUES (OLD.id, now(), NEW.edited_by, NEW.title, NEW.description, NEW.avatar);
                    
                    RETURN NEW;
                    
                ELSIF TG_OP = 'DELETE' THEN
                    RETURN NULL;
                END IF;
            END;
        $$ LANGUAGE plpgsql;
        
        CREATE TRIGGER fandoms_trig INSTEAD OF INSERT OR UPDATE OR DELETE
        ON FANDOMS FOR EACH ROW EXECUTE PROCEDURE fandoms_functions ();
        
        CREATE FUNCTION fandoms_create_check (
            user_id BIGINT
        ) RETURNS VOID AS $$
            BEGIN
                IF user_id = 0 THEN
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
        
        CREATE FUNCTION fandoms_create (
            user_id     BIGINT,
            url         CITEXT,
            title       VARCHAR(120),
            description TEXT,
            avatar      VARCHAR(64)
        ) RETURNS BIGINT AS $$
            BEGIN
                INSERT INTO fandoms (id, created_at, url, title, description, avatar)
                VALUES (nextval('fs_id_seq'), now(), url, title, description, avatar);
                
                INSERT INTO relationships (user_id, target_id, target_type, role, set_by)
                VALUES (user_id, currval('fs_id_seq'), 'fandom', 'admin', user_id);
                
                RETURN currval('fs_id_seq');
            END;
        $$ LANGUAGE plpgsql;
        
        CREATE FUNCTION fandoms_history (
            target_id BIGINT
        ) RETURNS SETOF fandoms AS $$
            SELECT fs.id, fs.created_at, fv.edited_at, fv.edited_by,
                   fv.title, fs.url, fv.description, fv.avatar
              FROM fandom_statics as fs
                   INNER JOIN fandom_versions AS fv
                   ON fv.id = fs.id
        $$ LANGUAGE sql;
    """))


def downgrade():
    op.get_bind().execute(sa.sql.text("""
    DROP FUNCTION fandoms_history (BIGINT);
    DROP FUNCTION fandoms_create (BIGINT, CITEXT, VARCHAR, TEXT, VARCHAR);
    DROP FUNCTION fandoms_history_check (BIGINT, BIGINT);
    DROP FUNCTION fandoms_update_check (BIGINT, BIGINT);
    DROP FUNCTION fandoms_create_check (BIGINT);
    DROP TRIGGER fandoms_trig ON fandoms;
    DROP FUNCTION fandoms_functions ();
    DROP VIEW fandoms;
    DROP SEQUENCE fs_id_seq;
    DROP TABLE fandom_versions;
    DROP TABLE fandom_statics;
    DROP TABLE relationships;
    DROP TYPE role_type;
    DROP TYPE target_type;
    """))
