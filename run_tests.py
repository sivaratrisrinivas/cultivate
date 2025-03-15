#!/usr/bin/env python3
# run_tests.py
import os
import sys
import subprocess
import time
from utils.logger import get_logger

# Set up logging
logger = get_logger("run_tests")

def run_test(test_script, description):
    """Run a test script and return the result."""
    logger.info(f"\n=== Running {description} ===")
    
    try:
        # Run the test script
        result = subprocess.run(
            [sys.executable, test_script],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Print output
        logger.info(result.stdout)
        
        if result.stderr:
            logger.error(result.stderr)
        
        # Return success/failure
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error running {test_script}: {str(e)}")
        return False

def main():
    """Run all test scripts."""
    # Create necessary directories
    for dir_path in ['data', 'cache', 'logs', 'templates/memes']:
        os.makedirs(dir_path, exist_ok=True)
    
    # Define tests to run
    tests = [
        ("test_blockchain.py", "Blockchain Module Tests"),
        ("test_ai.py", "AI Module Tests"),
        ("test_discord_bot.py", "Discord Bot Tests"),
        ("test_api.py", "API Tests")
    ]
    
    # Run tests
    results = {}
    for test_script, description in tests:
        results[description] = run_test(test_script, description)
        # Add a small delay between tests
        time.sleep(2)
    
    # Print summary
    logger.info("\n=== Overall Test Summary ===")
    all_passed = True
    
    for description, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        logger.info(f"{description}: {status}")
        all_passed = all_passed and passed
    
    if all_passed:
        logger.info("\nAll tests PASSED! The system is working correctly.")
        return 0
    else:
        logger.error("\nSome tests FAILED! Please check the logs for details.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)
