"""Static boundary checks for the Arc physical runtime harness UI."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "ui" / "arc_runtime_harness.html"


class RuntimeHarnessUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = UI.read_text(encoding="utf-8")

    def test_has_explicit_training_and_working_modes(self):
        self.assertIn('id="training-mode"', self.source)
        self.assertIn('id="working-mode"', self.source)
        self.assertIn('data-mode="training"', self.source)
        self.assertIn('id="training-workbench"', self.source)
        self.assertIn('id="working-workbench"', self.source)

    def test_uses_server_as_the_product_state_authority(self):
        for endpoint in (
            "/api/state",
            "/api/mode",
            "/api/training/instruction",
            "/api/work/read",
            "/api/worker/status",
        ):
            self.assertIn(endpoint, self.source)
        for forbidden in ("localStorage", "sessionStorage", "IndexedDB", "document.cookie"):
            self.assertNotIn(forbidden, self.source)

    def test_renders_unavailable_capability_classes(self):
        self.assertIn('id="blocked-list"', self.source)
        self.assertIn("Governed read only", self.source)
        self.assertIn("cannot turn a forbidden denial into permission", self.source)

    def test_dynamic_content_uses_text_content_not_inner_html(self):
        self.assertIn("textContent", self.source)
        self.assertNotIn("innerHTML", self.source)


if __name__ == "__main__":
    unittest.main()
