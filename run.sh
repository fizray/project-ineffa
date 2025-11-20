#!/bin/bash

# Check if python3 is available
if command -v python3 &>/dev/null; then
    PYTHON_CMD=python3
else
    PYTHON_CMD=python
fi

# Run the launcher script
$PYTHON_CMD launch.py
