# Destructive Bash command hook

Install from the repository root with `python3 hooks/install.py`. This adds a Bash PreToolUse command hook. It blocks recursive forced removal, DROP TABLE, forced Git push, TRUNCATE, and DELETE FROM without an active WHERE clause; SQL comments and string literals do not count as WHERE clauses; shell-quoted SQL is checked. Blocked commands are logged in `~/.claude/hooks/blocked.log` with UTC time, command and project path.
