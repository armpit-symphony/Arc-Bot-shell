"""Static security and wiring checks for the Arc operator IDE UI."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "ui" / "arc_operator_ide.html"


class ArcOperatorIDEUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = UI.read_text(encoding="utf-8")

    def test_has_training_working_queue_and_document_surfaces(self):
        for element_id in (
            "training-mode",
            "working-mode",
            "task-list",
            "next-task",
            "approval-list",
            "directory-path",
            "run-list",
            "document-list",
            "document-list-count",
            "gap-list",
            "ladder-json",
            "document-output",
            "next-page",
            "training-goal",
            "draft-training",
            "local-model-label",
            "registration-practice-panel",
            "registration-scenario",
            "registration-status",
            "registration-score",
            "registration-template",
            "registration-review-status",
            "registration-review-approve",
            "registration-review-reject",
            "registration-profile",
            "registration-form-fields",
            "registration-issues",
            "run-registration",
            "run-registration-suite",
            "registration-submit",
        ):
            self.assertIn(f'id="{element_id}"', self.source)

    def test_wires_every_operator_ide_endpoint(self):
        for endpoint in (
            "/api/state",
            "/api/mode",
            "/api/training/instruction",
            "/api/training/draft",
            "/api/training/registration/catalog",
            "/api/training/registration/run",
            "/api/training/registration/run-suite",
            "/api/training/registration/review",
            "/api/training/resolve-gap",
            "/api/work/list",
            "/api/training/escalation-ladder",
            "/api/work/read",
            "/api/work/content-page",
            "/api/work/approval",
            "/api/worker/status",
        ):
            self.assertIn(endpoint, self.source)

    def test_browser_has_no_product_state_store_or_unsafe_html_sink(self):
        for forbidden in (
            "localStorage",
            "sessionStorage",
            "IndexedDB",
            "document.cookie",
            "innerHTML",
        ):
            self.assertNotIn(forbidden, self.source)
        self.assertIn("textContent", self.source)

    def test_ui_restates_guardian_and_non_execution_boundaries(self):
        self.assertIn("Instructions never override Guardian", self.source)
        self.assertIn("no execution authority issued", self.source)
        self.assertIn("Hidden entries, symlinks, content, timestamps", self.source)
        self.assertIn("No mutation, send, connector", self.source)
        self.assertIn("Synthetic lab data only", self.source)
        self.assertIn("it has not been saved", self.source)
        self.assertIn("browser automation, external submission", self.source)
        self.assertIn("Approve localhost mock", self.source)
        self.assertIn("External submit blocked", self.source)
        self.assertIn('id="registration-submit" disabled', self.source)
        self.assertIn("nothing was sent", self.source)
        self.assertIn("external_side_effects", self.source)


if __name__ == "__main__":
    unittest.main()
