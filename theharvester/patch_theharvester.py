#!/usr/bin/env python3
"""Patch theHarvester to make aiosqli optional."""
import sys
import os

# Patch stash.py
stash_file = 'theHarvester/lib/stash.py'
if os.path.exists(stash_file):
    try:
        with open(stash_file, 'r') as f:
            lines = f.readlines()
        
        # Find and replace the import line
        new_lines = []
        replaced = False
        for line in lines:
            stripped = line.rstrip()
            if stripped == 'import aiosqli' and not replaced:
                # Get indentation
                indent = len(line) - len(line.lstrip())
                indent_str = ' ' * indent
                # Replace with try/except
                new_lines.append(f"{indent_str}try:\n")
                new_lines.append(f"{indent_str}    import aiosqli\n")
                new_lines.append(f"{indent_str}except ImportError:\n")
                new_lines.append(f"{indent_str}    aiosqli = None\n")
                replaced = True
            else:
                new_lines.append(line)
        
        if replaced:
            with open(stash_file, 'w') as f:
                f.writelines(new_lines)
            print('Patched stash.py successfully')
            sys.exit(0)
        else:
            print('aiosqli import not found or already patched')
            sys.exit(0)
    except Exception as e:
        print(f'Patch stash.py failed: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
else:
    print(f'stash.py not found at {stash_file}')
    sys.exit(1)
