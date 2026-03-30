from pathlib import Path

from adapters import OpenAIModel, load_llm
from agents.examples import ExampleWeatherTrafficAgent


def main() -> None:
    project_root = Path(__file__).resolve().parent

    print("Using project root:", project_root)

    config = load_llm(OpenAIModel.GPT_4O)
    llm = config.adapter.get_chat_model()
    weather_traffic_agent = ExampleWeatherTrafficAgent(llm=llm)

    print(f"Loaded provider={config.provider}, model={config.model}")
    print(weather_traffic_agent)

    query = "I need to drive in Singapore now. Please assess conditions."
    result = weather_traffic_agent.invoke(
        {"messages": [{"role": "user", "content": query}]}
    )

    final_msg = result["messages"][-1]
    print(final_msg.content if hasattr(final_msg, "content") else final_msg)


if __name__ == "__main__":
    main()
