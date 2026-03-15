#!/usr/bin/env python3
"""
Populate visualizer configurations for tools based on their functionality.

Analyzes each tool and suggests appropriate visualizers.
"""

import csv
from pathlib import Path
from typing import Dict

# Tool-specific visualizer mappings based on functionality
VISUALIZER_MAPPINGS = {
    # Amass tools
    'amass_intel_osint_001': 'plotly.bar',  # Domain/IP counts
    'amass_enum_osint_001': 'plotly.bar',  # Subdomain enumeration results
    'amass_viz_osint_001': 'graphviz.digraph',  # Network graph visualization
    'amass_track_osint_001': 'plotly.line',  # Track changes over time
    
    # Scanning tools
    'nuclei_scan_osint_001': 'plotly.bar',  # Vulnerabilities by severity
    'owasp_zap_scan_osint_001': 'plotly.bar',  # Alerts by risk
    'subfinder_enum_osint_001': 'plotly.bar',  # Subdomain counts
    'masscan_scan_osint_001': 'plotly.heatmap',  # Port scan results
    'zmap_scan_osint_001': 'plotly.heatmap',  # Port scan results
    
    # DNS and domain tools
    'dnsdumpster_search_osint_001': 'plotly.treemap',  # DNS hierarchy
    'waybackurls_osint_001': 'plotly.line',  # Historical URLs timeline
    
    # Social/username tools
    'holehe_osint_001': 'plotly.bar',  # Email registration status
    'maigret_osint_001': 'plotly.bar',  # Profile discovery results
    'sherlock_osint_001': 'graphviz.digraph',  # Username -> Platforms network
    
    # Dark web
    'onionsearch_osint_001': 'plotly.bar',  # Search results count
    
    # Browserless tools (web scraping)
    'browserless_content_osint_001': None,  # Text content, no visualization needed
    'browserless_scrape_osint_001': 'plotly.bar',  # Scraped data counts
    'browserless_screenshot_osint_001': 'image',  # Screenshot image
    'browserless_pdf_osint_001': 'pdf',  # PDF document
    'browserless_function_osint_001': 'plotly.bar',  # Function results
    'browserless_unblock_osint_001': None,  # Status, no chart needed
    
    # WebC Analysis tools
    'webc_analyze_webpage_osint_001': 'plotly.bar',  # Analysis metrics
    'webc_extract_text_osint_001': None,  # Text extraction, no chart
    'webc_get_webpage_response_osint_001': 'plotly.bar',  # Response metrics
    'webc_detect_language_osint_001': 'plotly.pie',  # Language distribution
    'webc_detect_multiple_languages_osint_001': 'plotly.bar',  # Multiple languages
    'webc_translate_text_osint_001': None,  # Translation, no chart
    'webc_translate_webpage_osint_001': None,  # Translation, no chart
    'webc_analyze_text_osint_001': 'plotly.bar',  # Text statistics
    'webc_extract_entities_osint_001': 'plotly.bar',  # Entity counts
    'webc_extract_emails_osint_001': 'plotly.bar',  # Email counts
    'webc_find_sensitive_data_osint_001': 'plotly.bar',  # Sensitive data types
    'webc_analyze_domain_osint_001': 'plotly.bar',  # Domain analysis metrics
    'webc_resolve_domain_ips_osint_001': 'plotly.bar',  # IP addresses
    'webc_get_domain_whois_osint_001': 'plotly.bar',  # WHOIS data
    'webc_get_ip_location_osint_001': 'map',  # IP geolocation map
    'webc_get_ip_whois_osint_001': 'plotly.bar',  # IP WHOIS data
    'webc_get_certificate_info_osint_001': 'plotly.bar',  # Certificate info
    'webc_get_domain_tld_info_osint_001': 'plotly.pie',  # TLD distribution
    'webc_calculate_text_similarity_osint_001': 'plotly.bar',  # Similarity scores
    'webc_calculate_similarity_spacy_osint_001': 'plotly.bar',  # Similarity scores
    'webc_extract_keyterms_osint_001': 'plotly.bar',  # Key terms
    'webc_extract_keyterms_textrank_osint_001': 'plotly.bar',  # Key terms
    'webc_get_readability_stats_osint_001': 'plotly.bar',  # Readability metrics
    'webc_scan_service_osint_001': 'plotly.bar',  # Port/service status
    'webc_ping_service_osint_001': 'plotly.line',  # Ping response times
    'webc_calculate_geo_distance_osint_001': 'plotly.bar',  # Distance metrics
    'webc_calculate_geoip_distance_osint_001': 'map',  # IP distance map
    'webc_calculate_geodomain_distance_osint_001': 'map',  # Domain distance map
    'webc_remove_stopwords_osint_001': None,  # Text processing, no chart
    'webc_validate_credit_card_osint_001': 'plotly.bar',  # Validation results
}


def suggest_visualizer(tool_id: str, tool_name: str) -> str:
    """
    Suggest a visualizer for a tool based on its ID and name.
    
    Returns:
        Visualizer string (e.g., "plotly.bar") or empty string if no visualization needed
    """
    # Check explicit mapping first
    if tool_id in VISUALIZER_MAPPINGS:
        visualizer = VISUALIZER_MAPPINGS[tool_id]
        return visualizer if visualizer else ''
    
    # Fallback: analyze tool name
    tool_name_lower = tool_name.lower()
    
    # Patterns for different visualizer types
    if any(keyword in tool_name_lower for keyword in ['enum', 'discover', 'find', 'search', 'scan']):
        return 'plotly.bar'  # Count-based results
    elif any(keyword in tool_name_lower for keyword in ['track', 'timeline', 'history', 'time']):
        return 'plotly.line'  # Time-based data
    elif any(keyword in tool_name_lower for keyword in ['location', 'geo', 'ip location', 'distance']):
        return 'map'  # Geographic data
    elif any(keyword in tool_name_lower for keyword in ['analyze', 'statistics', 'stats', 'metrics']):
        return 'plotly.bar'  # Analysis results
    elif any(keyword in tool_name_lower for keyword in ['extract', 'get', 'resolve']):
        return 'plotly.bar'  # Extracted data counts
    elif any(keyword in tool_name_lower for keyword in ['similarity', 'compare']):
        return 'plotly.bar'  # Comparison metrics
    elif any(keyword in tool_name_lower for keyword in ['language', 'translate']):
        return 'plotly.pie'  # Language distribution
    elif any(keyword in tool_name_lower for keyword in ['viz', 'visualization', 'graph']):
        return 'graphviz.digraph'  # Graph visualization
    else:
        # Default: bar chart for most tools
        return 'plotly.bar'


def main():
    """Update CSV with visualizer configurations."""
    script_dir = Path(__file__).parent
    csv_file = script_dir / 'tool_visualizers.csv'
    
    # Read existing CSV
    rows = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tool_id = row['tool_id']
            tool_name = row['tool_name']
            
            # If visualizer is empty, suggest one
            if not row.get('visualizer', '').strip():
                visualizer = suggest_visualizer(tool_id, tool_name)
                row['visualizer'] = visualizer
                print(f"Added visualizer for {tool_id} ({tool_name}): {visualizer}")
            
            rows.append(row)
    
    # Write updated CSV
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['tool_id', 'tool_name', 'visualizer'])
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\n✅ Updated CSV file: {csv_file}")
    print(f"   Total tools: {len(rows)}")
    print(f"   Tools with visualizer: {sum(1 for r in rows if r['visualizer'])}")


if __name__ == '__main__':
    main()

