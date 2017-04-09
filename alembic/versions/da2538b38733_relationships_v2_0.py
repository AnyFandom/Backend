"""Relationships v2.0

Revision ID: da2538b38733
Revises: 834a6e120048
Create Date: 2017-04-06 22:09:20.014622

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'da2538b38733'
down_revision = '834a6e120048'
branch_labels = None
depends_on = None


def upgrade():
    op.get_bind().execute(sa.sql.text("""
        DROP TABLE relationships;
        DROP FUNCTION check_rels (target_type, BIGINT, BIGINT, VARCHAR(8)[]);
        DROP TYPE target_type;
        DROP TYPE role_type;
              
        CREATE TABLE admins (
            PRIMARY KEY (user_id),
            
            user_id BIGINT NOT NULL
        );

        CREATE TABLE fandom_moders (
            PRIMARY KEY (user_id, target_id),

            user_id   BIGINT NOT NULL,
            target_id BIGINT NOT NULL,
            set_by    BIGINT NOT NULL,
            edit_f    BOOL   NOT NULL,
            manage_f  BOOL   NOT NULL,
            ban_f     BOOL   NOT NULL,
            create_b  BOOL   NOT NULL,
            edit_b    BOOL   NOT NULL,
            remove_b  BOOL   NOT NULL,
            edit_p    BOOL   NOT NULL,
            remove_p  BOOL   NOT NULL,
            edit_c    BOOL   NOT NULL,
            remove_c  BOOL   NOT NULL
        );
        
        CREATE TABLE fandom_bans (
            PRIMARY KEY (user_id, target_id), 
            
            user_id   BIGINT      NOT NULL,
            target_id BIGINT      NOT NULL,
            set_by    BIGINT      NOT NULL,
            reason    VARCHAR(32) NOT NULL,
            until     TIMESTAMPTZ NOT NULL
        );
        
        CREATE OR REPLACE FUNCTION fandoms_create (
            user_id     BIGINT,
            url         CITEXT,
            title       VARCHAR(120),
            description TEXT,
            avatar      VARCHAR(64)
        ) RETURNS BIGINT AS $$
            BEGIN
                INSERT INTO fandoms (id, created_at, url, title, description, avatar)
                VALUES (nextval('fs_id_seq'), now(), url, title, description, avatar);
                
                INSERT INTO fandom_staff
                VALUES (user_id, nextval('fs_id_seq'), user_id,
                        TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE, TRUE);
                
                RETURN currval('fs_id_seq');
            END;
        $$ LANGUAGE plpgsql;
"""))


def downgrade():
    op.get_bind().execute(sa.sql.text("""
        CREATE OR REPLACE FUNCTION fandoms_create (
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
        
        DROP TABLE fandom_moders;
        DROP TABLE fandom_bans;

        CREATE TYPE role_type AS ENUM (
            'owner', 'admin', 'moder', 'writer', 'sub', 'banned'
        );

        CREATE TYPE target_type AS ENUM (
            'site', 'fandom', 'blog', 'post', 'comment'
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
