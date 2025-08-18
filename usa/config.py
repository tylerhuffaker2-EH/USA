"""Configuration system for events and policies."""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum, auto


class TriggerType(Enum):
    RANDOM = auto()
    CONDITIONAL = auto()
    CHAINED = auto()


class ConsequenceType(Enum):
    POLICY_PROPOSAL = auto()
    CHAIN_EVENT = auto()
    PARTY_APPROVAL = auto()
    APPROVAL_BOOST = auto()


@dataclass
class EventConfig:
    """Configuration for an event."""
    key: str
    name: str
    description: str
    weight: float
    triggers: Dict[str, Any]
    effects: Dict[str, Any]
    consequences: List[Dict[str, Any]]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EventConfig":
        return cls(
            key=data["key"],
            name=data["name"],
            description=data["description"],
            weight=data.get("weight", 1.0),
            triggers=data.get("triggers", {}),
            effects=data.get("effects", {}),
            consequences=data.get("consequences", [])
        )


@dataclass
class PolicyConfig:
    """Configuration for a policy."""
    key: str
    title: str
    description: str
    cost: float
    effects: Dict[str, Any]
    popularity: float
    level: str  # "federal" or "state"
    requirements: Dict[str, Any]
    consequences: List[Dict[str, Any]]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolicyConfig":
        return cls(
            key=data["key"],
            title=data["title"],
            description=data["description"],
            cost=data.get("cost", 0.0),
            effects=data.get("effects", {}),
            popularity=data.get("popularity", 50.0),
            level=data.get("level", "federal"),
            requirements=data.get("requirements", {}),
            consequences=data.get("consequences", [])
        )


class ConfigLoader:
    """Loads and manages event and policy configurations."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.events: Dict[str, EventConfig] = {}
        self.policies: Dict[str, PolicyConfig] = {}
        self._load_configurations()
    
    def _load_configurations(self) -> None:
        """Load all configuration files."""
        self._load_events()
        self._load_policies()
    
    def _load_events(self) -> None:
        """Load event configurations from JSON."""
        events_path = os.path.join(self.config_dir, "events.json")
        if os.path.exists(events_path):
            with open(events_path, 'r') as f:
                data = json.load(f)
                for event_data in data.get("events", []):
                    event_config = EventConfig.from_dict(event_data)
                    self.events[event_config.key] = event_config
    
    def _load_policies(self) -> None:
        """Load policy configurations from JSON."""
        policies_path = os.path.join(self.config_dir, "policies.json")
        if os.path.exists(policies_path):
            with open(policies_path, 'r') as f:
                data = json.load(f)
                for policy_data in data.get("policies", []):
                    policy_config = PolicyConfig.from_dict(policy_data)
                    self.policies[policy_config.key] = policy_config
    
    def get_event(self, key: str) -> Optional[EventConfig]:
        """Get event configuration by key."""
        return self.events.get(key)
    
    def get_policy(self, key: str) -> Optional[PolicyConfig]:
        """Get policy configuration by key."""
        return self.policies.get(key)
    
    def get_all_events(self) -> List[EventConfig]:
        """Get all event configurations."""
        return list(self.events.values())
    
    def get_all_policies(self) -> List[PolicyConfig]:
        """Get all policy configurations."""
        return list(self.policies.values())
    
    def get_policies_by_level(self, level: str) -> List[PolicyConfig]:
        """Get policies by level (federal/state)."""
        return [p for p in self.policies.values() if p.level == level]
