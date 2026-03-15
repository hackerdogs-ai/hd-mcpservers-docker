"""
Test runner for all prodx tools tests.

Run all tests:
    python run_tests.py

Run specific test file:
    python run_tests.py test_excel_tools.py

Run with verbose output:
    python run_tests.py -v
"""

import sys
import os
import subprocess

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

def run_tests(test_file=None, verbose=False):
    """Run pytest tests."""
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if test_file:
        cmd.append(test_file)
    else:
        # Run all test files
        test_files = [
            "test_excel_tools.py",
            "test_powerpoint_tools.py",
            "test_visualization_tools.py",
            "test_ocr_tools.py",
            "test_file_operations_tools.py"
        ]
        cmd.extend(test_files)
    
    cmd.extend(["--tb=short", "-x"])  # Stop on first failure, short traceback
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__))
    return result.returncode


if __name__ == "__main__":
    verbose = "-v" in sys.argv or "--verbose" in sys.argv
    
    # Check if specific test file provided
    test_files = [f for f in sys.argv[1:] if f.endswith(".py") and not f.startswith("-")]
    test_file = test_files[0] if test_files else None
    
    exit_code = run_tests(test_file, verbose)
    sys.exit(exit_code)

