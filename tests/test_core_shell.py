from __future__ import annotations

import re
import sys
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from real_estate_intel.ui.contracts import ROUTE_IDS, ROUTE_LABELS_AR


class CoreShellFoundationTests(unittest.TestCase):
    def test_cairo_is_local_and_streamlit_static_serving_is_enabled(self) -> None:
        config = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
        font_path = ROOT / "static" / "fonts" / "Cairo-Variable.ttf"
        license_path = ROOT / "static" / "fonts" / "Cairo-OFL.txt"

        self.assertTrue(config["server"]["enableStaticServing"])
        self.assertEqual(config["theme"]["font"], "Cairo")
        self.assertEqual(config["theme"]["fontFaces"][0]["family"], "Cairo")
        self.assertEqual(config["theme"]["fontFaces"][0]["url"], "app/static/fonts/Cairo-Variable.ttf")
        self.assertGreater(font_path.stat().st_size, 100_000)
        self.assertIn("SIL OPEN FONT LICENSE Version 1.1", license_path.read_text(encoding="utf-8"))

    def test_shell_css_has_semantic_tokens_stable_selectors_and_three_weights(self) -> None:
        app_source = (ROOT / "app.py").read_text(encoding="utf-8")
        required_tokens = {
            "surface-canvas",
            "surface-default",
            "surface-subtle",
            "text-primary",
            "text-secondary",
            "border-default",
            "border-focus",
            "action-primary",
            "action-primary-hover",
            "status-success",
            "status-warning",
            "status-error",
        }

        for token in required_tokens:
            self.assertIn(f"--{token}:", app_source)
        self.assertNotIn('[class*="css"]', app_source)
        self.assertIn('[data-testid="stAppViewContainer"]', app_source)
        self.assertIn(":focus-visible", app_source)
        self.assertEqual(
            set(re.findall(r"--font-weight-(?:regular|semibold|bold):\s*(\d+)", app_source)),
            {"400", "600", "700"},
        )

    def test_streamlit_shell_renders_and_navigation_persists(self) -> None:
        from streamlit.testing.v1 import AppTest

        app_test = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
        app_test.run()
        self.assertFalse(app_test.exception)

        navigation = next(item for item in app_test.radio if item.label == "وجهات قرينة")
        self.assertEqual(tuple(navigation.options), tuple(ROUTE_LABELS_AR[route_id] for route_id in ROUTE_IDS))
        self.assertEqual(navigation.value, "home")

        navigation.set_value("comparison")
        app_test.run(timeout=60)
        self.assertFalse(app_test.exception)
        self.assertEqual(app_test.session_state["core.route"], "comparison")
        self.assertTrue(any("المسار الحالي" in item.value for item in app_test.markdown))


if __name__ == "__main__":
    unittest.main()
