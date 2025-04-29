#!/bin/bash
# Exit on error
set -e

# Print each command
set -x

# Install Python dependencies
pip install -r requirements.txt

# Print Python version
python --version

# Print installed packages
pip list
