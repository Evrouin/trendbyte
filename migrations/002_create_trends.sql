-- Create trends table for scored/aggregated data

CREATE TABLE IF NOT EXISTS trends (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    mentions INTEGER DEFAULT 0,
    growth_pct FLOAT DEFAULT 0.0,
    score FLOAT DEFAULT 0.0,
    sources TEXT[] DEFAULT '{}',
    top_url TEXT DEFAULT '',
    calculated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trends_calculated_at ON trends(calculated_at);
