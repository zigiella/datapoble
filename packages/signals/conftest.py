"""Assegura que ``datapoble_signals`` és importable als tests sense instal·lar el
paquet (mode worktree). Afegeix l'arrel del paquet a ``sys.path``.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
