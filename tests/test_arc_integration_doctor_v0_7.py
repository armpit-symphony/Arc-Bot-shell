"""Arc local integration doctor tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from arc_bot_shell.integrations import (
    DoctorConfig,
    DoctorProbes,
    GuardianContractProbe,
    LimaContractProbe,
    OllamaProbeResult,
    build_contract_report,
    normalize_ollama_url,
    run_doctor,
)
from arc_bot_shell.integrations.doctor import main


def _guardian(*, compatible: bool = True) -> GuardianContractProbe:
    return GuardianContractProbe(
        available=True,
        mode="real_guardian",
        import_path="guardian.public",
        evaluation_entrypoint="guardian.public.evaluate",
        request_input_type="GuardianRequest",
        decision_output_type="GuardianDecision",
        decision_id_field="decision_id" if compatible else None,
        requires_sparkbot_imports=False,
        integration_compatible=compatible,
        blockers=() if compatible else ("guardian_contract_missing_decision_id",),
    )


def _lima(*, compatible: bool = True) -> LimaContractProbe:
    return LimaContractProbe(
        available=True,
        import_path="lima.harness",
        runtime_entrypoint="lima.harness.execute_v1_live_provider_model_call",
        runtime_input_type="Mapping[str, Any]",
        runtime_output_type="dict[str, Any]",
        provider_executor_interface=(
            "Callable[[Mapping[str, Any]], Mapping[str, Any]]"
        ),
        guardian_request_type="ConsequentialActionRequest",
        guardian_decision_type="GuardianDecision",
        decision_id_field="decision_id" if compatible else None,
        requires_sparkbot_imports=False,
        integration_compatible=compatible,
        blockers=() if compatible else ("lima_contract_missing_decision_id",),
        decision_id_propagation_supported=compatible,
        fake_executor_smoke_ready=compatible,
    )


def _configured(
    tmp_path: Path, *, ollama_url: str = "http://127.0.0.1:11434"
) -> DoctorConfig:
    guardian_path = tmp_path / "guardian"
    lima_path = tmp_path / "lima"
    guardian_path.mkdir()
    lima_path.mkdir()
    return DoctorConfig(
        guardian_path=guardian_path,
        lima_path=lima_path,
        ollama_url=ollama_url,
        ollama_model="qwen2.5:7b",
    )


def test_missing_configuration_uses_installed_lima_without_network() -> None:
    def unexpected_path_probe(_path: Path) -> object:
        raise AssertionError(
            "dependency probe must not run without explicit configuration"
        )

    def unexpected_ollama_probe(
        _url: str,
        _model: str,
        _timeout: float,
    ) -> OllamaProbeResult:
        raise AssertionError("Ollama probe must not run without explicit configuration")

    report = run_doctor(
        DoctorConfig(None, None, None, None),
        DoctorProbes(
            guardian=unexpected_path_probe,  # type: ignore[arg-type]
            lima=lambda _path: _lima(),
            ollama=unexpected_ollama_probe,
        ),
    )

    assert report["guardian_available"] is False
    assert report["lima_available"] is True
    assert report["ollama_configured"] is False
    assert report["ollama_reachable"] is False
    assert report["ollama_model_available"] is False
    assert report["local_integration_ready"] is False
    assert report["blockers"] == [
        "ARC_GUARDIAN_PATH_not_configured",
        "ARC_OLLAMA_URL_not_configured",
        "ARC_OLLAMA_MODEL_not_configured",
    ]


def test_available_fake_contracts_and_ollama_report_ready(tmp_path: Path) -> None:
    observed: dict[str, object] = {}

    def reachable(url: str, model: str, timeout: float) -> OllamaProbeResult:
        observed["url"] = url
        observed["model"] = model
        observed["timeout"] = timeout
        return OllamaProbeResult(reachable=True, model_available=True)

    report = run_doctor(
        _configured(tmp_path),
        DoctorProbes(
            guardian=lambda _path: _guardian(),
            lima=lambda _path: _lima(),
            ollama=reachable,
        ),
    )

    assert report["arc_available"] is True
    assert report["guardian_available"] is True
    assert report["lima_available"] is True
    assert report["ollama_configured"] is True
    assert report["ollama_reachable"] is True
    assert report["ollama_model_available"] is True
    assert report["ollama_model"] == "qwen2.5:7b"
    assert report["local_integration_ready"] is True
    assert report["blockers"] == []
    assert observed["url"] == "http://127.0.0.1:11434"
    assert observed["model"] == "qwen2.5:7b"
    assert float(observed["timeout"]) < 1.0


def test_guardian_without_decision_id_blocks_readiness(tmp_path: Path) -> None:
    report = run_doctor(
        _configured(tmp_path),
        DoctorProbes(
            guardian=lambda _path: _guardian(compatible=False),
            lima=lambda _path: _lima(),
            ollama=lambda _url, _model, _timeout: OllamaProbeResult(True, True),
        ),
    )

    assert report["guardian_available"] is True
    assert report["local_integration_ready"] is False
    assert "guardian_contract_missing_decision_id" in report["blockers"]


def test_remote_ollama_url_is_rejected_without_network_probe(tmp_path: Path) -> None:
    def unexpected_ollama_probe(
        _url: str,
        _model: str,
        _timeout: float,
    ) -> OllamaProbeResult:
        raise AssertionError("remote Ollama URL must not be probed")

    report = run_doctor(
        _configured(tmp_path, ollama_url="http://192.0.2.10:11434"),
        DoctorProbes(
            guardian=lambda _path: _guardian(),
            lima=lambda _path: _lima(),
            ollama=unexpected_ollama_probe,
        ),
    )

    assert report["ollama_configured"] is False
    assert report["ollama_reachable"] is False
    assert report["ollama_model_available"] is False
    assert report["local_integration_ready"] is False
    assert "ollama_url_requires_loopback_host" in report["blockers"]


def test_missing_ollama_model_is_controlled_unavailable(tmp_path: Path) -> None:
    report = run_doctor(
        _configured(tmp_path),
        DoctorProbes(
            guardian=lambda _path: _guardian(),
            lima=lambda _path: _lima(),
            ollama=lambda _url, _model, _timeout: OllamaProbeResult(True, False),
        ),
    )

    assert report["ollama_reachable"] is True
    assert report["ollama_model_available"] is False
    assert report["local_integration_ready"] is False
    assert "ollama_model_unavailable" in report["blockers"]


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        ("http://127.0.0.1:11434", "http://127.0.0.1:11434"),
        ("http://localhost:11434/", "http://localhost:11434"),
    ),
)
def test_normalize_ollama_url_accepts_loopback(value: str, expected: str) -> None:
    assert normalize_ollama_url(value) == expected


@pytest.mark.parametrize(
    "value",
    (
        "https://127.0.0.1:11434",
        "http://example.com:11434",
        "http://[::1]:11434",
        "http://0.0.0.0:11434",
        "http://192.168.1.20:11434",
        "http://user:password@127.0.0.1:11434",
        "http://127.0.0.1:11434/api/generate",
    ),
)
def test_normalize_ollama_url_rejects_unapproved_scope(value: str) -> None:
    with pytest.raises(ValueError):
        normalize_ollama_url(value)


def test_contract_report_is_generated_from_probe_results() -> None:
    report = build_contract_report(_guardian(compatible=False), _lima())

    assert report["schema_version"] == "arc-integration-contract-report-v0.7"
    assert report["guardian"]["decision_id_field"] is None
    assert report["lima"]["decision_id_field"] == "decision_id"
    assert report["invariants"]["arc_direct_model_execution_allowed"] is False
    assert report["editable_install_audit"]["guardian_suite"]["result"] == "pass"


def test_cli_reports_installed_lima_without_ollama_probe(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    for name in (
        "ARC_GUARDIAN_PATH",
        "ARC_LIMA_PATH",
        "ARC_OLLAMA_URL",
        "ARC_OLLAMA_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)

    assert main(["doctor"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["local_integration_ready"] is False
    assert payload["guardian_available"] is False
    assert payload["lima_available"] is True
    assert payload["lima_public_import_path"] == "lima.harness"
    assert payload["decision_id_propagation_supported"] is True
    assert payload["fake_executor_smoke_ready"] is True
    assert payload["ollama_integration_ready"] is False
