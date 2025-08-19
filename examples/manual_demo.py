from usa.models import PartyID, Policy, UnitedStates

if __name__ == "__main__":
    us = UnitedStates.new_default(seed=123)
    print("Start:", us.year, us.month)

    # 1) Advance a few months
    us.advance_turn(3)
    print("After 3 months:", us.year, us.month)

    # 2) Manually attempt to pass a policy
    policy = Policy(
        title="Healthcare Expansion",
        description="Expand access via subsidies",
        cost=150.0,
        effect_growth=0.002,
        effect_unemployment=-0.1,
        effect_inflation=0.05,
        popularity=58.0,
        sponsor_party=us.president.party,
    )
    passed = us.attempt_pass_policy(policy)
    print("Policy passed?", passed)

    # 3) Trigger an event explicitly
    ev = us.trigger_event()
    print("Triggered event:", ev.key if ev else None)

    # 4) Force an election by moving to November and advancing one month
    us.month = 11
    us.advance_turn(1)
    print(
        "Post-election controls:",
        us.president.party.value,
        us.congress.house_control.value,
        us.congress.senate_control.value,
    )

    # Snapshot tail log
    print("Log tail:")
    for line in us.snapshot()["log_tail"][-5:]:
        print(" -", line)
