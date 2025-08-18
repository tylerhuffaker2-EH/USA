from usa.models import UnitedStates

if __name__ == "__main__":
    us = UnitedStates.new_default(seed=7)
    us.advance_turn(2)
    ss = us.snapshot()
    print(ss["time"], ss["federal"]["president_party"], len(ss["log_tail"]))
