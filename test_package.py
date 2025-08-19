#!/usr/bin/env python3
"""Simple test script to verify MLGEFS package installation."""

import sys
import importlib

def test_import(module_name):
    """Test if a module can be imported."""
    try:
        importlib.import_module(module_name)
        print(f"✓ {module_name} imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import {module_name}: {e}")
        return False

def main():
    """Run basic import tests."""
    print("Testing MLGEFS package imports...")
    print("=" * 50)

    modules_to_test = [
        "mlgefs",
        "mlgefs.oper",
        "mlgefs.training",
        "mlgefs.oper.utils",
    ]

    success_count = 0

    for module in modules_to_test:
        if test_import(module):
            success_count += 1

    print("=" * 50)
    print(f"Results: {success_count}/{len(modules_to_test)} modules imported successfully")

    if success_count == len(modules_to_test):
        print("🎉 All basic imports successful!")
        return 0
    else:
        print("⚠️  Some imports failed. Check dependencies and package structure.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
