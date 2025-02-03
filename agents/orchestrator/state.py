from typing import Annotated, Sequence, TypedDict, Union
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from langgraph.managed import IsLastStep, RemainingSteps
from langgraph.prebuilt.chat_agent_executor import StructuredResponse


class State(TypedDict):
    """State definition for the multi-agent system"""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    is_last_step: IsLastStep
    remaining_steps: RemainingSteps
    structured_response: StructuredResponse

    task_history: Annotated[Sequence[str], "History of tasks performed"]
    flight_results: Annotated[
        Union[Sequence[dict], None], "Results from flight queries"
    ]
    blog_results: Annotated[Union[Sequence[str], None], "Results from blog queries"]
    error: Annotated[Union[str, None], "Error message"]
    next_step: Annotated[Union[str, None], "Next step in the conversation"]
