"""Arc local integration diagnostics."""

from .contracts import (
    CONTRACT_REPORT_SCHEMA_VERSION,
    GuardianContractProbe,
    LimaContractProbe,
    build_contract_report,
)
from .doctor import (
    DoctorConfig,
    DoctorProbes,
    OllamaProbeResult,
    normalize_ollama_url,
    probe_guardian_contract,
    probe_lima_contract,
    probe_ollama_reachability,
    run_doctor,
)

__all__ = [
    "CONTRACT_REPORT_SCHEMA_VERSION",
    "DoctorConfig",
    "DoctorProbes",
    "GuardianContractProbe",
    "LimaContractProbe",
    "OllamaProbeResult",
    "build_contract_report",
    "normalize_ollama_url",
    "probe_guardian_contract",
    "probe_lima_contract",
    "probe_ollama_reachability",
    "run_doctor",
]
