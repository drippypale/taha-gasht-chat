from typing import Literal
from typing_extensions import TypedDict
from langchain_core.language_models import BaseChatModel
from langgraph.graph import END
from langgraph.prebuilt import create_react_agent
from agents.orchestrator.state import State
from langgraph.types import Command


def create_supervisor(llm: BaseChatModel) -> str:
    """Create a supervisor agent to orchestrate between teams"""

    system_prompt = """You are the Supervisor in a multi-agent system, responsible for orchestrating the workflow and ensuring that each query is handled by the correct specialized module. Your duties include:

1. **Module Coordination:**
   - **flight_team:** Handles flight search-related queries. Any flight-specific context should be stored in `flight_results`.
   - **blog_team:** Manages travel information and tourism-related questions. Relevant context should be stored in `blog_results`.
   - **non_relevent:** Processes queries that do not pertain to flights or travel topics.

2. **Workflow Management:**
   - **Routing:** Evaluate each incoming query to determine which module it best fits. Direct the query accordingly:
     - If the query is flight-related, send it to the `flight_team`.
     - If the query is about travel or tourism, forward it to the `blog_team`.
     - If the query does not relate to these topics, route it to `non_relevent`.
     
Your role is to ensure that each query is processed efficiently by coordinating between these specialized modules and managing the overall conversation flow.
"""

    class Router(TypedDict):
        next_step: Literal["flight_team", "blog_team", "generator"]

    def supervisor_node(
        state: State,
    ) -> Command[Literal["flight_team", "blog_team", "generator"]]:
        supervisor_agent = create_react_agent(
            model=llm,
            tools=[],
            prompt=system_prompt,
            response_format=Router,
        )
        try:
            print(state)
            response = supervisor_agent.invoke(state)["structured_response"]
        except Exception as e:
            return Command(update={"error": str(e)}, goto="generator")

        next_step = response.get("next_step", "FINISH")

        error = None
        if next_step == "non_relevant":
            error = "The user asked a question that is not relevant to the system."
            next_step = "generator"
        elif next_step == "FINISH":
            next_step = END

        return Command(goto=next_step, update={"next_step": next_step, "error": error})

    return supervisor_node
