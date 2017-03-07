CREATE EXTENSION IF NOT EXISTS citext;

CREATE TABLE "auth" (
    PRIMARY KEY (id),

    id            BIGINT       NOT NULL,
    password_hash VARCHAR(130) NOT NULL
);

CREATE TABLE "user_statics" (
    PRIMARY KEY (id),
    UNIQUE (username),

    id         BIGSERIAL                 NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    username   CITEXT                    NOT NULL
);

CREATE TABLE "user_versions" (
    PRIMARY KEY (id, edited_at),

    id            BIGINT                    NOT NULL,
    edited_at     TIMESTAMPTZ DEFAULT now() NOT NULL,
    edited_by     BIGINT                    NOT NULL,
    description   TEXT DEFAULT ''           NOT NULL
);

CREATE VIEW "users" AS (
    SELECT us.id, us.created_at, uv.edited_at, uv.edited_by,
           us.username, uv.description
      FROM "user_statics" as us
           INNER JOIN "user_versions" as uv
           ON uv.id = us.id
              AND uv.edited_at =
                  (SELECT max(uv2.edited_at)
                     FROM "user_versions" AS uv2
                    WHERE uv2.id = us.id)
);

CREATE OR REPLACE FUNCTION users_functions() RETURNS TRIGGER AS $function$
    BEGIN
      IF TG_OP = 'INSERT' THEN
        INSERT INTO "user_statics" (id, created_at, username)
        VALUES (NEW.id, now(), NEW.username);

        INSERT INTO "user_versions" (id, edited_at, edited_by)
        VALUES (NEW.id, now(), NEW.id);

        RETURN NEW;
      ELSIF TG_OP = 'UPDATE' THEN
        IF (NEW.description) = (OLD.description) THEN
          RETURN NULL;
        ELSE
          INSERT INTO "user_versions" (id, edited_at, edited_by, description)
          VALUES (OLD.id, now(), NEW.edited_by, NEW.description);

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
      INSERT INTO "users" (id, username)
      VALUES (nextval('user_statics_id_seq'), usern);

      INSERT INTO "auth" (id, password_hash)
      VALUES (currval('user_statics_id_seq'), passh);

      RETURN currval('user_statics_id_seq');
    END;
  $function$ LANGUAGE plpgsql;

