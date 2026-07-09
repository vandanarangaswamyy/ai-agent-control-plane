from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def _export_manifest() -> None:
    from app.services import seed_manifest as manifest

    exported_names = [name for name in dir(manifest) if not name.startswith("_")]
    globals().update({name: getattr(manifest, name) for name in exported_names})


_export_manifest()
