-- Expand category keywords to reduce 'Others' categorization

-- DevOps
INSERT INTO category_keywords (category_id, keyword)
SELECT c.id, kw FROM categories c,
UNNEST(ARRAY['docker','kubernetes','terraform','ansible','jenkins','github-actions','vercel','netlify','render','fly.io','railway','caddy','nginx']) AS kw
WHERE c.name = 'devops'
ON CONFLICT DO NOTHING;

-- AI
INSERT INTO category_keywords (category_id, keyword)
SELECT c.id, kw FROM categories c,
UNNEST(ARRAY['chatgpt','gpt','claude','gemini','copilot','deepseek','llama','anthropic','openai','hugging-face','groq','cursor']) AS kw
WHERE c.name = 'ai'
ON CONFLICT DO NOTHING;

-- Web
INSERT INTO category_keywords (category_id, keyword)
SELECT c.id, kw FROM categories c,
UNNEST(ARRAY['react','vue','angular','svelte','next.js','nuxt','tailwind','htmx','express','django','flask','fastapi','deno','bun','npm']) AS kw
WHERE c.name = 'web'
ON CONFLICT DO NOTHING;

-- Databases
INSERT INTO category_keywords (category_id, keyword)
SELECT c.id, kw FROM categories c,
UNNEST(ARRAY['duckdb','clickhouse','turso','dynamodb','cassandra','mariadb','elasticsearch','kafka']) AS kw
WHERE c.name = 'databases'
ON CONFLICT DO NOTHING;

-- Security
INSERT INTO category_keywords (category_id, keyword)
SELECT c.id, kw FROM categories c,
UNNEST(ARRAY['tailscale','wireguard','vault','snyk','bitwarden','keycloak','1password','crowdstrike']) AS kw
WHERE c.name = 'security'
ON CONFLICT DO NOTHING;

-- Languages
INSERT INTO category_keywords (category_id, keyword)
SELECT c.id, kw FROM categories c,
UNNEST(ARRAY['python','javascript','typescript','rust','go','java','c++','c#','swift','kotlin','elixir','zig','ruby','php']) AS kw
WHERE c.name = 'languages'
ON CONFLICT DO NOTHING;
