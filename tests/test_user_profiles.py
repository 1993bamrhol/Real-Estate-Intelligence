from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from real_estate_intel.user_profiles import (
    DEFAULT_USER_PROFILE,
    USER_PROFILES,
    get_user_profile,
    user_profile_key_from_label,
)


class UserProfileTests(unittest.TestCase):
    def test_all_product_roles_are_available(self) -> None:
        self.assertEqual(set(USER_PROFILES), {"investor", "broker", "developer", "researcher"})
        for key, profile in USER_PROFILES.items():
            self.assertEqual(profile.key, key)
            self.assertEqual(len(profile.tab_labels), 4)
            self.assertEqual(len(set(profile.tab_labels)), 4)
            self.assertGreaterEqual(len(profile.focus_metrics), 3)

    def test_unknown_profile_falls_back_to_investor(self) -> None:
        self.assertEqual(get_user_profile("missing").key, DEFAULT_USER_PROFILE)

    def test_label_maps_back_to_profile_key(self) -> None:
        for key, profile in USER_PROFILES.items():
            self.assertEqual(user_profile_key_from_label(profile.label), key)


if __name__ == "__main__":
    unittest.main()
