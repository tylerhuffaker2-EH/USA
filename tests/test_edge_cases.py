import random
import unittest

from usa.models import District, Event, EventManager, PartyID, Policy, UnitedStates


class EdgeCaseTest(unittest.TestCase):
    def test_election_tie_resolves_to_democrat(self):
        # Setup a minimal US with one state and two districts
        us = UnitedStates.new_default(seed=0)
        st = us.states.pop("California")
        us.states = {"California": st}
        # Override districts to two empty districts
        st.house_districts = [
            District(id="d1", cohorts=[], swing=0.0, turnout_bias=0.0),
            District(id="d2", cohorts=[], swing=0.0, turnout_bias=0.0),
        ]
        # Override probability calculation to neutral 0.5 for both districts
        us._district_dem_probability = lambda state, dist: 0.5

        # Custom RNG that alternates to force one R and one D win
        class DummyRNG:
            def __init__(self):
                self.values = [0.6, 0.4]
                self.idx = 0

            def random(self):
                v = self.values[self.idx]
                self.idx = (self.idx + 1) % len(self.values)
                return v

        us.rng = DummyRNG()
        # Force election month/year
        us.year = 2026
        us.month = 11
        # Run elections
        us.maybe_run_elections()
        # In a tie, Democrats should win (>=)
        self.assertEqual(us.congress.house_control, PartyID.DEMOCRAT)

    def test_policy_conflict_effects_accumulate(self):
        # Setup US and override RNG to always pass policies
        us = UnitedStates.new_default(seed=1)
        us.rng.random = lambda: 0.0  # always succeed
        initial_growth = us.growth
        initial_unemployment = us.unemployment
        # Define two policies with effects
        p1 = Policy(
            title="P1",
            description="Test policy 1",
            cost=0.0,
            effect_growth=0.01,
            effect_unemployment=-0.1,
            effect_inflation=0.0,
            popularity=100.0,
            sponsor_party=us.president.party,
        )
        p2 = Policy(
            title="P2",
            description="Test policy 2",
            cost=0.0,
            effect_growth=0.02,
            effect_unemployment=-0.2,
            effect_inflation=0.0,
            popularity=100.0,
            sponsor_party=us.president.party,
        )
        # Apply policies sequentially
        us.attempt_pass_policy(p1)
        us.attempt_pass_policy(p2)
        # Effects should accumulate
        self.assertAlmostEqual(us.growth, initial_growth + 0.01 + 0.02, places=6)
        self.assertAlmostEqual(
            us.unemployment,
            max(2.5, min(20.0, initial_unemployment - 0.1 - 0.2)),
            places=6,
        )

    def test_chain_event_scheduling(self):
        # Setup EventManager and register a follow-up event
        rng = random.Random(0)
        em = EventManager(rng)
        # Register event x in catalog
        follow = Event(key="x", description="Follow-up")
        em.register(follow, weight=1.0)
        # Create a base event with a chain_event consequence
        base = Event(
            key="base",
            description="Base",
            consequences=[
                {
                    "type": "chain_event",
                    "event_key": "x",
                    "delay_months": 3,
                    "probability": 1.0,
                }
            ],
        )
        # Process consequences
        us = UnitedStates.new_default(seed=2)
        em.process_event_consequences(base, us)
        # The follow-up event should be scheduled with delay
        self.assertIn(("x", 3), em.pending_events)


if __name__ == "__main__":
    unittest.main()
