# USA - Turn-based Political Simulation (Backend Prototype)

This is a Python-based, turn-based political simulation of the United States. It focuses on backend mechanics: political structure, elections, policies/legislation, economy, public opinion, and events.

## Features

- **Granular Elections**: District-based House elections, Senate staggering, and state-level voter modeling.
- **AI Decision-Making**: States and parties propose policies, react to events, and campaign based on public opinion, budgets, and events.
- **Serialization**: Save and load simulation state to/from JSON for deterministic continuation.
- **Turn-Based System**: Advance the simulation month by month, handling elections, AI decisions, and events.

## Updated Quick Start

Run the simulation demo (includes save/load):

```powershell
python examples/simulation_demo.py
```

## Recent Updates

- Added save/load functionality for the simulation state.
- Enhanced AI logic for state and party decision-making.
- Integrated granular election mechanics and voter modeling.
- Created a sample script demonstrating election simulation, policy passing, and AI decision-making.

## Notes
- This is a backend prototype; no UI yet.
- Economics and political mechanics are simplified placeholders with realistic levers to extend later.
