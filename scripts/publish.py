#!/usr/bin/env python3

"""
Script to build and publish the package to PyPI.

Usage:
    python3 scripts/publish.py [--test]

Options:
    --test: Upload to TestPyPI instead of PyPI
"""

import argparse
import os
import subprocess
import sys


def run_command(command, description=None):
    """Run a shell command and print its output."""
    if description:
        print(f"\n{description}...")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    if result.returncode != 0:
        print(f"Error: Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    
    return result


def main():
    """Build and publish the package to PyPI."""
    parser = argparse.ArgumentParser(description="Build and publish the package to PyPI")
    parser.add_argument("--test", action="store_true", help="Upload to TestPyPI instead of PyPI")
    args = parser.parse_args()
    
    # Get the path to the current Python interpreter
    python_executable = sys.executable
    
    # Ensure we're in the project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(os.path.dirname(script_dir))
    
    # Clean up previous builds
    run_command("rm -rf build/ dist/ *.egg-info/", "Cleaning up previous builds")
    
    # Install build dependencies
    run_command(f"{python_executable} -m pip install --upgrade build twine", "Installing build dependencies")
    
    # Build the package
    run_command(f"{python_executable} -m build", "Building the package")
    
    # Upload to PyPI or TestPyPI
    if args.test:
        run_command(
            f"{python_executable} -m twine upload --repository testpypi dist/*",
            "Uploading to TestPyPI"
        )
        print("\nPackage uploaded to TestPyPI!")
        print("You can install it with:")
        print("pip install --index-url https://test.pypi.org/simple/ asterisk-mcp-server")
    else:
        run_command(
            f"{python_executable} -m twine upload dist/*",
            "Uploading to PyPI"
        )
        print("\nPackage uploaded to PyPI!")
        print("You can install it with:")
        print("pip install asterisk-mcp-server")


if __name__ == "__main__":
    main()
