from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START
from agents.orchestrator.state import State
from agents.orchestrator.supervisor import create_supervisor
from agents.flight_team.agents import (
    flight_team_node,
    flight_team_search_node,
    flight_team_prompt_node,
)
from agents.blog_team.agents import (
    blog_team_node,
    blog_team_prompt_node,
    blog_team_rag_node,
)
from agents.generator.agents import generator_node


def create_workflow():
    llm = ChatOpenAI(model="gpt-4o")

    workflow = StateGraph(State)

    supervisor = create_supervisor(llm)

    # Add nodes
    workflow.add_node("supervisor", supervisor)

    workflow.add_node("flight_team", flight_team_node)
    workflow.add_node("flight_team_prompt", flight_team_prompt_node)
    workflow.add_node("flight_team_search", flight_team_search_node)

    workflow.add_node("blog_team", blog_team_node)
    workflow.add_node("blog_team_prompt", blog_team_prompt_node)
    workflow.add_node("blog_team_rag", blog_team_rag_node)

    workflow.add_node("generator", generator_node)

    # Add edges
    workflow.add_edge(START, "supervisor")

    return workflow.compile()
