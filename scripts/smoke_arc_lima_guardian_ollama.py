"""Retired Arc Ollama smoke retained as a fail-closed compatibility entry."""

from __future__ import annotations

import json


def main() -> int:
    """Report the retired route without probing or executing anything."""

    print(
        json.dumps(
            {
                "status": "blocked",
                "reason": (
                    "retired Arc-to-Ollama execution smoke is disabled; "
                    "use the non-executing governed Supervisor preflight"
                ),
                "guardian_called": False,
                "lima_called": False,
                "ollama_called": False,
                "network_called": False,
                "credentials_used": False,
                "external_side_effects": False,
                "execution_allowed": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 4


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
