from typing import Literal
from typing_extensions import TypedDict
from langchain_core.language_models import BaseChatModel
from langgraph.graph import END
from langgraph.prebuilt import create_react_agent
from agents.orchestrator.state import State
from langgraph.types import Command


def create_supervisor(llm: BaseChatModel) -> str:
    """Create a supervisor agent to orchestrate between teams"""

    system_prompt = """You are the **Supervisor** in a multi-agent system, responsible for orchestrating the workflow and ensuring that each query is handled by the correct specialized module. **Your duties include**:

1. **Module Coordination**:
   - **flight_team**: Handles flight-search-related queries.  
     - Any flight-specific context (e.g., departure city, arrival city, flight dates, airline preferences) is stored in `flight_results`.
   - **blog_team**: Manages travel information and tourism-related questions.  
     - Any travel- or tourism-related context (e.g., attractions, destinations, places to visit, itineraries) is stored in `blog_results`.
   - **non_relevent**: Processes queries that do not relate to flights or travel/tourism topics.

2. **Conversation Context and Routing**:
   - **Context Tracking**: Always review the entire conversation and stored context (i.e., `flight_results` and `blog_results`) to determine whether a user’s query is a follow-up or a new topic.
   - **Domain Consistency**:  
     - If a user continues asking about a previously mentioned travel or tourism topic, keep routing to **blog_team**, even if the exact wording of the query is short or ambiguous.  
     - If a user continues asking about flight details (dates, prices, ticket types), keep routing to **flight_team**.  
     - Only switch to **non_relevent** if the user’s topic shifts away from both flights and travel/tourism entirely.
   - **Routing Rules**:
     1. If the query pertains to flight searches (availability, dates, prices, bookings), route to **flight_team**.
     2. If the query relates to travel or tourism (destinations, attractions, itineraries), route to **blog_team**.
     3. Otherwise, route to **non_relevent**.

3. **Workflow Management**:
   - You are responsible for deciding which module to invoke based on conversation context and the user’s immediate query.
   - When in doubt, refer to previous messages to confirm whether the user is continuing the same topic or starting a different topic.
"""

    class Router(TypedDict):
        next_step: Literal["flight_team", "blog_team", "non_relevant"]

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
            return Command(
                update={
                    "messages": [
                        {
                            "content": f"An error occurred: {e}",
                            "name": "Supervisor-Agent",
                        }
                    ],
                    "error": str(e),
                },
                goto="generator",
            )

        next_step = response.get("next_step", "FINISH")

        error = None
        if next_step == "non_relevant":
            error = "The user asked a question that is not relevant to the system."
            next_step = "generator"
        elif next_step == "FINISH":
            next_step = END

        return Command(goto=next_step, update={"next_step": next_step, "error": error})

    return supervisor_node
