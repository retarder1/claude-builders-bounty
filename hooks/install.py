#!/usr/bin/env python3
"""Install the Claude Code PreToolUse hook."""
import json, os, shlex, shutil, subprocess, sys
from pathlib import Path
source = Path(__file__).with_name('block_destructive.py')
target = Path.home() / '.claude' / 'hooks' / source.name
target.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(source, target)
settings_path = Path.home() / '.claude' / 'settings.json'
settings = json.loads(settings_path.read_text(encoding='utf-8')) if settings_path.exists() else {}
hooks = settings.setdefault('hooks', {}).setdefault('PreToolUse', [])
command = subprocess.list2cmdline([sys.executable, str(target)]) if os.name == 'nt' else shlex.join([sys.executable, str(target)])
entry = {'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': command}]}
if entry not in hooks:
    hooks.append(entry)
settings_path.write_text(json.dumps(settings, indent=2) + '\n', encoding='utf-8')
print('Installed', target)
