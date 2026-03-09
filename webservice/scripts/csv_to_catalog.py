#!/usr/bin/env python3
"""
Convert the tools export CSV to the catalog JSON format expected by the webservice.
Usage: python scripts/csv_to_catalog.py [input.csv] [output.json]
Defaults: 2026-03-07T20-14_export.csv -> catalog.json
"""
import csv
import json
import sys
from pathlib import Path

def parse_search_terms(s: str):
    if not s or not s.strip():
        return []
    s = s.strip()
    if s.startswith("["):
        try:
            return json.loads(s.replace('""', '"'))
        except json.JSONDecodeError:
            pass
    return [t.strip() for t in s.split(",") if t.strip()]

def main():
    base = Path(__file__).resolve().parent.parent
    input_csv = base / "2026-03-07T20-14_export.csv"
    output_json = base / "catalog.json"
    if len(sys.argv) >= 2:
        input_csv = Path(sys.argv[1])
    if len(sys.argv) >= 3:
        output_json = Path(sys.argv[2])

    if not input_csv.exists():
        print(f"Error: input file not found: {input_csv}", file=sys.stderr)
        sys.exit(1)

    tools = []
    with open(input_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tool_id = (row.get("ID") or "").strip()
            if not tool_id:
                continue
            config_str = (row.get("Configuration") or "").strip()
            configuration = None
            if config_str:
                try:
                    configuration = json.loads(config_str)
                except json.JSONDecodeError:
                    continue
            if not configuration or "mcpServers" not in configuration:
                continue
            name = (row.get("Tool Name") or "").strip()
            description = (row.get("Description") or "").strip()
            category = (row.get("Category") or "").strip()
            vendor = (row.get("Vendor") or "").strip()
            tool_type = (row.get("Tool Type") or "mcp_server").strip()
            is_active = (row.get("Is Active") or "true").strip().lower() == "true"
            is_featured = (row.get("Is Featured") or "false").strip().lower() == "true"
            search_terms = parse_search_terms(row.get("Search Terms") or "")
            tools.append({
                "id": tool_id,
                "name": name,
                "description": description,
                "category": category,
                "vendor": vendor,
                "tool_type": tool_type,
                "is_active": is_active,
                "is_featured": is_featured,
                "search_terms": search_terms,
                "configuration": configuration,
                "metadata": {
                    "source_code_link": (row.get("Source Code Link") or "").strip(),
                    "documentation_url": (row.get("Documentation URL") or "").strip(),
                    "deployment_model": (row.get("Deployment Model") or "").strip(),
                    "pricing_model": (row.get("Pricing Model") or "").strip(),
                },
            })

    catalog = {
        "version": "1.0",
        "updated_at": "",
        "tools": tools,
    }
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(tools)} tools to {output_json}")

if __name__ == "__main__":
    main()
