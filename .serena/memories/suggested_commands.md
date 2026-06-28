# Suggested Commands

- Current repo is planning/docs only; scaffold commands are not yet available.
- Git status: `git status --short --branch`.
- Markdown/search checks: `rg -n "PATTERN" .serena/newproj/nornikel-kg-search README.md`.
- Whitespace check before commit: `git diff --check`.
- Basic secret-pattern scan before commit: use a targeted `rg` scan for secret labels, private-key markers, API-key labels, and long `sk-...` tokens over touched docs.
- After scaffold approval, expected targets to add: `make install`, `make test`, `make ingest-fixtures`, `make eval`, `make demo`.
