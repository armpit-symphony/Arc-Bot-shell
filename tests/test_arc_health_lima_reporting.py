"""Proofs that the health report tells the truth about LIMA.

Found during the first real Windows operator install. Three operator commands
disagreed about the same fact on the same installation, seconds apart:

    arc.ps1 status   lima_ready: true
    arc.ps1 doctor   lima_available: true, lima_installed_available: true
    arc.ps1 health   lima_ready: false, "LIMA runtime is not installed"

The health report was wrong, for two independent reasons, and both are the
kind of defect that sends an operator to the wrong component.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import unittest
from unittest import mock

from arc_bot_shell import health as health_module


def _doctor(**overrides: Any) -> dict[str, Any]:
    """A doctor report shaped like a healthy non-executing v0.11 install."""

    report: dict[str, Any] = {
        "lima_available": True,
        "lima_installed_available": True,
        "guardian_to_lima_contract_compatible": True,
        "fake_executor_smoke_ready": False,
        # Retired by design in the non-executing control plane.
        "lima_loopback_ollama_supported": False,
        "real_guardian_ready": True,
        "full_local_integration_ready": False,
        "ollama_reachable": False,
        "ollama_model_available": False,
        "blockers": ["lima_loopback_ollama_execution_disabled"],
    }
    report.update(overrides)
    return report


def _report(tmp: Path, **overrides: Any) -> dict[str, Any]:
    with mock.patch.object(health_module, "run_doctor", return_value=_doctor(**overrides)):
        return health_module.build_health_report(tmp)


class LimaReadyTests(unittest.TestCase):
    """lima_ready must not depend on a surface the product retired."""

    def setUp(self) -> None:
        import tempfile

        directory = tempfile.TemporaryDirectory(prefix="arc-health-")
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def test_lima_is_ready_on_a_non_executing_install(self) -> None:
        """The exact shape of a real v0.11 install: no loopback Ollama."""

        report = _report(self.root)
        self.assertTrue(report["lima_ready"])

    def test_lima_ready_agrees_with_the_operator_cli(self) -> None:
        """status derives lima_ready from the same doctor field; so must health."""

        for compatible in (True, False):
            with self.subTest(compatible=compatible):
                report = _report(
                    self.root, guardian_to_lima_contract_compatible=compatible
                )
                self.assertEqual(compatible, report["lima_ready"])

    def test_retiring_loopback_ollama_does_not_make_lima_unready(self) -> None:
        """The regression this fixes: a retired surface forcing lima_ready false."""

        report = _report(self.root, lima_loopback_ollama_supported=False)
        self.assertTrue(report["lima_ready"])


class LimaStatusTests(unittest.TestCase):
    """The lima block must describe the runtime Arc actually uses."""

    def setUp(self) -> None:
        import tempfile

        directory = tempfile.TemporaryDirectory(prefix="arc-health-")
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def test_a_packaged_install_is_reported_as_configured(self) -> None:
        """No lima.adapters, no source checkout - still a working install.

        This is every real install: the published lima-runtime wheel ships
        contracts, governed_kernel, release and runtime, and no adapters.
        """

        report = _report(self.root)
        self.assertTrue(report["lima"]["configured"])
        self.assertEqual("lima.runtime", report["lima"]["runtime"])

    def test_an_absent_runtime_is_still_reported_as_absent(self) -> None:
        """The fix must not make the report unconditionally cheerful."""

        report = _report(self.root, lima_available=False)
        self.assertFalse(report["lima"]["configured"])

    def test_the_legacy_port_is_reported_separately_and_named(self) -> None:
        """Its unavailability is a fact worth keeping, not a verdict on LIMA."""

        legacy = _report(self.root)["lima"]["legacy_local_import"]
        self.assertFalse(legacy["available"])
        self.assertIn("lima.adapters", legacy["requires"])

    def test_the_legacy_port_never_speaks_for_lima_overall(self) -> None:
        """The precise wording that caused the confusion, kept out of the top."""

        lima = _report(self.root)["lima"]
        self.assertNotIn("reason", lima)
        self.assertNotIn("LIMA runtime is not installed", str(lima.get("configured")))

    def test_fake_executor_readiness_does_not_come_from_finding_a_checkout(
        self,
    ) -> None:
        """Locating a checkout says nothing about executor readiness."""

        ready = _report(self.root, fake_executor_smoke_ready=True)
        self.assertTrue(ready["lima_fake_executor_smoke_ready"])

        not_ready = _report(self.root, fake_executor_smoke_ready=False)
        self.assertFalse(not_ready["lima_fake_executor_smoke_ready"])


if __name__ == "__main__":
    unittest.main()
