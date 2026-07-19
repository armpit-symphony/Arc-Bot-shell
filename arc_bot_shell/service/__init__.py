"""Windows-friendly local lifecycle contracts for Arc Bot."""

from .config import (
    ARC_STARTUP_TASK_NAME,
    ARC_V0_10_COMMIT,
    ARC_V0_10_ROLLBACK_TAG,
    ArcInstallPaths,
    OperatorConfig,
)
from .pidfile import (
    DuplicateServiceError,
    ManagedProcessRecord,
    acquire_pidfile,
    process_is_alive,
    read_pidfile,
    release_pidfile,
)

__all__ = [
    "ARC_STARTUP_TASK_NAME",
    "ARC_V0_10_COMMIT",
    "ARC_V0_10_ROLLBACK_TAG",
    "ArcInstallPaths",
    "DuplicateServiceError",
    "ManagedProcessRecord",
    "OperatorConfig",
    "acquire_pidfile",
    "process_is_alive",
    "read_pidfile",
    "release_pidfile",
]