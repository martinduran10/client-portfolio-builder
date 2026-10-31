"""Ensure ``src/`` is importable so ``import cpb`` works without installing."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
