#!/usr/bin/env python3
"""
Unit test runner for the Cultivate project.
Runs all unit tests and generates a report.
"""

import os
import sys
import pytest
import argparse
from colorama import init, Fore, Style

# Initialize colorama for colored terminal output
init()

def print_header(text):
    """Print a formatted header."""
    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"{Fore.CYAN}{text.center(80)}")
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")

def print_section(text):
    """Print a formatted section header."""
    print(f"\n{Fore.GREEN}{'-' * 80}")
    print(f"{Fore.GREEN}{text}")
    print(f"{Fore.GREEN}{'-' * 80}{Style.RESET_ALL}\n")

def run_tests(module=None, verbose=False):
    """Run the unit tests."""
    print_header("CULTIVATE UNIT TESTS")
    
    # Build the pytest arguments
    args = ["-xvs" if verbose else "-x"]
    
    # Add test directory
    test_dir = os.path.join(os.path.dirname(__file__), "tests", "unit")
    
    # If a specific module is specified, run only those tests
    if module:
        module_path = os.path.join(test_dir, f"test_{module}.py")
        if os.path.exists(module_path):
            args.append(module_path)
        else:
            print(f"{Fore.RED}Error: Module test file not found: {module_path}{Style.RESET_ALL}")
            return 1
    else:
        args.append(test_dir)
    
    # Run the tests
    print_section(f"Running tests for {'all modules' if not module else module}")
    result = pytest.main(args)
    
    # Print the result
    if result == 0:
        print_section(f"{Fore.GREEN}All tests passed!{Style.RESET_ALL}")
    else:
        print_section(f"{Fore.RED}Some tests failed!{Style.RESET_ALL}")
    
    return result

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run unit tests for the Cultivate project")
    parser.add_argument("-m", "--module", help="Specific module to test (blockchain, ai, notification, utils)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()
    
    # Run the tests
    return run_tests(args.module, args.verbose)

if __name__ == "__main__":
    sys.exit(main())
