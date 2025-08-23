"""
Simple launcher for the legacy photo digitization app.

- Creates required folders (Ingest, Processed Photos, Debug Output)
- Starts the legacy_main_processing entrypoint

Usage:
  python run_legacy_demo.py
"""
import os
import sys

# Ensure local imports resolve
APP_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, APP_DIR)

from legacy_main_processing import main

if __name__ == "__main__":
    # Pre-create expected directories
    for d in ("Ingest", "Processed Photos", "Debug Output"):
        os.makedirs(os.path.join(APP_DIR, d), exist_ok=True)
    main()
