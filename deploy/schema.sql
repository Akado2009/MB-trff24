
-- create user
\c mb-trff24-db;

CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS parsing_task(
    id SERIAL,
    username VARCHAR(30),
    platform VARCHAR(30),
    -- error_codes and descriptions
    status TEXT,
    error_message TEXT,
    is_reviewed BOOLEAN,
    is_id BOOLEAN,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY(username, platform)
);

CREATE TRIGGER set_timestamp
BEFORE UPDATE ON parsing_task
FOR EACH ROW
EXECUTE PROCEDURE trigger_set_timestamp();

CREATE TABLE IF NOT EXISTS llm_task(
    id SERIAL,
    username VARCHAR(30),
    platform VARCHAR(30),

    status TEXT,
    error_message TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY(username, platform)
);

CREATE TRIGGER set_timestamp
BEFORE UPDATE ON llm_task
FOR EACH ROW
EXECUTE PROCEDURE trigger_set_timestamp();

CREATE TABLE IF NOT EXISTS social_post(
    id SERIAL,
    platform VARCHAR(30),
    username VARCHAR(30),
    picture_path TEXT,
    picture_local_path TEXT,
    caption TEXT,
    hashtags TEXT[],
    picture_url_hash TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (platform, username, picture_url_hash, caption)
);

CREATE TRIGGER set_timestamp
BEFORE UPDATE ON social_post
FOR EACH ROW
EXECUTE PROCEDURE trigger_set_timestamp();

CREATE TABLE IF NOT EXISTS instagram_followee(
    id SERIAL,
    username VARCHAR(30) UNIQUE,
    description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (username)
);

CREATE TRIGGER set_timestamp
BEFORE UPDATE ON instagram_followee
FOR EACH ROW
EXECUTE PROCEDURE trigger_set_timestamp();

CREATE TABLE IF NOT EXISTS instagram_profile(
    id SERIAL,
    username VARCHAR(30) UNIQUE,
    full_name VARCHAR(60),
    bio TEXT,
    location TEXT,
    followers_count INTEGER,
    following_count INTEGER,
    followees INTEGER[],

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (username)
);

CREATE TRIGGER set_timestamp
BEFORE UPDATE ON instagram_profile
FOR EACH ROW
EXECUTE PROCEDURE trigger_set_timestamp();

CREATE TABLE IF NOT EXISTS facebook_profile(
    id SERIAL,
    username VARCHAR(30) UNIQUE,
    first_name VARCHAR(30),
    last_name VARCHAR(30),
    location TEXT,
    location_from TEXT,
    age TEXT,
    gender VARCHAR(20),
    civil_status VARCHAR(25),
    category VARCHAR(30),
    education TEXT[],
    workplaces TEXT[],
    interests TEXT[],
    friends_count VARCHAR(30),
    events TEXT[],
    contact_information TEXT,
    groups TEXT[],

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (username)
);

CREATE TRIGGER set_timestamp
BEFORE UPDATE ON facebook_profile
FOR EACH ROW
EXECUTE PROCEDURE trigger_set_timestamp();

CREATE TABLE IF NOT EXISTS llm_review(
    id SERIAL,
    platform VARCHAR(30),
    username VARCHAR(30),
    profile_section TEXT,
    market_section TEXT,
    psycho_section TEXT,
    socio_section TEXT,
    client_section TEXT,
    tags_section TEXT,


    -- market_score_section TEXT,
    -- psycho_score_section TEXT,
    -- socio_score_section TEXT,
    -- client_score_section TEXT,
    final_review_section TEXT,

    status_code INTEGER,
    error TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY(username, platform)
);

CREATE TRIGGER set_timestamp
BEFORE UPDATE ON llm_review
FOR EACH ROW
EXECUTE PROCEDURE trigger_set_timestamp();


GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public to mb-trff24-user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO mb-trff24-user;
