#!/usr/bin/env python3
"""
LLM Agent Test Runner

Runs comprehensive LLM agent tests for prodx tools using Ollama (qwen3:latest).

Usage:
    python run_llm_tests.py [options]

Options:
    --verbose, -v          Verbose output showing agent reasoning
    --tool TOOL_NAME       Test specific tool category (excel, powerpoint, visualization, ocr, file_ops, all)
    --prompt PROMPT_NAME   Test specific prompt by name
    --timeout SECONDS      Test timeout in seconds (default: 300)
    --base-url URL         Ollama base URL (default: http://192.168.5.217:11434)
    --model MODEL          Ollama model (default: qwen3:latest)
"""

import sys
import os
import asyncio
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import test module
try:
    from shared.modules.tools.prodx.test_llm_agent_integration import (
        LLMAgentTester,
        TestExcelToolsWithLLM,
        TestPowerPointToolsWithLLM,
        TestVisualizationToolsWithLLM,
        TestOCRToolsWithLLM,
        TestFileOperationsWithLLM,
        TestComplexWorkflowsWithLLM
    )
    from shared.modules.tools.prodx.test_llm_prompts import ALL_PROMPTS
except ImportError as e:
    print(f"❌ Error importing test modules: {e}")
    sys.exit(1)


class TestRunner:
    """Test runner for LLM agent tests."""
    
    def __init__(self, base_url: str, model: str, verbose: bool = False):
        """Initialize test runner."""
        self.base_url = base_url
        self.model = model
        self.verbose = verbose
        self.results = []
    
    async def run_test_class(self, test_class, test_method_name: str = None):
        """Run tests from a test class."""
        tester = LLMAgentTester(base_url=self.base_url, model=self.model)
        
        # Get test methods
        test_methods = [
            method for method in dir(test_class)
            if method.startswith('test_') and callable(getattr(test_class, method))
        ]
        
        if test_method_name:
            test_methods = [m for m in test_methods if test_method_name in m]
        
        print(f"\n{'='*60}")
        print(f"Running {len(test_methods)} tests from {test_class.__name__}")
        print(f"{'='*60}\n")
        
        for method_name in test_methods:
            print(f"\n🧪 Test: {method_name}")
            print("-" * 60)
            
            try:
                test_instance = test_class()
                test_method = getattr(test_instance, method_name)
                
                # Check if it's async
                if asyncio.iscoroutinefunction(test_method):
                    result = await test_method(tester)
                else:
                    result = test_method(tester)
                
                if result:
                    print(f"✅ {method_name}: PASSED")
                else:
                    print(f"❌ {method_name}: FAILED")
                
                self.results.append({
                    "class": test_class.__name__,
                    "method": method_name,
                    "status": "passed" if result else "failed",
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                print(f"❌ {method_name}: ERROR - {e}")
                self.results.append({
                    "class": test_class.__name__,
                    "method": method_name,
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
    
    def print_summary(self):
        """Print test summary."""
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}")
        
        total = len(self.results)
        passed = len([r for r in self.results if r["status"] == "passed"])
        failed = len([r for r in self.results if r["status"] == "failed"])
        errors = len([r for r in self.results if r["status"] == "error"])
        
        print(f"Total tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Errors: {errors}")
        print(f"Success rate: {(passed/total*100) if total > 0 else 0:.1f}%")
        
        if failed > 0 or errors > 0:
            print(f"\n{'='*60}")
            print("FAILED TESTS:")
            print(f"{'='*60}")
            for result in self.results:
                if result["status"] in ["failed", "error"]:
                    print(f"❌ {result['class']}.{result['method']}")
                    if "error" in result:
                        print(f"   Error: {result['error']}")
        
        print(f"\n{'='*60}\n")


async def main():
    """Main test execution."""
    parser = argparse.ArgumentParser(description="Run LLM agent tests for prodx tools")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--tool", choices=["excel", "powerpoint", "visualization", "ocr", "file_ops", "workflows", "all"], 
                       default="all", help="Tool category to test")
    parser.add_argument("--timeout", type=int, default=300, help="Test timeout in seconds")
    parser.add_argument("--base-url", default="http://192.168.5.217:11434", help="Ollama base URL")
    parser.add_argument("--model", default="qwen3:latest", help="Ollama model")
    parser.add_argument("--method", help="Specific test method to run")
    
    args = parser.parse_args()
    
    print("="*60)
    print("PRODX TOOLS - LLM AGENT INTEGRATION TESTS")
    print("="*60)
    print(f"Model: {args.model}")
    print(f"Base URL: {args.base_url}")
    print(f"Tool Category: {args.tool}")
    print(f"Verbose: {args.verbose}")
    print("="*60)
    
    runner = TestRunner(
        base_url=args.base_url,
        model=args.model,
        verbose=args.verbose
    )
    
    # Map tool categories to test classes
    test_classes = {
        "excel": [TestExcelToolsWithLLM],
        "powerpoint": [TestPowerPointToolsWithLLM],
        "visualization": [TestVisualizationToolsWithLLM],
        "ocr": [TestOCRToolsWithLLM],
        "file_ops": [TestFileOperationsWithLLM],
        "workflows": [TestComplexWorkflowsWithLLM],
        "all": [
            TestExcelToolsWithLLM,
            TestPowerPointToolsWithLLM,
            TestVisualizationToolsWithLLM,
            TestOCRToolsWithLLM,
            TestFileOperationsWithLLM,
            TestComplexWorkflowsWithLLM
        ]
    }
    
    classes_to_run = test_classes.get(args.tool, test_classes["all"])
    
    # Run tests
    for test_class in classes_to_run:
        await runner.run_test_class(test_class, args.method)
    
    # Print summary
    runner.print_summary()
    
    # Save results
    results_file = Path(__file__).parent / "llm_test_results.json"
    with open(results_file, 'w') as f:
        json.dump(runner.results, f, indent=2)
    print(f"📄 Results saved to: {results_file}")


if __name__ == "__main__":
    asyncio.run(main())

