#!/usr/bin/env python3
"""
Analyze each tool's output format and assign appropriate visualizations.

This script reviews the actual output structure of each tool and suggests
the most appropriate visualization type based on the data structure.
"""

import csv
from pathlib import Path

# Tool-specific visualizer mappings based on ACTUAL output analysis
VISUALIZER_MAPPINGS = {
    # Amass tools
    'amass_intel_osint_001': 'plotly.bar',  # Domain/IP counts
    'amass_enum_osint_001': 'plotly.bar',  # Subdomain enumeration results
    'amass_viz_osint_001': 'graphviz.digraph',  # Network graph visualization
    'amass_track_osint_001': 'plotly.line',  # Track changes over time
    
    # Scanning tools
    'nuclei_scan_osint_001': 'plotly.bar',  # Vulnerabilities by severity/category
    'subfinder_enum_osint_001': 'plotly.bar',  # Subdomain counts
    'masscan_scan_osint_001': 'plotly.heatmap',  # Port scan results (IP x Port)
    'zmap_scan_osint_001': 'plotly.heatmap',  # Port scan results (IP x Port)
    
    # DNS and domain tools
    'dnsdumpster_search_osint_001': 'plotly.treemap',  # DNS hierarchy (domain -> type -> record)
    'waybackurls_osint_001': 'plotly.line',  # Historical URLs timeline
    
    # Social/username tools
    'holehe_osint_001': 'graphviz.digraph',  # Email -> Sites network
    'maigret_osint_001': 'graphviz.digraph',  # Username -> Platforms network
    'sherlock_osint_001': 'graphviz.digraph',  # Username -> Platforms network
    
    # Dark web
    'onionsearch_osint_001': 'plotly.bar',  # Search results count
    
    # Browserless tools
    'browserless_content_osint_001': None,  # Text content, no visualization
    'browserless_scrape_osint_001': 'plotly.bar',  # Scraped data counts by type
    'browserless_screenshot_osint_001': None,  # Screenshot image, no chart
    'browserless_pdf_osint_001': None,  # PDF content, no chart
    'browserless_function_osint_001': 'plotly.bar',  # Function results
    'browserless_unblock_osint_001': None,  # Status response, no chart
    
    # WebC Analysis tools - Based on ACTUAL output structure
    'webc_analyze_webpage_osint_001': 'map',  # Has ip_locations with lat/long - MAP!
    'webc_extract_text_osint_001': None,  # Plain text extraction, no chart
    'webc_get_webpage_response_osint_001': 'plotly.bar',  # HTTP response metrics (status codes, headers)
    'webc_detect_language_osint_001': 'plotly.pie',  # Single language - pie chart
    'webc_detect_multiple_languages_osint_001': 'plotly.bar',  # Multiple languages with confidence - bar chart
    'webc_translate_text_osint_001': None,  # Translated text, no chart
    'webc_translate_webpage_osint_001': None,  # Translated webpage, no chart
    'webc_analyze_text_osint_001': 'plotly.bar',  # Text statistics (word count, sentences, etc.)
    'webc_extract_entities_osint_001': 'plotly.bar',  # Entity types distribution (PERSON, ORG, GPE, etc.)
    'webc_extract_emails_osint_001': 'plotly.bar',  # Email domain distribution
    'webc_find_sensitive_data_osint_001': 'plotly.bar',  # Sensitive data types (phones, emails, IPs, credit cards, etc.)
    'webc_analyze_domain_osint_001': 'map',  # Has ip_locations with lat/long - MAP!
    'webc_resolve_domain_ips_osint_001': 'plotly.bar',  # List of IPs - count/bar chart
    'webc_get_domain_whois_osint_001': None,  # WHOIS text data, structured but not chartable
    'webc_get_ip_location_osint_001': 'map',  # Single IP location - map (already correct)
    'webc_get_ip_whois_osint_001': None,  # IP WHOIS text data, not chartable
    'webc_get_certificate_info_osint_001': 'plotly.bar',  # Certificate fields (issuer, validity, etc.)
    'webc_get_domain_tld_info_osint_001': 'plotly.pie',  # TLD distribution - pie chart (already correct)
    'webc_calculate_text_similarity_osint_001': 'plotly.bar',  # Similarity scores - bar chart
    'webc_calculate_similarity_spacy_osint_001': 'plotly.bar',  # Similarity scores - bar chart
    'webc_extract_keyterms_osint_001': 'plotly.bar',  # Key terms with scores - bar chart (top terms)
    'webc_extract_keyterms_textrank_osint_001': 'plotly.bar',  # Key terms with scores - bar chart (top terms)
    'webc_get_readability_stats_osint_001': 'plotly.bar',  # Readability metrics (Flesch, etc.) - bar chart
    'webc_scan_service_osint_001': 'plotly.bar',  # Port/service status - bar chart
    'webc_ping_service_osint_001': 'plotly.line',  # Ping response times over time - line chart (already correct)
    'webc_calculate_geo_distance_osint_001': 'plotly.bar',  # Distance metrics - bar chart
    'webc_calculate_geoip_distance_osint_001': 'map',  # IP distance map (already correct)
    'webc_calculate_geodomain_distance_osint_001': 'map',  # Domain distance map (already correct)
    'webc_remove_stopwords_osint_001': None,  # Text processing, no chart
    'webc_validate_credit_card_osint_001': 'plotly.bar',  # Validation results by card type
}


def analyze_tool_output(tool_id: str, tool_name: str) -> str:
    """
    Analyze tool output and suggest appropriate visualization.
    
    Returns:
        Visualizer string (e.g., "plotly.bar") or empty string if no visualization needed
    """
    # Check explicit mapping first
    if tool_id in VISUALIZER_MAPPINGS:
        visualizer = VISUALIZER_MAPPINGS[tool_id]
        return visualizer if visualizer else ''
    
    # Fallback: analyze tool name patterns
    tool_name_lower = tool_name.lower()
    
    # Geographic data -> map
    if any(keyword in tool_name_lower for keyword in ['location', 'geo', 'ip location', 'distance', 'geolocation']):
        return 'map'
    
    # Time-based data -> line chart
    if any(keyword in tool_name_lower for keyword in ['track', 'timeline', 'history', 'time', 'ping']):
        return 'plotly.line'
    
    # Distribution data -> pie chart
    if any(keyword in tool_name_lower for keyword in ['language', 'tld', 'distribution']):
        return 'plotly.pie'
    
    # Network/graph data -> graphviz
    if any(keyword in tool_name_lower for keyword in ['viz', 'visualization', 'graph', 'network']):
        return 'graphviz.digraph'
    
    # Hierarchical data -> treemap
    if any(keyword in tool_name_lower for keyword in ['dns', 'hierarchy', 'tree']):
        return 'plotly.treemap'
    
    # Count/statistics -> bar chart
    if any(keyword in tool_name_lower for keyword in ['extract', 'find', 'analyze', 'count', 'stats', 'similarity', 'keyterms']):
        return 'plotly.bar'
    
    # Default: no visualization
    return ''


def main():
    """Update CSV with properly analyzed visualizer configurations."""
    script_dir = Path(__file__).parent
    csv_file = script_dir / 'tool_visualizers.csv'
    
    # Read existing CSV
    rows = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tool_id = row['tool_id']
            tool_name = row['tool_name']
            
            # Analyze and update visualizer
            visualizer = analyze_tool_output(tool_id, tool_name)
            old_visualizer = row.get('visualizer', '').strip()
            
            if visualizer != old_visualizer:
                print(f"Updating {tool_id} ({tool_name}):")
                print(f"  Old: {old_visualizer or '(empty)'}")
                print(f"  New: {visualizer or '(no visualization)'}")
                row['visualizer'] = visualizer
            else:
                print(f"Keeping {tool_id}: {visualizer or '(no visualization)'}")
            
            rows.append(row)
    
    # Write updated CSV
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['tool_id', 'tool_name', 'visualizer'])
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\n✅ Updated CSV file: {csv_file}")
    print(f"   Total tools: {len(rows)}")
    print(f"   Tools with visualizer: {sum(1 for r in rows if r['visualizer'])}")
    print(f"   Tools without visualizer: {sum(1 for r in rows if not r['visualizer'])}")


if __name__ == '__main__':
    main()

