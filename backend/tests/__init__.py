"""Ziggy backend test package.

Run:  python3 -m unittest discover -s backend/tests -t backend
      (or: cd backend && python3 -m unittest discover -s tests -v)
Put the backend package on sys.path so tests import plain 'engine' /
'server' modules (no install required)."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))