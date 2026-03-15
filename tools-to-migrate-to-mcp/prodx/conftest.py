"""
Pytest configuration for prodx tools tests.
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Ensure current directory is in path
if '.' not in sys.path:
    sys.path.insert(0, '.')

