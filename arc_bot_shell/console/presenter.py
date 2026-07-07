"""Console output helpers for Arc Harness Shell."""

from __future__ import annotations

import json
from typing import Any


def render_json(payload: dict[str, Any], compact: bool = False) -> str:
    if compact:
        return json.dumps(payload, sort_keys=True)
    return json.dumps(payload, indent=2, sort_keys=True)
