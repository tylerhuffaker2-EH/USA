from __future__ import annotations

import argparse
from typing import Optional
from .models import UnitedStates


def run(months: int, seed: Optional[int]) -> None:
    us = UnitedStates.new_default(seed=seed)
    us.advance_turn(months)
    # Print a compact summary and last 10 log lines
    print(f"Simulated through {us.year}-{us.month:02d}")
    print(f"President: {us.president.party.value}; House: {us.congress.house_control.value}; Senate: {us.congress.senate_control.value}")
    print(f"Growth: {us.growth:.3%}; Unemp: {us.unemployment:.1f}%; Inflation: {us.inflation:.1f}%")
    print(f"Approval - President: {us.opinion.approval_president:.1f}, Congress: {us.opinion.approval_congress:.1f}")
    if us.log:
        print("Recent log:")
        for line in us.log[-10:]:
            print(" -", line)


def main() -> None:
    parser = argparse.ArgumentParser(description="USA political simulation demo")
    parser.add_argument("--months", type=int, default=12, help="Number of months to simulate")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    args = parser.parse_args()
    run(args.months, args.seed)


if __name__ == "__main__":
    main()
