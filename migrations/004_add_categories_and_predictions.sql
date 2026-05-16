-- Add category column to mentions and predictions table

ALTER TABLE mentions ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT 'other';

CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    confidence FLOAT NOT NULL,
    signals TEXT[] DEFAULT '{}',
    url TEXT DEFAULT '',
    outcome VARCHAR(20) DEFAULT 'pending',
    predicted_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_predictions_name ON predictions(name);
CREATE INDEX IF NOT EXISTS idx_mentions_category ON mentions(category);
