-- Analytics table for tracking tweet engagement

CREATE TABLE IF NOT EXISTS analytics (
    id SERIAL PRIMARY KEY,
    tweet_id VARCHAR(100) NOT NULL REFERENCES posts(tweet_id),
    impressions INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    retweets INTEGER DEFAULT 0,
    replies INTEGER DEFAULT 0,
    followers_gained INTEGER DEFAULT 0,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_analytics_tweet_id ON analytics(tweet_id);
CREATE INDEX IF NOT EXISTS idx_analytics_recorded_at ON analytics(recorded_at);
