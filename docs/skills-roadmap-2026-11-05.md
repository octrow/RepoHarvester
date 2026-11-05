# Навыки с рынка: что добавить (2026-11-05)

Источник: `~/dev/jobs/data/corpus_roadmap.md` (11.5k вакансий, 2026-11-05) против [system-design](system-design.md) и [logic-map](logic-map.md). Берём только то, что нужно самому проекту; чего проект не требует — в «Отвергнуто». Сводка по всем репо: `~/dev/docs/skills-roadmap-report-2026-11-05.md`.

## Предложения

- [ ] **[mcp, agentic]** Тонкий MCP-сервер `harvest_repo(url|path, groups, max_size)` поверх чистой `harvest_text()` (system-design §3): продукт и есть «репо → контекст для LLM». Усилие S/M.

## Порядок

Только после #1 (`.env` с секретами попадает в вывод), #8, #9 и таймаутов `git ls-files`/`--max-total-mb` — иначе MCP отдаст агенту секреты и повиснет.

## Отвергнуто

- Docker: локальный CLI, зависимость — только `git`.
- Потоковая запись: только при >500 MB RSS (в «Идеях»). tiktoken вместо `len/4`: LOW.
