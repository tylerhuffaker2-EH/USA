"""
Demonstration of the configurable event and policy system.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from usa.models import UnitedStates
from usa.config import ConfigLoader


def main():
    """Demonstrate the configurable event and policy system."""
    print("=== USA Simulation - Configurable Events & Policies Demo ===\n")
    
    # Load configuration
    print("Loading configuration...")
    config_loader = ConfigLoader()
    
    print(f"Loaded {len(config_loader.get_all_events())} events:")
    for event in config_loader.get_all_events():
        print(f"  - {event.name}: {event.description}")
    
    print(f"\nLoaded {len(config_loader.get_all_policies())} policies:")
    federal_policies = config_loader.get_policies_by_level("federal")
    state_policies = config_loader.get_policies_by_level("state")
    
    print(f"  Federal policies ({len(federal_policies)}):")
    for policy in federal_policies:
        print(f"    - {policy.title}: ${policy.cost}B")
    
    print(f"  State policies ({len(state_policies)}):")
    for policy in state_policies:
        print(f"    - {policy.title}: ${policy.cost}B")
    
    print("\n" + "="*60)
    print("Starting simulation with configurable system...")
    print("="*60)
    
    # Initialize simulation
    usa = UnitedStates.new_default(seed=42)
    
    # Run simulation for 24 months to see events and policies in action
    for month in range(24):
        usa.advance_turn(1)
        
        # Display significant events
        if usa.log and month > 0:
            recent_log = usa.log[-3:]  # Last 3 entries
            for entry in recent_log:
                if any(keyword in entry.lower() for keyword in ["event", "policy", "election", "scandal", "hurricane"]):
                    print(f"Month {month+1}: {entry}")
    
    print("\n" + "="*60)
    print("Simulation Summary")
    print("="*60)
    
    # Show final state
    snapshot = usa.snapshot(last_logs=10)
    print(f"Final Year: {snapshot['time']['year']}")
    print(f"Economic Growth: {snapshot['macro']['growth']:.2%}")
    print(f"Unemployment: {snapshot['macro']['unemployment']:.1f}%")
    print(f"Inflation: {snapshot['macro']['inflation']:.1f}%")
    print(f"Presidential Approval: {snapshot['federal']['opinion']['president']:.1f}%")
    print(f"Congressional Approval: {snapshot['federal']['opinion']['congress']:.1f}%")
    
    print("\nRecent Events and Policies:")
    for entry in snapshot['log_tail'][-10:]:
        print(f"  {entry}")
    
    print("\nDemonstration complete!")
    print("\nKey Features Demonstrated:")
    print("✓ Events loaded from JSON configuration")
    print("✓ Policies loaded from JSON configuration") 
    print("✓ Conditional event triggers based on game state")
    print("✓ Chained events with delays")
    print("✓ Policy proposals triggered by events")
    print("✓ State-specific effects from events")
    print("✓ AI using configurable policies")


if __name__ == "__main__":
    main()
