from typing import Literal
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from agents.orchestrator.state import State


def generator_node(state: State) -> Command[Literal["__end__"]]:
    llm = ChatOpenAI(model="gpt-4o")

    generator_agent = create_react_agent(
        model=llm,
        tools=[],
        prompt="""You are a generator agent. Your task is to generate the proper response
        based on the user's query, and the provided context.
        If the error is not None, generate proper error messages along with proper guide 
        to the user.
        If error is None, based on the user's task which is either flight_search or blog_info,
        use the proper context (flight_results or blog_results) to generate the response.
        
        Always use the user's initial query language to generate the response.""",
    )
    response = generator_agent.invoke(state)

    return Command(
        update={
            "messages": [
                AIMessage(
                    content=response["messages"][-1].content, name="Generator-Agent"
                )
            ],
            "error": None,  # error processed by generator
            "next_step": None,
        },
        goto="__end__",
    )
