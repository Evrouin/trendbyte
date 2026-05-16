-- Store categories and keywords in database for dynamic management

CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS category_keywords (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    keyword VARCHAR(255) NOT NULL,
    added_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(category_id, keyword)
);

CREATE INDEX IF NOT EXISTS idx_category_keywords_keyword ON category_keywords(keyword);

-- Seed default categories
INSERT INTO categories (name) VALUES
    ('ai'), ('web'), ('devops'), ('languages'), ('databases'), ('security')
ON CONFLICT (name) DO NOTHING;
