#!/usr/bin/env python3
"""
Main entry point for the Smart International Sales Data Harmonizer CLI.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli.cli import cli

if __name__ == '__main__':
    cli()