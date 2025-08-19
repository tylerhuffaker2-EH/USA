import argparse

from usa.models import UnitedStates


def main():
    parser = argparse.ArgumentParser(description="USA Simulation CLI")
    parser.add_argument(
        "--seed", type=int, default=0, help="Random seed for simulation"
    )
    parser.add_argument(
        "--turns", type=int, default=1, help="Number of turns to advance"
    )
    parser.add_argument(
        "--snapshot", action="store_true", help="Print a snapshot of the current state"
    )

    args = parser.parse_args()

    # Initialize simulation
    us = UnitedStates.new_default(seed=args.seed)

    # Advance turns
    us.advance_turn(args.turns)

    # Print snapshot if requested
    if args.snapshot:
        snapshot = us.snapshot()
        print("\n=== Simulation Snapshot ===")
        print(snapshot)

    print("\nSimulation completed.")


if __name__ == "__main__":
    main()
