#!/usr/bin/env python3
"""Block destructive Claude Code Bash commands."""
import datetime, json, os, re, shlex, sys
from pathlib import Path

def sql_code(text):
    out = []
    i = 0
    while i < len(text):
        if text.startswith('--', i):
            end = text.find('\n', i)
            if end < 0:
                break
            out.append('\n')
            i = end + 1
        elif text.startswith('/*', i):
            end = text.find('*/', i + 2)
            if end < 0:
                break
            out.append(' ' * (end + 2 - i))
            i = end + 2
        elif text[i] in ("'", '"'):
            quote = text[i]
            out.append(' ')
            i += 1
            while i < len(text):
                if text[i] == quote:
                    if i + 1 < len(text) and text[i + 1] == quote:
                        i += 2
                        continue
                    i += 1
                    break
                if text[i] == '\\':
                    i += 2
                else:
                    i += 1
            out.append(' ')
        else:
            out.append(text[i])
            i += 1
    return ''.join(out)

def reason(command, depth=0):
    # A shell -c argument is itself a command; inspect it before the outer line.
    if depth < 4:
        try:
            words = shlex.split(command)
        except ValueError:
            words = []
        for i, word in enumerate(words):
            if word.rsplit('/', 1)[-1] not in ('bash', 'sh'):
                continue
            j = i + 1
            while j < len(words):
                option = words[j]
                if option == '--':
                    break
                if option in ('-o', '-O', '--rcfile', '--init-file'):
                    j += 2
                    continue
                if option == '-c' or (option.startswith('-') and not option.startswith('--') and 'c' in option[1:]):
                    if j + 1 < len(words):
                        nested = reason(words[j + 1], depth + 1)
                        if nested is not None:
                            return nested
                    break
                if option.startswith('-'):
                    j += 1
                    continue
                break
    for match in re.finditer(r'\brm\s+((?:(?:--[a-z-]+|-[a-z]+)\s+)+)', command, re.I):
        options = match.group(1).lower().split()
        recursive = any(x == '--recursive' or (x.startswith('-') and not x.startswith('--') and 'r' in x[1:]) for x in options)
        force = any(x == '--force' or (x.startswith('-') and not x.startswith('--') and 'f' in x[1:]) for x in options)
        if recursive and force:
            return 'recursive forced removal'
    for pattern, label in ((r'\bDROP\s+TABLE\b', 'DROP TABLE'), (r'\bgit\s+push\b[^;\n]*?(?:--force\b|-f\b)', 'forced git push'), (r'\bTRUNCATE\b', 'TRUNCATE')):
        if re.search(pattern, command, re.I):
            return label
    sql_inputs = [command]
    try:
        sql_inputs.extend(shlex.split(command))
    except ValueError:
        pass
    for sql_input in sql_inputs:
        for statement in sql_code(sql_input).split(';'):
            if re.search(r'\bDELETE\s+FROM\b', statement, re.I) and not re.search(r'\bWHERE\b', statement, re.I):
                return 'DELETE FROM without WHERE'
    return None

def main():
    try:
        event = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    if event.get('tool_name') != 'Bash':
        return 0
    command = event.get('tool_input', {}).get('command', '')
    if not isinstance(command, str):
        return 0
    why = reason(command)
    if why is None:
        return 0
    log = Path.home() / '.claude' / 'hooks' / 'blocked.log'
    try:
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'command': command, 'project_path': event.get('cwd') or os.getcwd()}, ensure_ascii=False) + '\n')
    except OSError:
        pass
    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'deny', 'permissionDecisionReason': 'Blocked destructive Bash command: ' + why}}))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
