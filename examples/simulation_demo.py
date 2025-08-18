import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from usa.models import UnitedStates, Policy, FederalBudget, PoliticalParty, PartyID, Congress, President, PublicOpinion
import random

# Initialize the simulation
rng = random.Random(7)  # Seed for reproducibility
usa = UnitedStates(
    year=2025,
    month=8,
    president=None,  # Replace with actual President object
    congress=None,   # Replace with actual Congress object
    court=None,      # Replace with actual SupremeCourt object
    parties={},      # Replace with actual parties
    states={},       # Replace with actual states
    budget=None,     # Replace with actual FederalBudget object
    opinion=None,    # Replace with actual PublicOpinion object
    event_manager=None,  # Replace with actual EventManager object
    rng=rng,
)

# Mock FederalBudget object
mock_budget = FederalBudget(spending=4000.0, revenue=3500.0)
usa.budget = mock_budget

# Mock PoliticalParty objects
mock_parties = {
    PartyID.DEMOCRAT: PoliticalParty(name=PartyID.DEMOCRAT, national_approval=50.0),
    PartyID.REPUBLICAN: PoliticalParty(name=PartyID.REPUBLICAN, national_approval=50.0),
}
usa.parties = mock_parties

# Mock Congress object
mock_congress = Congress(house_control=PartyID.DEMOCRAT, senate_control=PartyID.REPUBLICAN)
usa.congress = mock_congress

# Mock President object
mock_president = President(name="John Doe", party=PartyID.DEMOCRAT)
usa.president = mock_president

# Mock PublicOpinion object
mock_opinion = PublicOpinion(approval_president=50.0, approval_congress=30.0)
usa.opinion = mock_opinion

# Simulate 12 months
for _ in range(12):
    usa.advance_turn()

# Example: Propose and pass a policy
policy = Policy(
    title="Green Energy Initiative",
    description="Invest in renewable energy sources.",
    cost=500.0,
    effect_growth=0.02,
    effect_unemployment=-0.5,
    effect_inflation=0.1,
    popularity=70.0,
    sponsor_party=None,  # Replace with actual PartyID
)
if usa.attempt_pass_policy(policy):
    print(f"Policy passed: {policy.title}")
else:
    print(f"Policy failed: {policy.title}")

# Example: Log events
for log_entry in usa.log:
    print(log_entry)
