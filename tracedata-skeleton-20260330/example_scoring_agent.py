from pathlib import Path

from adapters import OpenAIModel, load_llm
from agents.scoring.agent import ScoringAgent


def main() -> None:
    project_root = Path(__file__).resolve().parent
    print("Using project root:", project_root)

    config = load_llm(OpenAIModel.GPT_4O)
    llm = config.adapter.get_chat_model()

    scoring_agent = ScoringAgent(llm=llm)
    print(f"Loaded provider={config.provider}, model={config.model}")
    print(scoring_agent)

    trip_id = "TRIP-T12345-2026-03-07-08:00"
    result = scoring_agent.invoke_with_trip(trip_id)

    final_msg = result["messages"][-1]
    print("\nFinal response:\n")
    print(final_msg.content if hasattr(final_msg, "content") else final_msg)


if __name__ == "__main__":
    main()
