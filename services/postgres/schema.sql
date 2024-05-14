CREATE EXTENSION postgis;

\set ON_ERROR_STOP on

BEGIN;

CREATE TABLE users (
	id_users BIGSERIAL PRIMARY KEY,
	username TEXT NOT NULL UNIQUE,
	password TEXT NOT NULL,
	bio TEXT
);

CREATE TABLE urls (
        id_urls BIGSERIAL PRIMARY KEY,
        -- id_tweets BIGINT UNIQUE REFERENCES tweets(id_tweets),
        url TEXT UNIQUE NOT NULL
);

CREATE TABLE tweets (
	id_tweets BIGSERIAL PRIMARY KEY,
	id_users BIGINT NOT NULL REFERENCES users(id_users),
	id_urls BIGINT NOT NULL UNIQUE REFERENCES urls(id_urls),
	text TEXT,
	time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMIT;
