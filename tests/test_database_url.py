from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from real_estate_intel.data_engine import normalize_database_url, pg_warehouse_status


class DatabaseUrlTests(unittest.TestCase):
    def test_accepts_raw_postgres_url(self) -> None:
        value = "postgresql://user:pass@db.example.test:5432/postgres"
        self.assertEqual(normalize_database_url(value), value)

    def test_accepts_quoted_toml_assignment(self) -> None:
        value = 'DATABASE_URL = "postgres://user:pass@db.example.test:5432/postgres"'
        self.assertEqual(
            normalize_database_url(value),
            "postgresql://user:pass@db.example.test:5432/postgres",
        )

    def test_rejects_non_database_text(self) -> None:
        self.assertIsNone(normalize_database_url("not-a-database-url"))

    def test_invalid_status_url_does_not_crash_streamlit(self) -> None:
        status = pg_warehouse_status("not-a-database-url")
        self.assertFalse(status["ready"])


if __name__ == "__main__":
    unittest.main()
