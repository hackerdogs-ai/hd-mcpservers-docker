#!/usr/bin/env python3
import sys
import os

# Patch source version at /opt/theharvester
os.chdir('/opt/theharvester')
fname = 'theHarvester/lib/stash.py'

if not os.path.exists(fname):
    print(f'ERROR: {fname} not found')
    sys.exit(1)

print(f'Patching {fname}...')
with open(fname, 'r') as f:
    lines = f.readlines()

# Find import aiosqli (not aiosqlite)
new_lines = []
replaced = False
for i, line in enumerate(lines):
    # Look for 'import aiosqli' but exclude 'aiosqlite'
    if 'import aiosqli' in line and 'aiosqlite' not in line and not replaced:
        print(f'Found import aiosqli at line {i+1}: {repr(line)}')
        indent = len(line) - len(line.lstrip())
        indent_str = ' ' * indent
        new_lines.append(f'{indent_str}try:\n')
        new_lines.append(f'{indent_str}    import aiosqli\n')
        new_lines.append(f'{indent_str}except ImportError:\n')
        new_lines.append(f'{indent_str}    aiosqli = None\n')
        replaced = True
    else:
        new_lines.append(line)

if replaced:
    with open(fname, 'w') as f:
        f.writelines(new_lines)
    print('SUCCESS: Patched stash.py')
else:
    # Also check pip version if importable
    try:
        import theharvester
        pip_stash = os.path.join(os.path.dirname(theharvester.__file__), 'lib', 'stash.py')
        if os.path.exists(pip_stash):
            print(f'Also checking pip version: {pip_stash}')
            with open(pip_stash, 'r') as f:
                pip_lines = f.readlines()
            for line in pip_lines:
                if 'import aiosqli' in line and 'aiosqlite' not in line:
                    print('Found aiosqli in pip version too - would need patching')
                    break
    except:
        pass
    
    print('WARNING: import aiosqli not found - may already be patched or not present')

# Also make screenshot import optional in __main__.py
main_file = '/opt/theharvester/theHarvester/__main__.py'
if os.path.exists(main_file):
    with open(main_file, 'r') as f:
        main_lines = f.readlines()
    
    new_main_lines = []
    for line in main_lines:
        if 'from theHarvester.screenshot.screenshot import ScreenShotter' in line:
            indent = len(line) - len(line.lstrip())
            indent_str = ' ' * indent
            new_main_lines.append(f'{indent_str}try:\n')
            new_main_lines.append(f'{indent_str}    from theHarvester.screenshot.screenshot import ScreenShotter\n')
            new_main_lines.append(f'{indent_str}except ImportError:\n')
            new_main_lines.append(f'{indent_str}    ScreenShotter = None\n')
        else:
            new_main_lines.append(line)
    
    with open(main_file, 'w') as f:
        f.writelines(new_main_lines)
    print('SUCCESS: Made screenshot import optional')

sys.exit(0)
