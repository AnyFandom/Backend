CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS pgcrypto;


-- RELATIONSHIPS


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


-- USERS


CREATE TABLE auth (
    PRIMARY KEY (id),
    UNIQUE (username),

    id            BIGINT                         NOT NULL,
    username      CITEXT                         NOT NULL,
    password_hash VARCHAR(130)                   NOT NULL,
    random        UUID DEFAULT gen_random_uuid() NOT NULL
);

CREATE TABLE user_statics (
    PRIMARY KEY (id),
    UNIQUE (username),

    id         BIGSERIAL                 NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    username   CITEXT                    NOT NULL
);

CREATE TABLE user_versions (
    PRIMARY KEY (id, edited_at),

    id            BIGINT                    NOT NULL,
    edited_at     TIMESTAMPTZ DEFAULT now() NOT NULL,
    edited_by     BIGINT                    NOT NULL,
    description   TEXT DEFAULT ''           NOT NULL,
    avatar        VARCHAR(64) DEFAULT ''    NOT NULL
);

CREATE VIEW users AS (
    SELECT us.id, us.created_at, uv.edited_at, uv.edited_by,
           us.username, uv.description, uv.avatar
      FROM user_statics as us
           INNER JOIN user_versions as uv
           ON uv.id = us.id
              AND uv.edited_at =
                  (SELECT max(uv2.edited_at)
                     FROM user_versions AS uv2
                    WHERE uv2.id = us.id)
);

CREATE OR REPLACE FUNCTION users_functions() RETURNS TRIGGER AS $function$
    BEGIN
      IF TG_OP = 'INSERT' THEN
        INSERT INTO user_statics (id, created_at, username)
        VALUES (NEW.id, now(), NEW.username);

        INSERT INTO user_versions (id, edited_at, edited_by)
        VALUES (NEW.id, now(), NEW.id);

        RETURN NEW;
      ELSIF TG_OP = 'UPDATE' THEN
        IF (NEW.description, NEW.avatar) = (OLD.description, OLD.avatar) THEN
          RETURN NULL;
        ELSE
          INSERT INTO user_versions (id, edited_at, edited_by, description,
                                       avatar)
          VALUES (OLD.id, now(), NEW.edited_by, NEW.description, NEW.avatar);

          RETURN NEW;
        END IF;
      ELSIF TG_OP = 'DELETE' THEN
        RETURN NULL;
      END IF;
    END;
  $function$ LANGUAGE plpgsql;

CREATE TRIGGER users_trig
INSTEAD OF INSERT OR UPDATE OR DELETE
ON users FOR EACH ROW
EXECUTE PROCEDURE users_functions();

CREATE OR REPLACE FUNCTION users_create(
  usern VARCHAR(120),
  passh VARCHAR(130)
) RETURNS BIGINT AS $function$
    BEGIN
      INSERT INTO users (id, username)
      VALUES (nextval('user_statics_id_seq'), usern);

      INSERT INTO auth (id, username, password_hash)
      VALUES (currval('user_statics_id_seq'), usern, passh);

      RETURN currval('user_statics_id_seq');
    END;
  $function$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION users_update(
  tid   BIGINT,
  uid   BIGINT,
  descr TEXT,
  avatr VARCHAR(64)
) RETURNS BOOLEAN AS $function$
    BEGIN
      IF tid != uid THEN  -- TODO: Сделать нормальную проверку
        RETURN FALSE;
      END IF;
      UPDATE users SET
        edited_at = DEFAULT, edited_by = uid,
        description = COALESCE(descr, description),
        avatar = COALESCE(avatr, avatar)
      WHERE id = tid;
      RETURN TRUE;
    END;
  $function$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION users_history(
  tid BIGINT,
  uid BIGINT
) RETURNS TABLE (id BIGINT, created_at TIMESTAMPTZ, edited_at TIMESTAMPTZ,
                 edited_by BIGINT, username CITEXT, description TEXT,
                 avatar VARCHAR(64)) AS $function$
    BEGIN
      IF tid != uid THEN  -- TODO: Сделать нормальную проверку
        RETURN;
      END IF;
      RETURN QUERY
      SELECT us.id, us.created_at, uv.edited_at, uv.edited_by,
             us.username, uv.description, uv.avatar
        FROM user_statics as us
             INNER JOIN user_versions as uv
             ON uv.id = us.id
       WHERE us.id = tid;
    END;
  $function$ LANGUAGE plpgsql;


-- FANDOMS


CREATE TABLE fandom_statics (
    PRIMARY KEY (id),
    UNIQUE (url),

    id         BIGSERIAL                 NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    url        CITEXT                    NOT NULL
);

CREATE TABLE fandom_versions (
    PRIMARY KEY (id, edited_at),

    id            BIGINT                    NOT NULL,
    edited_at     TIMESTAMPTZ DEFAULT now() NOT NULL,
    edited_by     BIGINT                    NOT NULL,
    title         VARCHAR(120)              NOT NULL,
    description   TEXT DEFAULT ''           NOT NULL,
    avatar        VARCHAR(64) DEFAULT ''    NOT NULL
);

CREATE VIEW fandoms AS (
    SELECT fs.id, fs.created_at, fv.edited_at, fv.edited_by,
           fv.title, fs.url, fv.description, fv.avatar, rl.user_id as owner
      FROM fandom_statics as fs
           INNER JOIN fandom_versions as fv
           ON fv.id = fs.id
              AND fv.edited_at =
                  (SELECT max(fv2.edited_at)
                     FROM fandom_versions AS fv2
                    WHERE fv2.id = fs.id)

           INNER JOIN relationships as rl
           ON rl.target_id = fs.id
              AND rl.target_type = 'fandom'
);

CREATE OR REPLACE FUNCTION fandoms_functions() RETURNS TRIGGER AS $function$
    BEGIN
      IF TG_OP = 'INSERT' THEN
        INSERT INTO fandom_statics (id, created_at, url)
        VALUES (NEW.id, now(), NEW.url);

        INSERT INTO fandom_versions (id, edited_at, edited_by, title,
                                     description, avatar)
        VALUES (NEW.id, now(), NEW.id, NEW.title, NEW.description, NEW.avatar);

        RETURN NEW;
      ELSIF TG_OP = 'UPDATE' THEN
        IF (NEW.description, NEW.avatar, NEW.title) =
           (OLD.description, OLD.avatar, OLD.title) THEN
          RETURN NULL;
        ELSE
          INSERT INTO fandom_versions (id, edited_at, edited_by, title,
                                       description, avatar)
          VALUES (OLD.id, now(), NEW.edited_by, NEW.title,
                  NEW.description, NEW.avatar);

          RETURN NEW;
        END IF;
      ELSIF TG_OP = 'DELETE' THEN
        RETURN NULL;
      END IF;
    END;
  $function$ LANGUAGE plpgsql;

CREATE TRIGGER fandom_trig
INSTEAD OF INSERT OR UPDATE OR DELETE
ON fandoms FOR EACH ROW
EXECUTE PROCEDURE fandoms_functions();


CREATE OR REPLACE FUNCTION fandoms_create(
  uid   BIGINT,
  u     CITEXT,
  titl  VARCHAR(120),
  descr TEXT,
  avatr VARCHAR(64)
) RETURNS BIGINT AS $function$
    BEGIN
      IF FALSE THEN  -- TODO: Сделать нормальную проверку
        RETURN FALSE;
      END IF;

      INSERT INTO fandoms (id, url, title, description, avatar)
      VALUES (nextval('fandom_statics_id_seq'), u, titl, descr, avatr);

      INSERT INTO relationships (user_id, target_id, target_type, role, set_by)
      VALUES (uid, currval('fandom_statics_id_seq'), 'fandom', 'owner', uid);

      RETURN currval('fandom_statics_id_seq');
    END;
  $function$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fandoms_update(
  tid   BIGINT,
  uid   BIGINT,
  titl  VARCHAR(120),
  descr TEXT,
  avatr VARCHAR(64)
) RETURNS BOOLEAN AS $function$
    BEGIN
      IF NOT EXISTS (SELECT 1 FROM relationships
                      WHERE target_type = 'fandom'
                        AND target_id = tid
                        AND user_id = uid) THEN  -- TODO: Сделать нормальную проверку
        RETURN FALSE;
      END IF;
      UPDATE fandoms SET
        edited_at = DEFAULT, edited_by = uid,
        description = COALESCE(descr, description),
        avatar = COALESCE(avatr, avatar),
        title = COALESCE(titl, title)
      WHERE id = tid;
      RETURN TRUE;
    END;
  $function$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fandoms_history(
  tid BIGINT,
  uid BIGINT
) RETURNS TABLE (id BIGINT, created_at TIMESTAMPTZ, edited_at TIMESTAMPTZ,
                 edited_by BIGINT, title VARCHAR, url CITEXT, description TEXT,
                 avatar VARCHAR(64), owner BIGINT) AS $function$
    BEGIN
      IF NOT EXISTS (SELECT 1 FROM relationships
                      WHERE target_type = 'fandom'
                        AND target_id = tid
                        AND user_id = uid) THEN  -- TODO: Сделать нормальную проверку
        RETURN;
      END IF;
      RETURN QUERY
      SELECT fs.id, fs.created_at, fv.edited_at, fv.edited_by,
             fv.title, fs.url, fv.description, fv.avatar, rl.user_id as owner
        FROM fandom_statics as fs
             INNER JOIN fandom_versions as fv
             ON fv.id = fs.id

             INNER JOIN relationships as rl
             ON rl.target_id = fs.id
                AND rl.target_type = 'fandom';
    END;
  $function$ LANGUAGE plpgsql;
