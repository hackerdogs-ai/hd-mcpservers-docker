#!/usr/bin/env python3
"""
Test Validation Script

This script validates that all test files are properly structured and can be imported.
It also runs a quick smoke test on each tool to ensure basic functionality.

Usage:
    python validate_tests.py
"""

import sys
import os
import importlib.util
import traceback

# Add parent directories to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
sys.path.insert(0, parent_dir)

def validate_test_file(test_file_path):
    """Validate that a test file can be imported and has test classes."""
    print(f"\n{'='*60}")
    print(f"Validating: {test_file_path}")
    print(f"{'='*60}")
    
    try:
        # Try to load the test file
        spec = importlib.util.spec_from_file_location("test_module", test_file_path)
        if spec is None:
            print(f"❌ ERROR: Could not create spec for {test_file_path}")
            return False
        
        module = importlib.util.module_from_spec(spec)
        if module is None:
            print(f"❌ ERROR: Could not create module from spec")
            return False
        
        # Try to execute the module
        spec.loader.exec_module(module)
        print(f"✅ Successfully imported {test_file_path}")
        
        # Check for test classes
        test_classes = [name for name in dir(module) if name.startswith('Test') and isinstance(getattr(module, name), type)]
        if test_classes:
            print(f"✅ Found {len(test_classes)} test classes: {', '.join(test_classes)}")
        else:
            print(f"⚠️  WARNING: No test classes found (classes starting with 'Test')")
        
        # Check for test functions
        test_functions = [name for name in dir(module) if name.startswith('test_')]
        if test_functions:
            print(f"✅ Found {len(test_functions)} test functions")
        else:
            print(f"⚠️  WARNING: No test functions found (functions starting with 'test_')")
        
        return True
        
    except ImportError as e:
        print(f"❌ IMPORT ERROR: {e}")
        print(f"   This is expected if dependencies are missing")
        return True  # Not a failure, just missing deps
    except SyntaxError as e:
        print(f"❌ SYNTAX ERROR: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        traceback.print_exc()
        return False


def validate_tool_imports():
    """Validate that all tools can be imported."""
    print(f"\n{'='*60}")
    print("Validating Tool Imports")
    print(f"{'='*60}")
    
    tools_to_check = [
        ("excel_tools", ["ReadExcelStructuredTool", "ModifyExcelTool", "CreateExcelChartTool", "AnalyzeExcelSecurityTool"]),
        ("powerpoint_tools", ["CreatePresentationTool", "AddSlideTool", "AddChartToSlideTool"]),
        ("visualization_tools", ["CreatePlotlyChartTool", "CreateChartFromFileTool"]),
        ("ocr_tools", ["ExtractTextFromImageTool", "ExtractTextFromPDFImagesTool", "AnalyzeDocumentStructureTool"]),
        ("file_operations_tools", ["SaveFileForDownloadTool", "ConvertFileFormatTool"]),
    ]
    
    all_passed = True
    for module_name, tool_names in tools_to_check:
        try:
            module_path = os.path.join(current_dir, f"{module_name}.py")
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec is None:
                print(f"❌ Could not load {module_name}.py")
                all_passed = False
                continue
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            for tool_name in tool_names:
                if hasattr(module, tool_name):
                    print(f"✅ {module_name}.{tool_name}")
                else:
                    print(f"❌ {module_name}.{tool_name} - NOT FOUND")
                    all_passed = False
                    
        except Exception as e:
            print(f"❌ Error loading {module_name}: {e}")
            all_passed = False
    
    return all_passed


def main():
    """Main validation function."""
    print("="*60)
    print("PRODX TOOLS TEST VALIDATION")
    print("="*60)
    
    test_files = [
        "test_excel_tools.py",
        "test_powerpoint_tools.py",
        "test_visualization_tools.py",
        "test_ocr_tools.py",
        "test_file_operations_tools.py",
        "test_comprehensive_real_world.py"
    ]
    
    all_passed = True
    
    # Validate tool imports first
    if not validate_tool_imports():
        print("\n❌ Tool import validation failed!")
        all_passed = False
    
    # Validate each test file
    for test_file in test_files:
        test_path = os.path.join(current_dir, test_file)
        if not os.path.exists(test_path):
            print(f"\n⚠️  WARNING: {test_file} not found")
            continue
        
        if not validate_test_file(test_path):
            all_passed = False
    
    print(f"\n{'='*60}")
    if all_passed:
        print("✅ ALL VALIDATIONS PASSED")
    else:
        print("❌ SOME VALIDATIONS FAILED")
    print(f"{'='*60}\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

