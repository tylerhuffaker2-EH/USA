import json
import unittest

from usa.models import PartyID, UnitedStates


class SmokeTest(unittest.TestCase):
    def test_sim_runs_and_changes_time(self):
        us = UnitedStates.new_default(seed=1)
        y0, m0 = us.year, us.month
        us.advance_turn(3)
        self.assertTrue((us.year, us.month) != (y0, m0))

    def test_election_and_policy_paths(self):
        us = UnitedStates.new_default(seed=2)
        us.month = 10
        us.advance_turn(2)  # force November elections
        self.assertIn(us.congress.house_control, (PartyID.DEMOCRAT, PartyID.REPUBLICAN))

    def test_save_load_roundtrip(self):
        us = UnitedStates.new_default(seed=99)
        us.advance_turn(5)
        data = us.to_dict()
        # simulate JSON persistence
        blob = json.dumps(data)
        data2 = json.loads(blob)
        us2 = UnitedStates.from_dict(data2)
        # core checks
        self.assertEqual(us2.year, us.year)
        self.assertEqual(us2.month, us.month)
        self.assertAlmostEqual(us2.growth, us.growth, places=6)
        self.assertEqual(set(us2.states.keys()), set(us.states.keys()))

    def test_deterministic_continuation(self):
        # With saved rng state, continuing should match a control run
        us_a = UnitedStates.new_default(seed=1234)
        us_a.advance_turn(7)
        snap_a = json.loads(json.dumps(us_a.to_dict()))
        # Clone by from_dict
        us_b = UnitedStates.from_dict(snap_a)
        # Now advance both by same steps and compare a few key metrics
        us_a.advance_turn(3)
        us_b.advance_turn(3)
        self.assertEqual(us_a.year, us_b.year)
        self.assertEqual(us_a.month, us_b.month)
        self.assertAlmostEqual(us_a.growth, us_b.growth, places=6)
        self.assertAlmostEqual(us_a.unemployment, us_b.unemployment, places=6)
        self.assertAlmostEqual(us_a.inflation, us_b.inflation, places=6)


if __name__ == "__main__":
    unittest.main()
