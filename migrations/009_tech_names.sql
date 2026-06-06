CREATE TABLE IF NOT EXISTS tech_names (
    id SERIAL PRIMARY KEY,
    canonical_name VARCHAR(200) NOT NULL UNIQUE,
    category_id INTEGER REFERENCES categories(id),
    icon_slug VARCHAR(200),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tech_aliases (
    id SERIAL PRIMARY KEY,
    tech_id INTEGER NOT NULL REFERENCES tech_names(id) ON DELETE CASCADE,
    alias VARCHAR(200) NOT NULL,
    source VARCHAR(50) DEFAULT 'manual',
    UNIQUE(alias)
);

CREATE INDEX IF NOT EXISTS idx_tech_aliases_alias ON tech_aliases(alias);
