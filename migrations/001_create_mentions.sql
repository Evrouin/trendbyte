-- Create mentions table for raw data from collectors

CREATE TABLE IF NOT EXISTS mentions (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    description TEXT DEFAULT '',
    stars INTEGER,
    forks INTEGER,
    score FLOAT DEFAULT 0.0,
    collected_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mentions_name ON mentions(name);
CREATE INDEX IF NOT EXISTS idx_mentions_collected_at ON mentions(collected_at);
