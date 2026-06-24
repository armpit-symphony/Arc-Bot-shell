"""README local artifact references resolve to real repo files or modules."""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
README_PATH = REPO_ROOT / "README.md"


def test_readme_markdown_local_links_exist() -> None:
    readme = README_PATH.read_text(encoding="utf-8")
    links = re.findall(r"\]\((?!https?://)([^)#]+)", readme)

    missing = []
    for link in links:
        path = (REPO_ROOT / link).resolve()
        try:
            path.relative_to(REPO_ROOT)
        except ValueError:
            continue
        if not path.exists():
            missing.append(link)

    assert not missing, f"README local markdown links are missing: {missing}"


def test_readme_advertised_python_modules_import() -> None:
    readme = README_PATH.read_text(encoding="utf-8")
    modules = sorted(set(re.findall(r"python(?: -B)? -m ([A-Za-z0-9_.]+)", readme)))

    missing = [module for module in modules if importlib.util.find_spec(module) is None]

    assert not missing, f"README advertised python modules are missing: {missing}"


def test_readme_advertised_guardrail_artifacts_exist() -> None:
    readme = README_PATH.read_text(encoding="utf-8")
    references = set(re.findall(r"`(\./scripts/[^` ]+)", readme))
    references.update(re.findall(r"`(\.github/workflows/[^`]+)`", readme))

    missing = []
    for reference in sorted(references):
        normalized = reference[2:] if reference.startswith("./") else reference
        if not (REPO_ROOT / normalized).exists():
            missing.append(reference)

    assert not missing, f"README advertised guardrail artifacts are missing: {missing}"
