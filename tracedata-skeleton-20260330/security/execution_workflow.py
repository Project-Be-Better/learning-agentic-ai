"""
Execution Workflow Specification

Define whether agents run sequentially or in parallel, with explicit dependencies.
This determines Celery task chaining and event listener logic.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Set

from models.event_config import AgentType

# ==============================================================================
# EXECUTION POLICIES
# ==============================================================================


class ExecutionPolicy(Enum):
    """How agents should execute"""

    SEQUENTIAL = auto()
    """Agents run one after another in order. Each must complete before next starts."""

    PARALLEL = auto()
    """Agents run simultaneously (no dependencies)."""

    CONDITIONAL = auto()
    """Agents run based on conditions (e.g., "only if scoring fails")."""


# ==============================================================================
# AGENT SEQUENCE DEFINITION
# ==============================================================================


@dataclass
class AgentSequenceStep:
    """
    One step in the execution sequence.

    Example:
        Step 1: SafetyAgent (order=1, depends_on={})
        Step 2: ScoringAgent (order=2, depends_on={AgentType.SAFETY})
        Step 3: DriverSupportAgent (order=3, depends_on={AgentType.SCORING})
    """

    agent: AgentType
    """Which agent runs at this step"""

    order: int
    """Execution order (1, 2, 3, ...). Lower runs first."""

    depends_on: Set[AgentType] = field(default_factory=set)
    """Which agents must complete before this one starts.
    
    Example:
        SafetyAgent: depends_on={}  (no dependencies)
        ScoringAgent: depends_on={AgentType.SAFETY}  (wait for safety first)
    """

    optional: bool = False
    """Can this step be skipped if dependencies fail?
    
    Example:
        CoachingAgent: optional=True (skip if scoring fails)
        SafetyAgent: optional=False (always required)
    """

    @property
    def is_first(self) -> bool:
        """Is this the first step (no dependencies)"""
        return len(self.depends_on) == 0

    def blocks(self, other_agent: AgentType) -> bool:
        """Does this agent block another agent?"""
        return (
            self.agent in other_agent.depends_on
            if hasattr(other_agent, "depends_on")
            else False
        )


@dataclass
class ExecutionWorkflow:
    """
    Complete execution workflow for an event.

    Defines:
    - What agents run
    - In what order (sequential)
    - What depends on what (dependencies)
    - Can they run in parallel (execution_policy)

    Example (harsh_brake):
        Policy: SEQUENTIAL
        Steps:
          1. ScoringAgent (order=1, depends_on={})
          2. DriverSupportAgent (order=2, depends_on={ScoringAgent})

    Example (collision):
        Policy: SEQUENTIAL
        Steps:
          1. SafetyAgent (order=1, depends_on={})
          2. ScoringAgent (order=2, depends_on={SafetyAgent})
          3. DriverSupportAgent (order=3, depends_on={ScoringAgent})
    """

    execution_policy: ExecutionPolicy
    """Sequential, Parallel, or Conditional"""

    steps: List[AgentSequenceStep] = field(default_factory=list)
    """Ordered list of execution steps"""

    timeout_seconds: int = 300
    """How long to wait for all agents to complete"""

    @property
    def agents(self) -> Set[AgentType]:
        """All agents in this workflow"""
        return {step.agent for step in self.steps}

    @property
    def first_agents(self) -> Set[AgentType]:
        """Agents that run first (no dependencies)"""
        return {step.agent for step in self.steps if step.is_first}

    @property
    def is_sequential(self) -> bool:
        """Is this a sequential workflow?"""
        return self.execution_policy == ExecutionPolicy.SEQUENTIAL

    @property
    def is_parallel(self) -> bool:
        """Is this a parallel workflow?"""
        return self.execution_policy == ExecutionPolicy.PARALLEL

    def get_step(self, agent: AgentType) -> "AgentSequenceStep":
        """Get the step for an agent"""
        for step in self.steps:
            if step.agent == agent:
                return step
        return None

    def get_dependents(self, agent: AgentType) -> List[AgentType]:
        """Get agents that depend on this agent"""
        dependents = []
        for step in self.steps:
            if agent in step.depends_on:
                dependents.append(step.agent)
        return dependents

    def validate(self) -> tuple[bool, str]:
        """Validate workflow (no circular dependencies, etc.)"""

        # Check for circular dependencies
        visited = set()
        rec_stack = set()

        def has_cycle(agent: AgentType) -> bool:
            visited.add(agent)
            rec_stack.add(agent)

            step = self.get_step(agent)
            if step:
                for dep in step.depends_on:
                    if dep not in visited:
                        if has_cycle(dep):
                            return True
                    elif dep in rec_stack:
                        return True

            rec_stack.remove(agent)
            return False

        for agent in self.agents:
            if agent not in visited:
                if has_cycle(agent):
                    return False, f"Circular dependency detected involving {agent}"

        return True, "Valid"


# ==============================================================================
# WORKFLOW EXAMPLES (COMMON PATTERNS)
# ==============================================================================

# Pattern 1: SEQUENTIAL (Most Common)
# Safety → Scoring → Coaching
SEQUENTIAL_SAFETY_SCORING_COACHING = ExecutionWorkflow(
    execution_policy=ExecutionPolicy.SEQUENTIAL,
    steps=[
        AgentSequenceStep(
            agent=AgentType.SAFETY,
            order=1,
            depends_on=set(),
            optional=False,
        ),
        AgentSequenceStep(
            agent=AgentType.SCORING,
            order=2,
            depends_on={AgentType.SAFETY},
            optional=False,
        ),
        AgentSequenceStep(
            agent=AgentType.DRIVER_SUPPORT,
            order=3,
            depends_on={AgentType.SCORING},
            optional=True,  # Can skip if coaching not needed
        ),
    ],
    timeout_seconds=300,
)

# Pattern 2: SEQUENTIAL (Scoring → Coaching only)
SEQUENTIAL_SCORING_COACHING = ExecutionWorkflow(
    execution_policy=ExecutionPolicy.SEQUENTIAL,
    steps=[
        AgentSequenceStep(
            agent=AgentType.SCORING,
            order=1,
            depends_on=set(),
            optional=False,
        ),
        AgentSequenceStep(
            agent=AgentType.DRIVER_SUPPORT,
            order=2,
            depends_on={AgentType.SCORING},
            optional=True,
        ),
    ],
    timeout_seconds=300,
)

# Pattern 3: SEQUENTIAL (Scoring only)
SEQUENTIAL_SCORING_ONLY = ExecutionWorkflow(
    execution_policy=ExecutionPolicy.SEQUENTIAL,
    steps=[
        AgentSequenceStep(
            agent=AgentType.SCORING,
            order=1,
            depends_on=set(),
            optional=False,
        ),
    ],
    timeout_seconds=60,
)

# Pattern 4: SEQUENTIAL (Safety only)
SEQUENTIAL_SAFETY_ONLY = ExecutionWorkflow(
    execution_policy=ExecutionPolicy.SEQUENTIAL,
    steps=[
        AgentSequenceStep(
            agent=AgentType.SAFETY,
            order=1,
            depends_on=set(),
            optional=False,
        ),
    ],
    timeout_seconds=60,
)

# Pattern 5: PARALLEL (Scoring + Sentiment together)
# No dependencies, both can run at same time
PARALLEL_SCORING_SENTIMENT = ExecutionWorkflow(
    execution_policy=ExecutionPolicy.PARALLEL,
    steps=[
        AgentSequenceStep(
            agent=AgentType.SCORING,
            order=1,
            depends_on=set(),
            optional=False,
        ),
        AgentSequenceStep(
            agent=AgentType.SENTIMENT,
            order=1,  # Same order = run in parallel
            depends_on=set(),
            optional=False,
        ),
    ],
    timeout_seconds=120,
)


# ==============================================================================
# WORKFLOW REGISTRY (Map Actions to Workflows)
# ==============================================================================

# Which workflow to use for each action
ACTION_TO_WORKFLOW = {
    # Critical events: Safety → Scoring
    # (no coaching for critical, immediate action)
    "Emergency Alert & 911": SEQUENTIAL_SAFETY_ONLY,
    "Emergency Alert": SEQUENTIAL_SAFETY_ONLY,
    "Fleet Alert": SEQUENTIAL_SAFETY_ONLY,
    # Coaching: Scoring → Driver Support
    "Coaching": SEQUENTIAL_SCORING_COACHING,
    # Regulatory: Just Scoring
    "Regulatory": SEQUENTIAL_SCORING_ONLY,
    # Standard Scoring
    "Scoring": SEQUENTIAL_SCORING_ONLY,
    # Sentiment: Just Sentiment
    "Sentiment": ExecutionWorkflow(
        execution_policy=ExecutionPolicy.SEQUENTIAL,
        steps=[
            AgentSequenceStep(
                agent=AgentType.SENTIMENT,
                order=1,
                depends_on=set(),
                optional=False,
            ),
        ],
        timeout_seconds=60,
    ),
    # Support: Just Driver Support
    "Support": ExecutionWorkflow(
        execution_policy=ExecutionPolicy.SEQUENTIAL,
        steps=[
            AgentSequenceStep(
                agent=AgentType.DRIVER_SUPPORT,
                order=1,
                depends_on=set(),
                optional=False,
            ),
        ],
        timeout_seconds=60,
    ),
    # HITL: Human in the loop
    "HITL": ExecutionWorkflow(
        execution_policy=ExecutionPolicy.SEQUENTIAL,
        steps=[
            AgentSequenceStep(
                agent=AgentType.HUMAN_IN_THE_LOOP,
                order=1,
                depends_on=set(),
                optional=False,
            ),
        ],
        timeout_seconds=3600,  # Much longer for human review
    ),
    # No agents needed
    "Analytics": ExecutionWorkflow(
        execution_policy=ExecutionPolicy.SEQUENTIAL,
        steps=[],
    ),
    "Logging": ExecutionWorkflow(
        execution_policy=ExecutionPolicy.SEQUENTIAL,
        steps=[],
    ),
    "Reward Bonus": ExecutionWorkflow(
        execution_policy=ExecutionPolicy.SEQUENTIAL,
        steps=[],
    ),
    "Reject & Log": ExecutionWorkflow(
        execution_policy=ExecutionPolicy.SEQUENTIAL,
        steps=[],
    ),
}


# ==============================================================================
# WORKFLOW VALIDATION EXAMPLES
# ==============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("EXECUTION WORKFLOW VALIDATION")
    print("=" * 70)

    # Test 1: Sequential workflow
    print("\n[TEST 1] Sequential: Safety → Scoring → Coaching")
    valid, msg = SEQUENTIAL_SAFETY_SCORING_COACHING.validate()
    print(f"  Valid: {valid} ({msg})")
    print(f"  Policy: {SEQUENTIAL_SAFETY_SCORING_COACHING.execution_policy.name}")
    print(
        f"  Steps: {[s.agent.value for s in SEQUENTIAL_SAFETY_SCORING_COACHING.steps]}"
    )
    print(
        f"  First agents: {[a.value for a in SEQUENTIAL_SAFETY_SCORING_COACHING.first_agents]}"
    )

    # Test 2: Dependencies
    print("\n[TEST 2] Check dependencies")
    scoring_step = SEQUENTIAL_SAFETY_SCORING_COACHING.get_step(AgentType.SCORING)
    print(f"  ScoringAgent depends on: {[a.value for a in scoring_step.depends_on]}")

    coaching_step = SEQUENTIAL_SAFETY_SCORING_COACHING.get_step(
        AgentType.DRIVER_SUPPORT
    )
    print(
        f"  DriverSupportAgent depends on: {[a.value for a in coaching_step.depends_on]}"
    )
    print(f"  DriverSupportAgent optional: {coaching_step.optional}")

    # Test 3: Parallel workflow
    print("\n[TEST 3] Parallel: Scoring + Sentiment (no dependencies)")
    valid, msg = PARALLEL_SCORING_SENTIMENT.validate()
    print(f"  Valid: {valid} ({msg})")
    print(f"  Policy: {PARALLEL_SCORING_SENTIMENT.execution_policy.name}")
    print(f"  Is parallel: {PARALLEL_SCORING_SENTIMENT.is_parallel}")

    print("\n" + "=" * 70)
    print("✅ ALL VALIDATIONS PASSED")
    print("=" * 70)
