from __future__ import annotations

import unittest
from streamlit.testing.v1 import AppTest
from engines.workspace_engine import workspace_names, subviews_for


class TestAllWorkspaces(unittest.TestCase):
    def test_all_16_workspaces_render_without_exception(self):
        names = workspace_names()
        self.assertEqual(len(names), 16)

        for name in names:
            with self.subTest(workspace=name):
                at = AppTest.from_file("app.py", default_timeout=15)
                at.session_state["ifit_v082_module"] = name
                at.session_state["ifit_v082_subview"] = subviews_for(name)[0]
                at.session_state["ifit_data_mode"] = "SIMULATION"
                at.run()

                self.assertFalse(
                    at.exception,
                    f"Workspace '{name}' threw exception: {[e.value for e in at.exception]}",
                )


if __name__ == "__main__":
    unittest.main()
