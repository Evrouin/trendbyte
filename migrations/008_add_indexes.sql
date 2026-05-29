CREATE INDEX IF NOT EXISTS idx_trends_name_lower ON trends (LOWER(name));
CREATE INDEX IF NOT EXISTS idx_trends_calculated_at ON trends (calculated_at DESC);
CREATE INDEX IF NOT EXISTS idx_mentions_name_lower ON mentions (LOWER(name));
CREATE INDEX IF NOT EXISTS idx_mentions_source ON mentions (source);
CREATE INDEX IF NOT EXISTS idx_mentions_collected_at ON mentions (collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_name ON predictions (name);
CREATE INDEX IF NOT EXISTS idx_predictions_predicted_at ON predictions (predicted_at DESC);
