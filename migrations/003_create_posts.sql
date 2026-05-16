-- Create posts table for tweet history and deduplication

CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    trend_name VARCHAR(255) NOT NULL,
    tweet_id VARCHAR(100) UNIQUE NOT NULL,
    tweet_text TEXT NOT NULL,
    image_path TEXT,
    posted_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_posts_trend_name ON posts(trend_name);
CREATE INDEX IF NOT EXISTS idx_posts_posted_at ON posts(posted_at);
