# USA - Turn-based Political Simulation (Backend Prototype)

This is a Python-based, turn-based political simulation of the United States. It focuses on backend mechanics: political structure, elections, policies/legislation, economy, public opinion, and events.

Highlights:
- Modular classes: UnitedStates, State, PoliticalParty, Election, Policy, PublicOpinion, EventManager.
- Turn-based month/quarter time step.
- AI stubs for parties/states to make decisions.
- Deterministic RNG seed option for reproducibility.

## Quick start

Requirements: Python 3.10+

Run a short demo (12 months):

```powershell
python -m usa.main --months 12 --seed 42
```

Run unit tests:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

Examples:

```powershell
# Snapshot demo
python -m examples.snapshot_demo

# Manual interactions demo (advancing turns, policy, event, election)
python -m examples.manual_demo
```

## Notes
- This is a backend prototype; no UI yet.
- Economics and political mechanics are simplified placeholders with realistic levers to extend later.
- Save/load can be added by serializing `UnitedStates` state to JSON.
