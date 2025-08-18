from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple
import random
import copy


def _enum_value(e):
    return e.value if isinstance(e, Enum) else e


def _tupleify(obj):
    if isinstance(obj, list):
        return tuple(_tupleify(x) for x in obj)
    if isinstance(obj, dict):
        # Not expected for random state but keep generic
        return {k: _tupleify(v) for k, v in obj.items()}
    return obj


def _listify(obj):
    if isinstance(obj, tuple):
        return [_listify(x) for x in obj]
    if isinstance(obj, list):
        return [_listify(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _listify(v) for k, v in obj.items()}
    return obj


class Branch(Enum):
    EXECUTIVE = auto()
    LEGISLATIVE = auto()
    JUDICIAL = auto()


class Chamber(Enum):
    HOUSE = auto()
    SENATE = auto()


class PartyID(str, Enum):
    DEMOCRAT = "Democrat"
    REPUBLICAN = "Republican"
    INDEPENDENT = "Independent"


@dataclass
class PoliticalParty:
    name: PartyID
    national_approval: float = 50.0  # 0-100

    def adjust_approval(self, delta: float) -> None:
        """Adjust party national approval with bounds."""
        self.national_approval = max(0.0, min(100.0, self.national_approval + delta))

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name.value,
            "national_approval": self.national_approval,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "PoliticalParty":
        return cls(name=PartyID(data["name"]), national_approval=float(data["national_approval"]))


@dataclass
class Policy:
    title: str
    description: str
    cost: float = 0.0  # billions
    effect_growth: float = 0.0  # +/- GDP growth in percentage points
    effect_unemployment: float = 0.0  # +/- percentage points
    effect_inflation: float = 0.0  # +/- percentage points
    popularity: float = 0.0  # baseline public support 0-100
    sponsor_party: PartyID = PartyID.INDEPENDENT

    def to_dict(self) -> Dict[str, object]:
        return {
            "title": self.title,
            "description": self.description,
            "cost": self.cost,
            "effect_growth": self.effect_growth,
            "effect_unemployment": self.effect_unemployment,
            "effect_inflation": self.effect_inflation,
            "popularity": self.popularity,
            "sponsor_party": self.sponsor_party.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Policy":
        return cls(
            title=str(data["title"]),
            description=str(data["description"]),
            cost=float(data.get("cost", 0.0)),
            effect_growth=float(data.get("effect_growth", 0.0)),
            effect_unemployment=float(data.get("effect_unemployment", 0.0)),
            effect_inflation=float(data.get("effect_inflation", 0.0)),
            popularity=float(data.get("popularity", 0.0)),
            sponsor_party=PartyID(data.get("sponsor_party", PartyID.INDEPENDENT.value)),
        )


@dataclass
class PublicOpinion:
    approval_president: float = 50.0
    approval_congress: float = 30.0
    issue_support: Dict[str, float] = field(default_factory=dict)  # policy title -> support 0-100

    def update_issue(self, policy: Policy, delta: float) -> None:
        base = self.issue_support.get(policy.title, policy.popularity)
        self.issue_support[policy.title] = max(0.0, min(100.0, base + delta))

    def to_dict(self) -> Dict[str, object]:
        return {
            "approval_president": self.approval_president,
            "approval_congress": self.approval_congress,
            "issue_support": copy.deepcopy(self.issue_support),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "PublicOpinion":
        return cls(
            approval_president=float(data.get("approval_president", 50.0)),
            approval_congress=float(data.get("approval_congress", 30.0)),
            issue_support=dict(data.get("issue_support", {})),
        )


@dataclass
class LegislatureControl:
    house: PartyID
    senate: PartyID

    def to_dict(self) -> Dict[str, object]:
        return {"house": self.house.value, "senate": self.senate.value}

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "LegislatureControl":
        return cls(house=PartyID(data["house"]), senate=PartyID(data["senate"]))


@dataclass
class VoterCohort:
    name: str
    share: float  # 0..1 of electorate
    lean: PartyID
    turnout: float  # 0..1

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "share": self.share,
            "lean": self.lean.value,
            "turnout": self.turnout,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "VoterCohort":
        return cls(
            name=str(data["name"]),
            share=float(data["share"]),
            lean=PartyID(data["lean"]),
            turnout=float(data["turnout"]),
        )


@dataclass
class District:
    id: str
    cohorts: List[VoterCohort]
    incumbent: PartyID = PartyID.INDEPENDENT
    turnout_bias: float = 0.0  # -0.1..+0.1
    swing: float = 0.0  # -0.2..+0.2 partisan lean where + favors DEM

    def to_dict(self) -> Dict[str, object]:
        return {
            "id": self.id,
            "cohorts": [c.to_dict() for c in self.cohorts],
            "incumbent": self.incumbent.value,
            "turnout_bias": self.turnout_bias,
            "swing": self.swing,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "District":
        return cls(
            id=str(data["id"]),
            cohorts=[VoterCohort.from_dict(d) for d in data.get("cohorts", [])],
            incumbent=PartyID(data.get("incumbent", PartyID.INDEPENDENT.value)),
            turnout_bias=float(data.get("turnout_bias", 0.0)),
            swing=float(data.get("swing", 0.0)),
        )


@dataclass
class State:
    name: str
    population: int
    gdp: float  # in billions
    unemployment: float  # %
    inflation: float  # %
    governor_party: PartyID
    legislature: LegislatureControl
    approval_governor: float = 50.0
    approval_legislature: float = 40.0
    # simple public finance placeholders
    budget_revenue: float = 100.0  # billions
    budget_spending: float = 100.0  # billions
    tax_rate: float = 0.06  # effective state-level tax rate over GDP (approx.)
    gdp_sectors: Dict[str, float] = field(default_factory=lambda: {
        "services": 0.65,
        "industry": 0.27,
        "agriculture": 0.08,
    })
    voter_cohorts: List[VoterCohort] = field(default_factory=list)
    # Elections
    house_districts: List[District] = field(default_factory=list)
    senate_seats: List[PartyID] = field(default_factory=lambda: [PartyID.INDEPENDENT, PartyID.INDEPENDENT])
    senate_classes: List[int] = field(default_factory=lambda: [0, 3])  # which cycle years mod 6 when up

    # Simple state economy tick
    def advance_economy(self, growth: float, nat_inflation: float, rng: random.Random) -> None:
        gdp_growth = max(-0.1, min(0.1, growth + rng.uniform(-0.01, 0.01)))  # +/- 1pp noise
        self.gdp *= (1.0 + gdp_growth)
        # unemployment mean-reverts to 5-6% with noise and growth sensitivity
        target_u = 5.5 - 0.5 * growth
        self.unemployment += 0.2 * (target_u - self.unemployment) + rng.uniform(-0.1, 0.1)
        self.unemployment = max(2.5, min(20.0, self.unemployment))
        # inflation partially driven by national inflation
        self.inflation = max(0.0, min(20.0, 0.6 * nat_inflation + rng.uniform(-0.2, 0.2)))

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "population": self.population,
            "gdp": self.gdp,
            "unemployment": self.unemployment,
            "inflation": self.inflation,
            "governor_party": self.governor_party.value,
            "legislature": self.legislature.to_dict(),
            "approval_governor": self.approval_governor,
            "approval_legislature": self.approval_legislature,
            "budget_revenue": self.budget_revenue,
            "budget_spending": self.budget_spending,
            "tax_rate": self.tax_rate,
            "gdp_sectors": copy.deepcopy(self.gdp_sectors),
            "voter_cohorts": [c.to_dict() for c in self.voter_cohorts],
            "house_districts": [d.to_dict() for d in self.house_districts],
            "senate_seats": [p.value for p in self.senate_seats],
            "senate_classes": list(self.senate_classes),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "State":
        st = cls(
            name=str(data["name"]),
            population=int(data["population"]),
            gdp=float(data["gdp"]),
            unemployment=float(data["unemployment"]),
            inflation=float(data["inflation"]),
            governor_party=PartyID(data["governor_party"]),
            legislature=LegislatureControl.from_dict(data["legislature"]),
            approval_governor=float(data.get("approval_governor", 50.0)),
            approval_legislature=float(data.get("approval_legislature", 40.0)),
            budget_revenue=float(data.get("budget_revenue", 0.0)),
            budget_spending=float(data.get("budget_spending", 0.0)),
            tax_rate=float(data.get("tax_rate", 0.06)),
            gdp_sectors=dict(data.get("gdp_sectors", {})),
        )
        st.voter_cohorts = [VoterCohort.from_dict(d) for d in data.get("voter_cohorts", [])]
        st.house_districts = [District.from_dict(d) for d in data.get("house_districts", [])]
        st.senate_seats = [PartyID(p) for p in data.get("senate_seats", [PartyID.INDEPENDENT.value, PartyID.INDEPENDENT.value])]
        st.senate_classes = list(data.get("senate_classes", [0, 3]))
        return st


@dataclass
class FederalBudget:
    revenue: float  # billions
    spending: float  # billions
    tax_rate: float = 0.18  # effective federal tax rate over national GDP

    @property
    def deficit(self) -> float:
        return self.spending - self.revenue

    def to_dict(self) -> Dict[str, object]:
        return {"revenue": self.revenue, "spending": self.spending, "tax_rate": self.tax_rate}

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "FederalBudget":
        return cls(
            revenue=float(data["revenue"]),
            spending=float(data["spending"]),
            tax_rate=float(data.get("tax_rate", 0.18)),
        )


@dataclass
class Congress:
    house_control: PartyID
    senate_control: PartyID

    def to_dict(self) -> Dict[str, object]:
        return {"house_control": self.house_control.value, "senate_control": self.senate_control.value}

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Congress":
        return cls(house_control=PartyID(data["house_control"]), senate_control=PartyID(data["senate_control"]))


@dataclass
class President:
    name: str
    party: PartyID

    def to_dict(self) -> Dict[str, object]:
        return {"name": self.name, "party": self.party.value}

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "President":
        return cls(name=str(data["name"]), party=PartyID(data["party"]))


@dataclass
class SupremeCourt:
    lean: PartyID  # rough proxy for ideological lean

    def to_dict(self) -> Dict[str, object]:
        return {"lean": self.lean.value}

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "SupremeCourt":
        return cls(lean=PartyID(data["lean"]))


@dataclass
class ElectionResult:
    winner_party: PartyID
    details: Dict[str, float]

    def to_dict(self) -> Dict[str, object]:
        return {"winner_party": self.winner_party.value, "details": copy.deepcopy(self.details)}

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "ElectionResult":
        return cls(winner_party=PartyID(data["winner_party"]), details=dict(data.get("details", {})))


@dataclass
class Election:
    level: str  # 'federal' or state name
    chamber: Optional[Chamber] = None  # for federal/state legislature races
    office: Optional[str] = None  # e.g., 'President', 'Governor'
    year: int = 0

    def run(self, us: "UnitedStates", rng: random.Random) -> ElectionResult:
        """Very simplified election: swing based on approval and economy.
        Returns an ElectionResult with winner_party and detail metrics.
        """
        economy_signal = us.growth - us.inflation * 0.2 - us.unemployment * 0.3
        approval_signal = (
            us.opinion.approval_president - 50.0 if self.office == "President" else us.opinion.approval_congress - 30.0
        )
        base = 0.5 + 0.02 * economy_signal + 0.01 * approval_signal
        base = max(0.05, min(0.95, base))
        noise = rng.uniform(-0.05, 0.05)
        prob_dem = base + noise
        prob_dem = max(0.05, min(0.95, prob_dem))
        winner = PartyID.DEMOCRAT if rng.random() < prob_dem else PartyID.REPUBLICAN
        details = {
            "prob_dem": prob_dem,
            "economy_signal": economy_signal,
            "approval_signal": approval_signal,
        }
        return ElectionResult(winner_party=winner, details=details)

    def to_dict(self) -> Dict[str, object]:
        return {
            "level": self.level,
            "chamber": self.chamber.name if self.chamber else None,
            "office": self.office,
            "year": self.year,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Election":
        chamber = data.get("chamber")
        return cls(
            level=str(data["level"]),
            chamber=Chamber[chamber] if chamber else None,
            office=data.get("office"),
            year=int(data.get("year", 0)),
        )


@dataclass
class Event:
    key: str
    description: str
    # impacts are deltas applied at national level; states may add noise modifiers
    impact_approval_president: float = 0.0
    impact_approval_congress: float = 0.0
    impact_growth: float = 0.0
    impact_unemployment: float = 0.0
    impact_inflation: float = 0.0
    party_benefit: Optional[PartyID] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "key": self.key,
            "description": self.description,
            "impact_approval_president": self.impact_approval_president,
            "impact_approval_congress": self.impact_approval_congress,
            "impact_growth": self.impact_growth,
            "impact_unemployment": self.impact_unemployment,
            "impact_inflation": self.impact_inflation,
            "party_benefit": self.party_benefit.value if self.party_benefit else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Event":
        pb = data.get("party_benefit")
        return cls(
            key=str(data["key"]),
            description=str(data["description"]),
            impact_approval_president=float(data.get("impact_approval_president", 0.0)),
            impact_approval_congress=float(data.get("impact_approval_congress", 0.0)),
            impact_growth=float(data.get("impact_growth", 0.0)),
            impact_unemployment=float(data.get("impact_unemployment", 0.0)),
            impact_inflation=float(data.get("impact_inflation", 0.0)),
            party_benefit=PartyID(pb) if pb else None,
        )


class EventManager:
    """Random and triggered events with simple weighted selection."""

    def __init__(self, rng: random.Random):
        self.rng = rng
        self.catalog: Dict[str, Tuple[Event, float]] = {}

    def register(self, event: Event, weight: float = 1.0) -> None:
        self.catalog[event.key] = (event, weight)

    def random_event(self) -> Optional[Event]:
        if not self.catalog:
            return None
        events = list(self.catalog.values())
        total_w = sum(w for _, w in events)
        pick = self.rng.uniform(0, total_w)
        acc = 0.0
        for ev, w in events:
            acc += w
            if pick <= acc:
                return ev
        return events[-1][0]

    def to_dict(self) -> Dict[str, object]:
        return {
            "catalog": [
                {"event": ev.to_dict(), "weight": w}
                for (ev, w) in self.catalog.values()
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object], rng: random.Random) -> "EventManager":
        em = cls(rng)
        for item in data.get("catalog", []):
            ev = Event.from_dict(item["event"])
            w = float(item.get("weight", 1.0))
            em.register(ev, w)
        return em


@dataclass
class UnitedStates:
    """Top-level game state for the USA simulation.

    Provides the monthly turn loop, simple AI hooks, elections, events, and
    macro/state economic ticks. Use `advance_turn()` to move time forward.

    Use `snapshot()` to get a lightweight structured dict for logging/saving.
    """
    year: int
    month: int
    president: President
    congress: Congress
    court: SupremeCourt
    parties: Dict[PartyID, PoliticalParty]
    states: Dict[str, State]
    budget: FederalBudget
    opinion: PublicOpinion
    event_manager: EventManager
    rng: random.Random = field(default_factory=random.Random)

    # macro indicators (annualized rates, but we'll tick monthly/quarterly)
    growth: float = 0.02
    unemployment: float = 5.5
    inflation: float = 2.5

    log: List[str] = field(default_factory=list)
    recent_events: List[str] = field(default_factory=list)

    def log_event(self, msg: str) -> None:
        self.log.append(f"[{self.year}-{self.month:02d}] {msg}")

    # --- election helpers ---
    def _init_state_elections_if_missing(self, st: State) -> None:
        if not st.voter_cohorts:
            st.voter_cohorts = [
                VoterCohort(name="Urban Dem", share=0.4, lean=PartyID.DEMOCRAT, turnout=0.62),
                VoterCohort(name="Suburban Rep", share=0.4, lean=PartyID.REPUBLICAN, turnout=0.61),
                VoterCohort(name="Independent", share=0.2, lean=PartyID.INDEPENDENT, turnout=0.48),
            ]
        if not st.house_districts:
            # Create 6 districts with slight variations
            for i in range(6):
                swing = self.rng.uniform(-0.04, 0.04)
                bias = self.rng.uniform(-0.03, 0.03)
                # vary cohort shares a bit
                cohorts = []
                for c in st.voter_cohorts:
                    delta = self.rng.uniform(-0.05, 0.05)
                    share = max(0.05, min(0.9, c.share + delta))
                    cohorts.append(VoterCohort(name=c.name, share=share, lean=c.lean, turnout=c.turnout))
                # normalize shares
                total = sum(c.share for c in cohorts)
                for c in cohorts:
                    c.share = c.share / total
                st.house_districts.append(District(id=f"{st.name}-{i+1}", cohorts=cohorts, turnout_bias=bias, swing=swing))
        if not st.senate_seats or len(st.senate_seats) != 2:
            st.senate_seats = [st.legislature.senate, st.legislature.senate]
        if not st.senate_classes or len(st.senate_classes) != 2:
            # distribute classes; keep defaults but randomize the second to spread
            st.senate_classes = [self.rng.randrange(0, 6), (self.rng.randrange(0, 6))]

    def _national_signal_dem(self) -> float:
        economy_signal = self.growth - self.inflation * 0.2 - self.unemployment * 0.3
        approval_signal = self.opinion.approval_president - 50.0
        return 0.02 * economy_signal + 0.01 * approval_signal

    def _state_signal_dem(self, st: State) -> float:
        gov = (st.approval_governor - 50.0) / 200.0
        leg = (st.approval_legislature - 40.0) / 200.0
        return gov * (1 if st.governor_party == PartyID.DEMOCRAT else -1) + leg * (1 if st.legislature.house == PartyID.DEMOCRAT else -1)

    def _district_dem_probability(self, st: State, d: District) -> float:
        # cohort partisan tendency
        score = 0.0
        for c in d.cohorts:
            if c.lean == PartyID.DEMOCRAT:
                score += c.share * c.turnout * 1.0
            elif c.lean == PartyID.REPUBLICAN:
                score += c.share * c.turnout * -1.0
            else:
                score += c.share * c.turnout * 0.0
        base = 0.5 + 0.15 * score + d.swing + d.turnout_bias
        # incumbency modest advantage
        if d.incumbent == PartyID.DEMOCRAT:
            base += 0.02
        elif d.incumbent == PartyID.REPUBLICAN:
            base -= 0.02
        # national and state signals
        base += self._national_signal_dem()
        base += 0.5 * self._state_signal_dem(st)
        # noise
        base += self.rng.uniform(-0.03, 0.03)
        return max(0.05, min(0.95, base))

    def _statewide_dem_probability(self, st: State, incumbent: PartyID) -> float:
        # Aggregate cohorts statewide
        score = 0.0
        for c in (st.voter_cohorts or []):
            if c.lean == PartyID.DEMOCRAT:
                score += c.share * c.turnout * 1.0
            elif c.lean == PartyID.REPUBLICAN:
                score += c.share * c.turnout * -1.0
        base = 0.5 + 0.12 * score + 0.5 * self._state_signal_dem(st) + self._national_signal_dem()
        if incumbent == PartyID.DEMOCRAT:
            base += 0.02
        elif incumbent == PartyID.REPUBLICAN:
            base -= 0.02
        base += self.rng.uniform(-0.03, 0.03)
        return max(0.05, min(0.95, base))

    def _update_approvals_after_congress_results(self, prev_house: PartyID, prev_senate: PartyID) -> None:
        # modest approval adjustments
        if self.congress.house_control != prev_house:
            if self.congress.house_control == self.president.party:
                self.opinion.approval_president = max(0, min(100, self.opinion.approval_president + 1.0))
                self.opinion.approval_congress = max(0, min(100, self.opinion.approval_congress + 0.5))
            else:
                self.opinion.approval_president = max(0, min(100, self.opinion.approval_president - 1.0))
                self.opinion.approval_congress = max(0, min(100, self.opinion.approval_congress - 0.5))
        if self.congress.senate_control != prev_senate:
            if self.congress.senate_control == self.president.party:
                self.opinion.approval_president = max(0, min(100, self.opinion.approval_president + 0.5))
            else:
                self.opinion.approval_president = max(0, min(100, self.opinion.approval_president - 0.5))

    # --- AI stubs ---
    def ai_consider_policy(self) -> Optional[Policy]:
        """Very simple AI: sometimes propose a popular or counter-cyclical policy."""
        if self.rng.random() < 0.6:
            # economic tweak policy
            if self.growth < 0.0:
                return Policy(
                    title="Stimulus",
                    description="Counter-cyclical fiscal stimulus",
                    cost=300.0,
                    effect_growth=0.01,
                    effect_unemployment=-0.3,
                    popularity=60.0,
                    sponsor_party=self.president.party,
                )
            elif self.inflation > 4.0:
                return Policy(
                    title="Austerity",
                    description="Spending restraint to curb inflation",
                    cost=-100.0,
                    effect_growth=-0.005,
                    effect_inflation=-0.8,
                    popularity=45.0,
                    sponsor_party=self.congress.house_control,
                )
            else:
                return Policy(
                    title="Infrastructure",
                    description="Invest in infrastructure",
                    cost=200.0,
                    effect_growth=0.005,
                    effect_unemployment=-0.2,
                    popularity=65.0,
                    sponsor_party=self.president.party,
                )
        return None

    # --- state policy process ---
    def attempt_pass_state_policy(self, st: State, policy: Policy) -> bool:
        """Simulate state-level policy passage and apply effects to that state.
        Returns True if policy passes.
        """
        base_support = (policy.popularity - 50.0) / 120.0  # narrower range for states
        align = 0.12 if policy.sponsor_party in (st.legislature.house, st.legislature.senate) else -0.06
        gov_bonus = 0.08 if policy.sponsor_party == st.governor_party else 0.0
        opinion_push = (st.approval_governor - 50.0) / 200.0
        prob = 0.5 + base_support + align + gov_bonus + opinion_push
        prob = max(0.05, min(0.95, prob))
        if self.rng.random() < prob:
            # Apply local effects
            st.gdp *= (1.0 + policy.effect_growth)
            st.unemployment = max(2.5, min(20.0, st.unemployment + policy.effect_unemployment))
            st.inflation = max(0.0, min(20.0, st.inflation + policy.effect_inflation))
            if policy.cost >= 0:
                st.budget_spending += policy.cost
            else:
                st.budget_revenue += -policy.cost
            # Local approval shifts
            if policy.sponsor_party == st.governor_party:
                st.approval_governor = max(0.0, min(100.0, st.approval_governor + 0.8))
            st.approval_legislature = max(0.0, min(100.0, st.approval_legislature + 0.4))
            # National issue awareness
            self.opinion.update_issue(policy, self.rng.uniform(-2.0, 2.0))
            self.log_event(f"{st.name} policy passed: {policy.title}")
            return True
        else:
            self.log_event(f"{st.name} policy failed: {policy.title}")
            return False

    # --- AI: state-level decision this month ---
    def ai_state_turn(self, st: State) -> None:
        # Choose a policy theme based on state conditions
        pol: Optional[Policy] = None
        if st.unemployment > 6.5:
            pol = Policy(
                title="State Jobs Program",
                description="Hire for public works and small biz grants",
                cost=10.0,
                effect_growth=0.003,
                effect_unemployment=-0.2,
                popularity=62.0,
                sponsor_party=st.governor_party,
            )
        elif st.inflation > 5.0:
            pol = Policy(
                title="State Spending Freeze",
                description="Temporary restraint on non-essential spending",
                cost=-5.0,
                effect_growth=-0.001,
                effect_inflation=-0.2,
                popularity=52.0,
                sponsor_party=st.legislature.house,
            )
        elif st.budget_spending - st.budget_revenue > 5.0:
            pol = Policy(
                title="Budget Balance Act",
                description="Raise fees and cut waste to close gap",
                cost=-8.0,
                effect_growth=-0.0005,
                effect_unemployment=0.05,
                popularity=49.0,
                sponsor_party=st.legislature.senate,
            )
        else:
            if self.rng.random() < 0.35:
                pol = Policy(
                    title="State Infrastructure",
                    description="Fix roads and bridges",
                    cost=12.0,
                    effect_growth=0.002,
                    effect_unemployment=-0.1,
                    popularity=64.0,
                    sponsor_party=st.governor_party,
                )
        if pol:
            self.attempt_pass_state_policy(st, pol)

        # Campaigning: gently adjust district swing/turnout
        if self.rng.random() < 0.30:
            party = st.governor_party
            adj = 0.004 if party == PartyID.DEMOCRAT else -0.004
            for d in st.house_districts:
                d.swing = max(-0.2, min(0.2, d.swing + adj + self.rng.uniform(-0.002, 0.002)))
                d.turnout_bias = max(-0.1, min(0.1, d.turnout_bias + self.rng.uniform(-0.002, 0.002)))
            # small approval nudges
            st.approval_governor = max(0, min(100, st.approval_governor + 0.2))
            st.approval_legislature = max(0, min(100, st.approval_legislature + 0.1))

    # --- AI: national party strategy placeholders ---
    def ai_party_national_strategy(self) -> None:
        """Placeholder: tweak party approvals based on macro context."""
        deficit_ratio = (self.budget.spending - self.budget.revenue) / max(1.0, self.budget.revenue)
        econ = self.growth - 0.2 * self.inflation - 0.3 * self.unemployment
        # Dems gain on growth, Reps gain on inflation/deficit concerns (simplified heuristic)
        self.parties[PartyID.DEMOCRAT].adjust_approval(0.2 * econ)
        self.parties[PartyID.REPUBLICAN].adjust_approval(0.5 * (0.02 - econ) + 0.5 * deficit_ratio)

    def ai_react_to_events(self) -> None:
        """Placeholder reactions to very recent events: propose emergency actions or campaign messaging."""
        if not self.recent_events:
            return
        recent = self.recent_events[-1]
        if recent == "hurricane":
            # Federal emergency package
            pol = Policy(
                title="Disaster Relief",
                description="Emergency aid to impacted regions",
                cost=50.0,
                effect_growth=0.001,
                effect_unemployment=-0.05,
                popularity=70.0,
                sponsor_party=self.president.party,
            )
            self.attempt_pass_policy(pol)
            # Likely impacted states campaign and local measures (TX, FL if present)
            for name in ("Texas", "Florida"):
                st = self.states.get(name)
                if st:
                    self.ai_state_turn(st)
        elif recent == "scandal":
            # Opposing party campaigns nationally
            opp = PartyID.REPUBLICAN if self.president.party == PartyID.DEMOCRAT else PartyID.DEMOCRAT
            self.parties[opp].adjust_approval(1.0)
        # Other events could be handled similarly

    # --- policy process ---
    def attempt_pass_policy(self, policy: Policy) -> bool:
        """Simulate legislative passage influenced by party control and popularity.
        Returns True if policy passes.
        """
        base_support = (policy.popularity - 50.0) / 100.0  # -0.5..+0.5
        alignment = 0.15 if policy.sponsor_party in (self.congress.house_control, self.congress.senate_control) else -0.05
        pres_bonus = 0.1 if policy.sponsor_party == self.president.party else 0.0
        court_risk = -0.05 if policy.effect_inflation > 0.7 and self.court.lean != policy.sponsor_party else 0.0
        prob = 0.5 + base_support + alignment + pres_bonus + court_risk
        prob = max(0.05, min(0.95, prob))
        if self.rng.random() < prob:
            # apply macro effects
            self.growth += policy.effect_growth
            self.unemployment = max(2.5, min(20.0, self.unemployment + policy.effect_unemployment))
            self.inflation = max(0.0, min(20.0, self.inflation + policy.effect_inflation))
            self.budget.spending += max(0.0, policy.cost)
            self.budget.revenue += max(0.0, -policy.cost)  # negative cost means savings
            self.opinion.update_issue(policy, self.rng.uniform(-5, 5))
            # approvals shift modestly toward sponsor party success
            if policy.sponsor_party == self.president.party:
                self.opinion.approval_president = max(0.0, min(100.0, self.opinion.approval_president + 1.0))
            self.log_event(f"Policy passed: {policy.title}")
            return True
        else:
            self.log_event(f"Policy failed: {policy.title}")
            return False

    # --- elections ---
    def maybe_run_elections(self) -> None:
        """Run granular elections: House by districts (even years), Senate staggered (6-year classes), President every 4 years."""
        if self.month != 11:
            return
        year = self.year
        prev_house = self.congress.house_control
        prev_senate = self.congress.senate_control

        # Ensure structures
        for st in self.states.values():
            self._init_state_elections_if_missing(st)

        # House elections (all seats) every 2 years
        if year % 2 == 0:
            dem_seats = 0
            rep_seats = 0
            for st in self.states.values():
                for d in st.house_districts:
                    p_dem = self._district_dem_probability(st, d)
                    winner = PartyID.DEMOCRAT if self.rng.random() < p_dem else PartyID.REPUBLICAN
                    d.incumbent = winner
                    if winner == PartyID.DEMOCRAT:
                        dem_seats += 1
                    else:
                        rep_seats += 1
            self.congress.house_control = PartyID.DEMOCRAT if dem_seats >= rep_seats else PartyID.REPUBLICAN
            self.log_event(f"House elections (granular): D {dem_seats} - R {rep_seats}")

        # Senate: seats up based on class == year % 6
        dem_total = 0
        rep_total = 0
        cycle = year % 6
        for st in self.states.values():
            for i in range(2):
                inc = st.senate_seats[i]
                if st.senate_classes[i] == cycle:
                    p_dem = self._statewide_dem_probability(st, inc)
                    winner = PartyID.DEMOCRAT if self.rng.random() < p_dem else PartyID.REPUBLICAN
                    st.senate_seats[i] = winner
            # count totals after possible updates
            for seat in st.senate_seats:
                if seat == PartyID.DEMOCRAT:
                    dem_total += 1
                elif seat == PartyID.REPUBLICAN:
                    rep_total += 1
        if dem_total or rep_total:
            self.congress.senate_control = PartyID.DEMOCRAT if dem_total >= rep_total else PartyID.REPUBLICAN
            self.log_event(f"Senate elections (staggered): D {dem_total} - R {rep_total}")

        # President every 4 years
        if year % 4 == 0:
            result_pres = Election(level="federal", office="President", year=year).run(self, self.rng)
            self.president.party = result_pres.winner_party
            self.log_event(f"Presidential election: {result_pres.winner_party.value}")

        # Post-election approvals
        self._update_approvals_after_congress_results(prev_house, prev_senate)

    # --- events ---
    def trigger_event(self) -> Optional[Event]:
        ev = self.event_manager.random_event()
        if not ev:
            return None
        self.growth += ev.impact_growth
        self.unemployment = max(2.5, min(20.0, self.unemployment + ev.impact_unemployment))
        self.inflation = max(0.0, min(20.0, self.inflation + ev.impact_inflation))
        self.opinion.approval_president = max(0.0, min(100.0, self.opinion.approval_president + ev.impact_approval_president))
        self.opinion.approval_congress = max(0.0, min(100.0, self.opinion.approval_congress + ev.impact_approval_congress))
        if ev.party_benefit and ev.party_benefit in self.parties:
            self.parties[ev.party_benefit].adjust_approval(1.0)
        self.log_event(f"Event: {ev.description}")
        # Track recent events by key for AI
        self.recent_events.append(ev.key)
        if len(self.recent_events) > 12:
            self.recent_events.pop(0)
        return ev

    # --- monthly/quarterly tick ---
    def advance_turn(self, months: int = 1) -> None:
        for _ in range(months):
            # macro drift
            self.growth += self.rng.uniform(-0.002, 0.002)
            self.inflation += self.rng.uniform(-0.05, 0.05)
            self.unemployment += self.rng.uniform(-0.05, 0.05)
            # clamp
            self.growth = max(-0.05, min(0.06, self.growth))
            self.inflation = max(0.0, min(10.0, self.inflation))
            self.unemployment = max(2.5, min(20.0, self.unemployment))

            # state economies
            for st in self.states.values():
                st.advance_economy(self.growth, self.inflation, self.rng)
                # simplistic public finance update for states
                st.budget_revenue = st.tax_rate * st.gdp
                # spending mean-reverts toward revenue with small noise
                st.budget_spending += 0.2 * (st.budget_revenue - st.budget_spending) + self.rng.uniform(-1.0, 1.0)

            # AI policy consideration
            pol = self.ai_consider_policy()
            if pol:
                self.attempt_pass_policy(pol)
            # State AIs propose and campaign
            for st in self.states.values():
                self.ai_state_turn(st)

            # events chance
            if self.rng.random() < 0.35:
                self.trigger_event()
                # Reactions to the most recent event
                self.ai_react_to_events()

            # elections if applicable
            self.maybe_run_elections()

            # approvals mean reversion
            self.opinion.approval_president += 0.05 * (50.0 - self.opinion.approval_president)
            self.opinion.approval_congress += 0.05 * (40.0 - self.opinion.approval_congress)
            self.opinion.approval_president = max(0.0, min(100.0, self.opinion.approval_president))
            self.opinion.approval_congress = max(0.0, min(100.0, self.opinion.approval_congress))

            # national party strategic drift
            if self.rng.random() < 0.5:
                self.ai_party_national_strategy()

            # federal revenue tracks national GDP via tax_rate
            total_gdp = sum(st.gdp for st in self.states.values())
            self.budget.revenue = self.budget.tax_rate * total_gdp

            # time
            self.month += 1
            if self.month > 12:
                self.month = 1
                self.year += 1

    # --- factory ---
    @staticmethod
    def new_default(seed: Optional[int] = None) -> "UnitedStates":
        rng = random.Random(seed)
        parties = {
            PartyID.DEMOCRAT: PoliticalParty(PartyID.DEMOCRAT, national_approval=52.0),
            PartyID.REPUBLICAN: PoliticalParty(PartyID.REPUBLICAN, national_approval=48.0),
            PartyID.INDEPENDENT: PoliticalParty(PartyID.INDEPENDENT, national_approval=35.0),
        }
        states = {
            "California": State(
                name="California",
                population=39000000,
                gdp=3200.0,
                unemployment=4.8,
                inflation=2.8,
                governor_party=PartyID.DEMOCRAT,
                legislature=LegislatureControl(house=PartyID.DEMOCRAT, senate=PartyID.DEMOCRAT),
            ),
            "Texas": State(
                name="Texas",
                population=30000000,
                gdp=2000.0,
                unemployment=4.0,
                inflation=2.5,
                governor_party=PartyID.REPUBLICAN,
                legislature=LegislatureControl(house=PartyID.REPUBLICAN, senate=PartyID.REPUBLICAN),
            ),
            "Florida": State(
                name="Florida",
                population=22000000,
                gdp=1100.0,
                unemployment=3.5,
                inflation=2.6,
                governor_party=PartyID.REPUBLICAN,
                legislature=LegislatureControl(house=PartyID.REPUBLICAN, senate=PartyID.REPUBLICAN),
            ),
            "New York": State(
                name="New York",
                population=19500000,
                gdp=1800.0,
                unemployment=4.2,
                inflation=2.7,
                governor_party=PartyID.DEMOCRAT,
                legislature=LegislatureControl(house=PartyID.DEMOCRAT, senate=PartyID.DEMOCRAT),
            ),
        }
        # Initialize election structures for each state
        tmp_us = {
            "year": 2025,
            "month": 1,
        }
        # Use a temporary UnitedStates-like object for init helper signature by ad-hoc call later
        # Instead, we will just do a quick local init similar to helper to avoid complexity here.
        for st in states.values():
            if not st.voter_cohorts:
                st.voter_cohorts = [
                    VoterCohort(name="Urban Dem", share=0.42, lean=PartyID.DEMOCRAT, turnout=0.62),
                    VoterCohort(name="Suburban Rep", share=0.40, lean=PartyID.REPUBLICAN, turnout=0.61),
                    VoterCohort(name="Independent", share=0.18, lean=PartyID.INDEPENDENT, turnout=0.48),
                ]
            if not st.house_districts:
                # Create 6 basic districts with minor swings
                rnd = random.Random(seed + 1 if seed is not None else None)
                for i in range(6):
                    swing = rnd.uniform(-0.04, 0.04)
                    bias = rnd.uniform(-0.03, 0.03)
                    cohorts = []
                    for c in st.voter_cohorts:
                        delta = rnd.uniform(-0.05, 0.05)
                        share = max(0.05, min(0.9, c.share + delta))
                        cohorts.append(VoterCohort(name=c.name, share=share, lean=c.lean, turnout=c.turnout))
                    total = sum(c.share for c in cohorts)
                    for c in cohorts:
                        c.share = c.share / total
                    st.house_districts.append(District(id=f"{st.name}-{i+1}", cohorts=cohorts, turnout_bias=bias, swing=swing))
            if not st.senate_seats or len(st.senate_seats) != 2:
                st.senate_seats = [st.legislature.senate, st.legislature.senate]
            if not st.senate_classes or len(st.senate_classes) != 2:
                rnd2 = random.Random(seed + 2 if seed is not None else None)
                st.senate_classes = [rnd2.randrange(0, 6), rnd2.randrange(0, 6)]
        budget = FederalBudget(revenue=4500.0, spending=5200.0)
        president = President(name="Incumbent", party=PartyID.DEMOCRAT)
        congress = Congress(house_control=PartyID.DEMOCRAT, senate_control=PartyID.DEMOCRAT)
        court = SupremeCourt(lean=PartyID.REPUBLICAN)
        opinion = PublicOpinion(approval_president=51.0, approval_congress=38.0)
        em = EventManager(rng)
        # register some events
        em.register(Event(key="hurricane", description="Major hurricane hits Gulf Coast", impact_growth=-0.003, impact_unemployment=0.2, impact_inflation=0.1))
        em.register(Event(key="tech_boom", description="Tech productivity boom", impact_growth=0.004, impact_unemployment=-0.15, impact_inflation=0.0), weight=0.6)
        em.register(Event(key="scandal", description="Political scandal", impact_approval_president=-2.5, party_benefit=PartyID.REPUBLICAN))
        em.register(Event(key="bipartisan", description="Bipartisan breakthrough", impact_approval_congress=2.0))
        return UnitedStates(
            year=2025,
            month=1,
            president=president,
            congress=congress,
            court=court,
            parties=parties,
            states=states,
            budget=budget,
            opinion=opinion,
            event_manager=em,
            rng=rng,
        )

    # --- structured snapshot ---
    def snapshot(self, last_logs: int = 20) -> Dict[str, object]:
        """Return a lightweight structured dict of current state for debugging/saving.

        Note: This is not a full fidelity serializer; it’s intended for logs,
        telemetry, or quick saves and can be extended to proper to_dict/from_dict.
        """
        return {
            "time": {"year": self.year, "month": self.month},
            "macro": {
                "growth": self.growth,
                "unemployment": self.unemployment,
                "inflation": self.inflation,
            },
            "federal": {
                "president_party": self.president.party.value,
                "house_control": self.congress.house_control.value,
                "senate_control": self.congress.senate_control.value,
                "court_lean": self.court.lean.value,
                "budget": {
                    "revenue": self.budget.revenue,
                    "spending": self.budget.spending,
                    "deficit": self.budget.deficit,
                },
                "opinion": {
                    "president": self.opinion.approval_president,
                    "congress": self.opinion.approval_congress,
                },
            },
            "states": {
                name: {
                    "population": st.population,
                    "gdp": st.gdp,
                    "unemployment": st.unemployment,
                    "inflation": st.inflation,
                    "rev": st.budget_revenue,
                    "spend": st.budget_spending,
                    "tax_rate": st.tax_rate,
                    "governor_party": st.governor_party.value,
                    "leg_house": st.legislature.house.value,
                    "leg_senate": st.legislature.senate.value,
                }
                for name, st in self.states.items()
            },
            "parties": {pid.value: p.national_approval for pid, p in self.parties.items()},
            "log_tail": self.log[-last_logs:],
        }

    # --- serialization ---
    def to_dict(self) -> Dict[str, object]:
        return {
            "time": {"year": self.year, "month": self.month},
            "macro": {
                "growth": self.growth,
                "unemployment": self.unemployment,
                "inflation": self.inflation,
            },
            "federal": {
                "president": self.president.to_dict(),
                "congress": self.congress.to_dict(),
                "court": self.court.to_dict(),
                "budget": self.budget.to_dict(),
                "opinion": self.opinion.to_dict(),
            },
            "parties": {pid.value: p.to_dict() for pid, p in self.parties.items()},
            "states": {name: st.to_dict() for name, st in self.states.items()},
            "events": self.event_manager.to_dict(),
            "rng_state": _listify(self.rng.getstate()),
            "log": list(self.log),
            "recent_events": list(self.recent_events),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "UnitedStates":
        y = int(data["time"]["year"])  # type: ignore[index]
        m = int(data["time"]["month"])  # type: ignore[index]
        rng = random.Random()
        rng_state = data.get("rng_state")
        if rng_state is not None:
            rng.setstate(_tupleify(rng_state))
        parties = {PartyID(k): PoliticalParty.from_dict(v) for k, v in data.get("parties", {}).items()}
        states = {k: State.from_dict(v) for k, v in data.get("states", {}).items()}
        em = EventManager.from_dict(data.get("events", {}), rng)
        us = cls(
            year=y,
            month=m,
            president=President.from_dict(data["federal"]["president"]),  # type: ignore[index]
            congress=Congress.from_dict(data["federal"]["congress"]),  # type: ignore[index]
            court=SupremeCourt.from_dict(data["federal"]["court"]),  # type: ignore[index]
            parties=parties,
            states=states,
            budget=FederalBudget.from_dict(data["federal"]["budget"]),  # type: ignore[index]
            opinion=PublicOpinion.from_dict(data["federal"]["opinion"]),  # type: ignore[index]
            event_manager=em,
            rng=rng,
            growth=float(data["macro"]["growth"]),  # type: ignore[index]
            unemployment=float(data["macro"]["unemployment"]),  # type: ignore[index]
            inflation=float(data["macro"]["inflation"]),  # type: ignore[index]
            log=list(data.get("log", [])),
        )
        us.recent_events = list(data.get("recent_events", []))
        return us
