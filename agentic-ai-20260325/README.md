# Agent Framework with Intent Gate

A secure agent execution framework using signed Intent Capsules for permission management and execution control.

## Architecture

### Class Diagram

```mermaid
classDiagram
    class TDAgentBase {
        -agent_id: String
        -secret_key: String
        -logger: StructuredLogger
        +run(state: TDAgentState) Dict
        #_execute_logic(trip_context: Dict) Dict*
    }
    
    class TDScoringAgent {
        +_execute_logic(trip_context: Dict) Dict
    }
    
    class TDAgentEnum {
        SCORING_AGENT
        SAFETY_AGENT
    }
    
    class StructuredLogger {
        -logger: logging.Logger
        -handler: logging.StreamHandler
        +info(action: str, **kwargs)
        +warning(action: str, **kwargs)
        +error(action: str, **kwargs)
    }
    
    class LogContext {
        -logger: StructuredLogger
        -action: str
        +__enter__() LogContext
        +__exit__() None
    }
    
    class SecurityError {
    }
    
    class TamperingError {
    }
    
    class ExpirationError {
    }
    
    class ConstraintViolationError {
    }
    
    class MissingFieldError {
    }
    
    TDAgentBase <|-- TDScoringAgent
    TDAgentBase --> TDAgentEnum
    TDAgentBase --> StructuredLogger
    TDAgentBase --> LogContext
    TDAgentBase --> SecurityError
    SecurityError <|-- TamperingError
    SecurityError <|-- ExpirationError
    SecurityError <|-- ConstraintViolationError
    SecurityError <|-- MissingFieldError
    
    note "Intent Gate decorator\non run() method"
    note "Structured JSON logging\nfor ELK/PLG stacks"
```

### Execution Flow with Security & Logging

```mermaid
sequenceDiagram
    participant Client
    participant Agent as Agent.run()
    participant Gate as Intent Gate
    participant Logger as StructuredLogger
    participant Logic as _execute_logic()
    
    Client->>Agent: state (trip_context + capsule)
    Agent->>Gate: Verify capsule
    
    alt Signature Valid
        Gate->>Logger: ✅ Security check passed
        Logger-->>Gate: JSON log event
        Gate->>Agent: Proceed
    else Signature Invalid
        Gate->>Logger: ❌ Tampering detected
        Logger-->>Gate: JSON log event
        Gate->>Agent: TamperingError (exception)
    end
    
    alt Capsule Not Expired
        Agent->>Logger: Generate correlation_id (uuid)
        Agent->>Logic: Execute with LogContext
        LogContext->>Logic: Measure execution time
        Logic-->>LogContext: Result
        LogContext->>Logger: Execution time + status
        Logger-->>Client: Final JSON log
    else Capsule Expired
        Gate->>Logger: ❌ Capsule expired
        Logger-->>Client: Expiration JSON log
    end
    
    Agent-->>Client: Result + metadata
```

### Structured Logging Format (ELK/PLG Compatible)

```json
{
  "timestamp": "2026-03-26T12:34:56.789Z",
  "level": "INFO",
  "action": "agent_execution_completed",
  "status": "success",
  "agent_id": "scoring_agent",
  "trip_id": "TRIP-001",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "duration_ms": 45.23,
  "output_keys": ["trip_score", "harsh_events_count"],
  "error": null,
  "timestamp_unix": 1711353296.789
}
```

### Security Event Logging

```mermaid
graph TD
    A["Intent Capsule"] -->|verify| B["Intent Gate"]
    B -->|check signature| C{Signature Valid?}
    C -->|✅ Yes| D["Log: security_check passed"]
    C -->|❌ No| E["Log: signature_mismatch<br/>Raise TamperingError"]
    
    D -->|check expiration| F{Not Expired?}
    F -->|✅ Yes| G["Log: constraint_check<br/>Proceed to agent"]
    F -->|❌ No| H["Log: capsule_expired<br/>Raise ExpirationError"]
    
    E -->|with metadata| I["↓ Security Event<br/>event_id + trip_id<br/>+ severity"]
    H -->|with metadata| I
    D -->|with metadata| J["↓ Audit Log<br/>Passed validation<br/>trip_id + timestamp"]
```

## Components

### Core Classes

- **TDAgentBase**: Abstract base for all agents
  - `run()`: Pure execution with structured logging (validate → execute → wrap)
  - `_execute_logic()`: Override for custom logic
  - Protected by `@verify_intent_capsule` decorator
  - Logger injected as instance variable for observability
  - Generates correlation IDs (uuid) for distributed tracing

- **TDScoringAgent**: Scores trips based on harsh events
  - Formula: `100 - (harsh_events * 5)`, min 0
  - Inherits logging and security validation from base class

- **StructuredLogger**: Production-ready JSON logging
  - Compatible with ELK (Elasticsearch/Logstash/Kibana) stacks
  - Compatible with PLG (Prometheus/Loki/Grafana) stacks
  - Methods: `info()`, `warning()`, `error()` with structured context
  - JSONFormatter for automatic JSON serialization

- **LogContext**: Context manager for operation tracing
  - Automatically measures execution time (duration_ms)
  - Tracks correlation IDs across distributed requests
  - Wraps operations for consistent logging

### Security

- **Intent Capsule**: Signed work order containing:
  - Trip ID, subject, purpose
  - Allowed actions & constraints
  - Issued/expiry timestamps
  - HMAC-SHA256 signature

- **Intent Gate**: Decorator that validates with structured event logging:
  - Signature verification (detect tampering)
  - Expiration check (time window validation)
  - Constraint validation (resource/action limits)
  - Logs all security events with: event_id, trip_id, severity, action, reason
  - Returns specific exceptions on failure
  - All events logged as JSON for audit trail

### Observability

- **Structured Logging**: JSON output includes:
  - Timestamp (ISO 8601 with milliseconds)
  - Log level (INFO, WARNING, ERROR)
  - Action identifier (what operation)
  - Status (success/failed/in-progress)
  - Agent/trip context (agent_id, trip_id)
  - Correlation ID (uuid for request tracing)
  - Duration metrics (execution time in ms)
  - Error details (if applicable)

- **Security Events**: Audit-grade logging with:
  - Unique security_event_id for tracking
  - Reason for security check result
  - Severity level (critical/medium/low)
  - Trip ID for affected resource correlation
  - Timestamp for forensics

### Exceptions Hierarchy

```
AgentException
├── SecurityError
│   ├── TamperingError
│   ├── ExpirationError
│   └── ConstraintViolationError
└── ValidationError
    └── MissingFieldError
```

## Quick Start

### Installation

```bash
uv pip install pytest pytest-cov
```

### Run Tests

```bash
# All tests
pytest agentic-ai-20260325/test_agent_framework.py -v

# Specific test class
pytest agentic-ai-20260325/test_agent_framework.py::TestIntentGateValidation -v

# With coverage
pytest agentic-ai-20260325/test_agent_framework.py --cov
```

## Example Usage

```python
from TDScoringAgent import TDScoringAgent
from TDAgentBase import TDAgentEnum
from intent_gate import create_intent_capsule
from logger import get_logger
import time

# 1. Create agent (logger automatically injected)
agent = TDScoringAgent(
    agent_id=TDAgentEnum.SCORING_AGENT,
    secret_key="dev_secret"
)

# 2. Create signed capsule
capsule = create_intent_capsule(
    trip_id="TRIP-001",
    secret_key="dev_secret",
    expires_at=time.time() + 60
)

# 3. Execute with state
# Logs are automatically emitted as JSON with:
# - correlation_id (uuid for request tracing)
# - duration_ms (execution time)
# - output details
result = agent.run({
    "trip_id": "TRIP-001",
    "trip_context": {
        "trip_pings": [1, 2, 3],
        "harsh_events": 2
    },
    "intent_capsule": capsule
})

# Output includes metadata
print(result["agent_id"])        # "scoring_agent"
print(result["trip_id"])         # "TRIP-001"
print(result["status"])          # "success"
print(result["timestamp"])       # ISO 8601 timestamp
print(result["output"]["trip_score"])  # 90 (100 - 2*5)

# JSON logs output (viewable in ELK/PLG stacks):
# {
#   "timestamp": "2026-03-26T12:34:56.789Z",
#   "action": "intent_gate_validation",
#   "status": "passed",
#   "trip_id": "TRIP-001",
#   "security_event_id": "..."
# }
# {
#   "timestamp": "2026-03-26T12:34:56.834Z",
#   "action": "agent_execution_completed",
#   "status": "success",
#   "agent_id": "scoring_agent",
#   "trip_id": "TRIP-001",
#   "correlation_id": "...",
#   "duration_ms": 45.23
# }
```

## Test Coverage

- **18/18 tests passing** ✅
- Intent Capsule creation & signing
- Intent Gate validation (signature, expiration, tampering)
- Agent execution with valid/invalid capsules
- Scoring logic edge cases
- Output metadata validation

## Design Principles

- **Single Responsibility**: `run()` does only: validate → execute → wrap
- **Security by default**: Intent Gate decorator blocks invalid execution
- **Pure execution**: No broad error handling in agent (let exceptions propagate)
- **Observability first**: Structured JSON logging for ELK/PLG stack integration
- **Distributed tracing**: Correlation IDs for request tracking across services
- **Audit-grade security events**: Unique event IDs with trip/agent context
- **Specific exceptions**: Different error types for different security failures
- **Testable**: No mocks needed; clean boundaries
- **Timing instrumentation**: Automatic duration tracking with LogContext
- **Production ready**: Compatible with major monitoring platforms (ELK, Prometheus/Loki)
