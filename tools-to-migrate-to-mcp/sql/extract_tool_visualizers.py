#!/usr/bin/env python3
"""
Extract tool visualizer configurations from SQL files and backup.

Reads:
1. g_tools from SQL insert files
2. t_tools from latest backup file
3. Extracts VISUALIZER environment variable values

Outputs CSV with: tool_id, tool_name, visualizer
"""

import re
import csv
import json
from pathlib import Path
from typing import Dict, Optional

# SQL files to parse for g_tools
SQL_FILES = [
    'insert_feeds_tools.sql',
    'insert_spiderfoot_adblock.sql',
    'insert_osint_tools_infra.sql',
    'insert_osint_tools.sql',
    'insert_abusech.sql',
    'insert_abstract_exif_phoneinfoga.sql',
    'insert_certgraph.sql',
    'insert_graphviz_mermaid.sql',
    'insert_webc_dnsdumpster.sql'
]

# Latest backup file
BACKUP_FILE = '../../../../db/schema/hd_data_Dec-14-19-23-PT-v7.4.2.sql'

# Output CSV file
OUTPUT_CSV = 'tool_visualizers.csv'


def extract_g_tools_from_sql(sql_file: Path) -> Dict[str, str]:
    """Extract tool_id and tool_name from g_tools INSERT statements."""
    tools = {}
    
    if not sql_file.exists():
        print(f"Warning: {sql_file} not found")
        return tools
    
    content = sql_file.read_text(encoding='utf-8')
    
    # Pattern to match: INSERT INTO hdtm.g_tools VALUES (
    #     'tool_id',  -- id
    #     ...
    #     'tool_name',  -- tool_name
    pattern = r"INSERT INTO hdtm\.g_tools VALUES\s*\(\s*'([^']+)',\s*-- id"
    
    # Find all INSERT statements
    insert_matches = list(re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE))
    
    for match in insert_matches:
        start_pos = match.start()
        # Find the tool_id (first quoted string after INSERT)
        tool_id_match = match.group(1)
        
        # Now find tool_name - it's typically the 4th field (after id, domain_id, pillar_id)
        # Look for pattern: 'tool_name', -- tool_name
        # Search from the match position forward
        remaining = content[start_pos:]
        
        # Try to find tool_name field - it's usually after 2-3 fields
        # Pattern: 'tool_name', -- tool_name
        tool_name_pattern = r"'([^']+)',\s*--\s*tool_name"
        tool_name_match = re.search(tool_name_pattern, remaining, re.IGNORECASE)
        
        if tool_name_match:
            tool_name = tool_name_match.group(1)
            tools[tool_id_match] = tool_name
        else:
            # Fallback: try to find it by position (4th quoted string)
            # Count quoted strings
            quoted_strings = re.findall(r"'([^']+)'", remaining[:2000])  # Look in first 2000 chars
            if len(quoted_strings) >= 4:
                # Usually tool_name is the 4th one (index 3)
                tools[tool_id_match] = quoted_strings[3]
    
    return tools


def extract_visualizer_from_env_vars(env_vars_str: str) -> Optional[str]:
    """Extract VISUALIZER value from environment_variables JSON string."""
    if not env_vars_str or env_vars_str.strip() in ['NULL', '{}', "''", '']:
        return None
    
    try:
        # Try to parse as JSON
        env_vars = json.loads(env_vars_str)
        if isinstance(env_vars, dict):
            visualizer = env_vars.get('VISUALIZER')
            if visualizer:
                # If it's a string, return it; if it's a dict, convert to string
                if isinstance(visualizer, str):
                    return visualizer
                elif isinstance(visualizer, dict):
                    return json.dumps(visualizer)
                else:
                    return str(visualizer)
    except (json.JSONDecodeError, TypeError):
        # Not valid JSON, might be encrypted or other format
        pass
    
    return None


def parse_sql_values(values_str: str) -> list:
    """Parse SQL VALUES string into list of fields, handling quotes and JSON."""
    fields = []
    current_field = ""
    in_quotes = False
    quote_char = None
    brace_depth = 0
    paren_depth = 0
    
    i = 0
    while i < len(values_str):
        char = values_str[i]
        
        # Handle escaped quotes
        if char == '\\' and i + 1 < len(values_str):
            current_field += char + values_str[i + 1]
            i += 2
            continue
        
        # Handle quote escaping in SQL (two single quotes)
        if char == "'" and i + 1 < len(values_str) and values_str[i + 1] == "'":
            current_field += "''"
            i += 2
            continue
        
        if char in ["'", '"']:
            if not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char:
                in_quotes = False
                quote_char = None
            current_field += char
        elif char == '{' and not in_quotes:
            brace_depth += 1
            current_field += char
        elif char == '}' and not in_quotes:
            brace_depth -= 1
            current_field += char
        elif char == '(' and not in_quotes:
            paren_depth += 1
            current_field += char
        elif char == ')' and not in_quotes:
            paren_depth -= 1
            current_field += char
        elif char == ',' and not in_quotes and brace_depth == 0 and paren_depth == 0:
            fields.append(current_field.strip())
            current_field = ""
        else:
            current_field += char
        
        i += 1
    
    if current_field.strip():
        fields.append(current_field.strip())
    
    return fields


def extract_t_tools_from_backup(backup_file: Path) -> Dict[str, Dict[str, str]]:
    """Extract t_tools data from backup file, mapping tool_id to visualizer."""
    t_tools_data = {}
    
    if not backup_file.exists():
        print(f"Warning: {backup_file} not found")
        return t_tools_data
    
    print(f"Reading backup file: {backup_file} (this may take a moment...)")
    content = backup_file.read_text(encoding='utf-8')
    
    # Pattern to match INSERT INTO hdtm.t_tools VALUES
    pattern = r"INSERT INTO hdtm\.t_tools VALUES\s*\("
    
    insert_matches = list(re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE))
    print(f"Found {len(insert_matches)} t_tools INSERT statements")
    
    for idx, match in enumerate(insert_matches):
        start_pos = match.end()
        # Find the end of this VALUES clause
        end_match = re.search(r'\);', content[start_pos:start_pos+10000])
        if not end_match:
            continue
        
        values_str = content[start_pos:start_pos+end_match.start()]
        
        # Parse fields
        fields = parse_sql_values(values_str)
        
        # Based on t_tools schema:
        # Fields: tool_instance_id, tenant_id, tool_id, instance_name, installation_status, 
        # installation_date, last_used, usage_count, user_config, credentials, access_keys,
        # environment_variables (index 11), ...
        if len(fields) >= 12:
            tool_id = fields[2].strip("'\"")  # 3rd field (index 2)
            instance_name = fields[3].strip("'\"")  # 4th field (index 3)
            
            # environment_variables is at index 11 (12th field)
            env_vars_str = fields[11].strip()
            
            # Remove outer quotes if present
            if env_vars_str.startswith("'") and env_vars_str.endswith("'"):
                env_vars_str = env_vars_str[1:-1]
                # Unescape SQL quotes
                env_vars_str = env_vars_str.replace("''", "'")
            elif env_vars_str.startswith('"') and env_vars_str.endswith('"'):
                env_vars_str = env_vars_str[1:-1]
            
            # Skip if NULL or empty
            if env_vars_str.upper() in ['NULL', '{}', '']:
                continue
            
            visualizer = extract_visualizer_from_env_vars(env_vars_str)
            if visualizer:
                t_tools_data[tool_id] = {
                    'instance_name': instance_name,
                    'visualizer': visualizer
                }
                print(f"  Found VISUALIZER for {tool_id}: {visualizer}")
    
    return t_tools_data


def main():
    """Main function to extract and combine tool data."""
    script_dir = Path(__file__).parent
    output_file = script_dir / OUTPUT_CSV
    
    # Step 1: Extract g_tools from SQL files
    all_g_tools = {}
    for sql_file_name in SQL_FILES:
        sql_file = script_dir / sql_file_name
        tools = extract_g_tools_from_sql(sql_file)
        all_g_tools.update(tools)
        print(f"Extracted {len(tools)} tools from {sql_file_name}")
    
    print(f"\nTotal g_tools extracted: {len(all_g_tools)}")
    
    # Step 2: Extract t_tools from backup
    backup_file = script_dir / BACKUP_FILE
    t_tools_data = extract_t_tools_from_backup(backup_file)
    print(f"\nTotal t_tools with VISUALIZER found: {len(t_tools_data)}")
    
    # Step 3: Combine data and write CSV
    rows = []
    
    # Add g_tools entries (with NULL visualizer if not in t_tools)
    for tool_id, tool_name in all_g_tools.items():
        visualizer = None
        if tool_id in t_tools_data:
            visualizer = t_tools_data[tool_id]['visualizer']
        rows.append({
            'tool_id': tool_id,
            'tool_name': tool_name,
            'visualizer': visualizer or ''
        })
    
    # Add t_tools entries that aren't in g_tools (in case of mismatches)
    for tool_id, data in t_tools_data.items():
        if tool_id not in all_g_tools:
            rows.append({
                'tool_id': tool_id,
                'tool_name': data['instance_name'],
                'visualizer': data['visualizer'] or ''
            })
    
    # Write CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['tool_id', 'tool_name', 'visualizer'])
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\n✅ Created CSV file: {output_file}")
    print(f"   Total rows: {len(rows)}")
    print(f"   Tools with visualizer: {sum(1 for r in rows if r['visualizer'])}")


if __name__ == '__main__':
    main()

