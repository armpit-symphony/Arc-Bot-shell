"""Phase-5 office workflow template contracts."""

from __future__ import annotations

from importlib import import_module
from typing import Any


_REEXPORTS: dict[str, tuple[str, str]] = {
    "PHASE5_APPROVAL_REQUIRED_ACTIONS": (
        ".workflows",
        "PHASE5_APPROVAL_REQUIRED_ACTIONS",
    ),
    "PHASE5_ROLE_PROFILE_IDS": (".workflows", "PHASE5_ROLE_PROFILE_IDS"),
    "PHASE5_WORKFLOW_IDS": (".workflows", "PHASE5_WORKFLOW_IDS"),
    "OfficeWorkflowRequest": (".workflows", "OfficeWorkflowRequest"),
    "OfficeWorkflowTemplateError": (".workflows", "OfficeWorkflowTemplateError"),
    "build_office_workflow_preview": (
        ".workflows",
        "build_office_workflow_preview",
    ),
    "build_office_workflow_template_catalog": (
        ".workflows",
        "build_office_workflow_template_catalog",
    ),
    "run_office_workflow_templates_preview": (
        ".workflows",
        "run_office_workflow_templates_preview",
    ),
}


def __getattr__(name: str) -> Any:
    mapping = _REEXPORTS.get(name)
    if mapping is None:
        raise AttributeError(name)

    module_name, symbol_name = mapping
    symbol = getattr(import_module(module_name, package=__name__), symbol_name)
    globals()[name] = symbol
    return symbol


__all__ = list(_REEXPORTS)
