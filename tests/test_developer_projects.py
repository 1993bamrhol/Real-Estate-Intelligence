from __future__ import annotations

import sys
import unittest
from pathlib import Path

from sqlalchemy import create_engine

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from real_estate_intel.developer_ai import DevelopmentAssumptions, analyze_development, stress_test_development
from real_estate_intel.developer_projects import (
    delete_developer_project,
    initialize_developer_project_store,
    load_developer_projects,
    project_comparison_row,
    save_developer_project,
    workspace_fingerprint,
)


class DeveloperProjectStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        initialize_developer_project_store(self.engine)
        self.assumptions = DevelopmentAssumptions(
            land_area_sqm=2_000,
            land_cost=4_000_000,
            floor_area_ratio=2,
            saleable_efficiency_pct=80,
            average_unit_area_sqm=100,
            construction_cost_per_sqm=2_000,
            sale_price_per_sqm=6_000,
            annual_rent_per_unit=45_000,
        )
        self.result = analyze_development(self.assumptions)
        self.stress = stress_test_development(self.assumptions)

    def test_workspace_code_is_hashed_and_validated(self) -> None:
        fingerprint = workspace_fingerprint("workspace-123")
        self.assertEqual(len(fingerprint), 64)
        self.assertNotIn("workspace-123", fingerprint)
        with self.assertRaises(ValueError):
            workspace_fingerprint("short")

    def test_save_load_update_and_delete_project(self) -> None:
        first_id = save_developer_project(
            self.engine,
            workspace_code="workspace-123",
            project_name="مشروع النخيل",
            property_type="شقة",
            assumptions=self.assumptions,
            result=self.result,
            stress=self.stress,
        )
        second_id = save_developer_project(
            self.engine,
            workspace_code="workspace-123",
            project_name="مشروع النخيل",
            property_type="شقة",
            assumptions=self.assumptions,
            result={**self.result, "profit": 9_000_000},
            stress=self.stress,
        )
        self.assertEqual(first_id, second_id)
        projects = load_developer_projects(self.engine, workspace_code="workspace-123")
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["result"]["profit"], 9_000_000)
        comparison = project_comparison_row(projects[0])
        self.assertEqual(comparison["project"], "مشروع النخيل")
        self.assertTrue(
            delete_developer_project(
                self.engine,
                workspace_code="workspace-123",
                project_name="مشروع النخيل",
            )
        )
        self.assertEqual(load_developer_projects(self.engine, workspace_code="workspace-123"), [])

    def test_workspaces_are_isolated(self) -> None:
        save_developer_project(
            self.engine,
            workspace_code="workspace-123",
            project_name="مشروع خاص",
            property_type="شقة",
            assumptions=self.assumptions,
            result=self.result,
            stress=self.stress,
        )
        self.assertEqual(load_developer_projects(self.engine, workspace_code="workspace-999"), [])


if __name__ == "__main__":
    unittest.main()
