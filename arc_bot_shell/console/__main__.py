"""Module entrypoint for Arc Harness Shell console commands."""

from __future__ import annotations

import sys

from .commands import main


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
