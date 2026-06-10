ALTER TABLE tech_names ADD COLUMN IF NOT EXISTS ambiguous BOOLEAN DEFAULT NULL;

UPDATE tech_names SET ambiguous = TRUE
WHERE ambiguous IS NULL
AND LENGTH(canonical_name) <= 8
AND canonical_name ~ '^[A-Z][a-z]+$';
