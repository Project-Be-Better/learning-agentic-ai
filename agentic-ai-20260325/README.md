# Run all tests with verbose output
pytest agentic-ai-20260325/test_agent_framework.py -v

# Run with coverage report
pytest agentic-ai-20260325/test_agent_framework.py --cov=agentic-ai-20260325

# Run specific test class
pytest agentic-ai-20260325/test_agent_framework.py::TestIntentGateValidation -v