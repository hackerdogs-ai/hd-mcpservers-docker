#!/usr/bin/env python3
"""
Comprehensive Test Execution Script

This script executes all tests with proper error handling and provides
a detailed report. It handles missing dependencies gracefully and
downloads test images from the web.

Usage:
    python execute_comprehensive_tests.py [--verbose] [--coverage] [test_file_pattern]
"""

import sys
import os
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional

# Add parent directories to path
current_dir = Path(__file__).parent.absolute()
project_root = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def check_dependencies() -> Dict[str, bool]:
    """Check which dependencies are available."""
    deps = {
        'pytest': False,
        'openpyxl': False,
        'pandas': False,
        'python-pptx': False,
        'plotly': False,
        'streamlit': False,
        'pytesseract': False,
        'easyocr': False,
        'PIL': False,
        'requests': False,
    }
    
    for dep in deps.keys():
        try:
            if dep == 'pytest':
                import pytest
            elif dep == 'openpyxl':
                from openpyxl import Workbook
            elif dep == 'pandas':
                import pandas
            elif dep == 'python-pptx':
                from pptx import Presentation
            elif dep == 'plotly':
                import plotly
            elif dep == 'streamlit':
                import streamlit
            elif dep == 'pytesseract':
                import pytesseract
            elif dep == 'easyocr':
                import easyocr
            elif dep == 'PIL':
                from PIL import Image
            elif dep == 'requests':
                import requests
            deps[dep] = True
        except ImportError:
            pass
    
    return deps


def download_test_images() -> bool:
    """Download test images from web for OCR testing."""
    try:
        import requests
        from PIL import Image
        import io
        
        test_urls = [
            "https://via.placeholder.com/600x300/FFFFFF/000000?text=OCR+Test+Image+123",
            "https://httpbin.org/image/png",
        ]
        
        downloaded = 0
        for url in test_urls:
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                img = Image.open(io.BytesIO(response.content))
                downloaded += 1
                print(f"✅ Downloaded test image from {url}")
            except Exception as e:
                print(f"⚠️  Could not download {url}: {e}")
        
        return downloaded > 0
    except ImportError:
        print("⚠️  requests or PIL not available, skipping image downloads")
        return False


def run_tests(test_files: Optional[List[str]] = None, verbose: bool = False, coverage: bool = False) -> int:
    """Run pytest tests."""
    cmd = ["python3", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=term-missing"])
    
    if test_files:
        cmd.extend(test_files)
    else:
        # Run all test files
        test_pattern = str(current_dir / "test_*.py")
        cmd.append(test_pattern)
    
    cmd.extend(["--tb=short", "-x"])  # Stop on first failure, short traceback
    
    print(f"\n{'='*60}")
    print("Running Tests")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(cmd, cwd=str(current_dir), capture_output=False)
        return result.returncode
    except FileNotFoundError:
        print("❌ ERROR: pytest not found. Install with: pip install pytest")
        return 1
    except Exception as e:
        print(f"❌ ERROR running tests: {e}")
        return 1


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Execute comprehensive tests for prodx tools")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", "-c", action="store_true", help="Generate coverage report")
    parser.add_argument("--download-images", "-i", action="store_true", help="Download test images from web")
    parser.add_argument("test_files", nargs="*", help="Specific test files to run (default: all)")
    
    args = parser.parse_args()
    
    print("="*60)
    print("PRODX TOOLS - COMPREHENSIVE TEST EXECUTION")
    print("="*60)
    
    # Check dependencies
    print("\n📦 Checking Dependencies...")
    deps = check_dependencies()
    for dep, available in deps.items():
        status = "✅" if available else "❌"
        print(f"  {status} {dep}")
    
    missing_critical = [dep for dep in ['pytest'] if not deps[dep]]
    if missing_critical:
        print(f"\n❌ Missing critical dependencies: {', '.join(missing_critical)}")
        print("Install with: pip install pytest")
        return 1
    
    # Download test images if requested
    if args.download_images:
        print("\n🌐 Downloading Test Images...")
        download_test_images()
    
    # Run tests
    test_files = args.test_files if args.test_files else None
    exit_code = run_tests(test_files, args.verbose, args.coverage)
    
    # Summary
    print(f"\n{'='*60}")
    if exit_code == 0:
        print("✅ ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print(f"{'='*60}\n")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

