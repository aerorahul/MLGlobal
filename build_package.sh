#!/bin/bash

# MLGEFS Package Build Script
# This script sets up the package structure and builds the MLGEFS package

set -e

echo "Setting up MLGEFS package structure..."

# Create package directories if they don't exist
mkdir -p mlgefs/oper/utils
mkdir -p mlgefs/training

# Copy Python modules to package structure
echo "Copying Python modules..."

# Copy operational scripts
if [ -d "oper" ]; then
    cp oper/*.py mlgefs/oper/ 2>/dev/null || echo "No Python files in oper/ to copy"
    cp oper/utils/*.py mlgefs/oper/utils/ 2>/dev/null || echo "No Python files in oper/utils/ to copy"
fi

# Copy training scripts
if [ -d "training" ]; then
    cp training/*.py mlgefs/training/ 2>/dev/null || echo "No Python files in training/ to copy"
fi

# Copy shell scripts and configuration files
echo "Copying configuration files..."
if [ -d "oper" ]; then
    cp oper/*.sh mlgefs/oper/ 2>/dev/null || echo "No shell scripts in oper/ to copy"
    cp oper/*.json mlgefs/oper/ 2>/dev/null || echo "No JSON files in oper/ to copy"

    if [ -d "oper/ursa" ]; then
        mkdir -p mlgefs/oper/ursa
        cp oper/ursa/* mlgefs/oper/ursa/ 2>/dev/null || echo "No files in oper/ursa/ to copy"
    fi
fi

# Ensure __init__.py files exist and have correct imports
echo "Setting up package imports..."

# Update __init__.py files to import the copied modules
cat > mlgefs/oper/__init__.py << 'EOF'
"""Operations module for MLGEFS

This module contains operational scripts for running the GraphCast ensemble model
with GEFS data, including initial condition generation and model execution.
"""

try:
    from .gen_gefs_ics import GFSDataProcessor
    __all__ = ["GFSDataProcessor"]
except ImportError:
    __all__ = []
EOF

cat > mlgefs/training/__init__.py << 'EOF'
"""Training module for MLGEFS

This module contains training utilities and data processing scripts
for the GraphCast ensemble model.
"""

try:
    from .generate_batch_files import GEFSDataProcessor
    __all__ = ["GEFSDataProcessor"]
except ImportError:
    __all__ = []
EOF

cat > mlgefs/oper/utils/__init__.py << 'EOF'
"""Utilities for MLGEFS operations"""

try:
    from .nc2grib import Netcdf2Grib
    __all__ = ["Netcdf2Grib"]
except ImportError:
    __all__ = []
EOF

echo "Package structure setup complete!"

# Check if build tools are available
if command -v python -m build &> /dev/null; then
    echo "Building package..."
    python -m build
    echo "Package built successfully! Check the dist/ directory."
elif command -v python setup.py &> /dev/null; then
    echo "Building package with setup.py..."
    python setup.py sdist bdist_wheel
    echo "Package built successfully! Check the dist/ directory."
else
    echo "Build tools not found. Please install build tools:"
    echo "pip install build"
    echo "Then run: python -m build"
fi

echo ""
echo "To install the package in development mode:"
echo "pip install -e ."
echo ""
echo "To install from the built package:"
echo "pip install dist/mlgefs-0.1.0-py3-none-any.whl"
