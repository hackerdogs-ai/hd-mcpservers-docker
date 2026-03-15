#!/bin/bash
# Entrypoint script for OSINT tools container

set -e

echo "OSINT Tools Container Starting..."
echo "Available tools:"
echo "  - amass"
echo "  - nuclei"
echo "  - subfinder"
echo "  - masscan"
echo "  - zmap"
echo "  - waybackurls"
echo "  - exiftool"
echo "  - yara"
echo "  - Python OSINT tools (sublist3r, theHarvester, etc.)"

# Verify tools are installed
echo ""
echo "Verifying tool installations..."

command -v amass >/dev/null 2>&1 && echo "✓ Amass installed" || echo "✗ Amass not found"
command -v nuclei >/dev/null 2>&1 && echo "✓ Nuclei installed" || echo "✗ Nuclei not found"
command -v subfinder >/dev/null 2>&1 && echo "✓ Subfinder installed" || echo "✗ Subfinder not found"
command -v masscan >/dev/null 2>&1 && echo "✓ Masscan installed" || echo "✗ Masscan not found"
command -v zmap >/dev/null 2>&1 && echo "✓ ZMap installed" || echo "✗ ZMap not found"
command -v waybackurls >/dev/null 2>&1 && echo "✓ Waybackurls installed" || echo "✗ Waybackurls not found"
command -v exiftool >/dev/null 2>&1 && echo "✓ ExifTool installed" || echo "✗ ExifTool not found"
command -v yara >/dev/null 2>&1 && echo "✓ YARA installed" || echo "✗ YARA not found"

echo ""
echo "Container ready. Waiting for commands..."

# Execute command if provided, otherwise keep container running
if [ $# -gt 0 ]; then
    exec "$@"
else
    # Keep container running
    tail -f /dev/null
fi

