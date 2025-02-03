from datetime import datetime
import jdatetime
from typing import Literal
from pydantic import BaseModel, Field
from typing_extensions import Optional, TypedDict
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from agents.flight_team.tools import (
    search_available_flights,
    query_flight_database,
)
from agents.orchestrator.state import State
import json


def flight_team_db_node(
    state: State,
) -> Command[Literal["flight_team_search", "generator"]]:
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    class FlightResult(TypedDict):
        airline: str
        date_time: str
        flight_number: str
        last_updated: str

    class FlightNodeResult(BaseModel):
        results: Optional[list[FlightResult]] = Field(
            description="List of flight results found in the database. If no results found, return an empty list."
        )

    # Create the flight database agent
    flight_db_agent = create_react_agent(
        model=llm,
        tools=[query_flight_database],
        prompt=f"""You are a flight database specialist. Your task is to query the flights database 
        to find matching flights. Use SQL queries to search the database.
        
        Here is the flights table schema:
        CREATE TABLE flights (
            airline TEXT NOT NULL,
            departure_datetime TEXT NOT NULL,
            flight_number TEXT NOT NULL,
            origin_code TEXT NOT NULL,
            dest_code TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        
        Today's date is: {datetime.now().strftime("%Y-%m-%d")} or in Jalaali calendar: {jdatetime.datetime.now().strftime("%Y-%m-%d")}
        Your response should be based on the query_flight_database tool function.
        
        If no flights found IN THE DATABASE, return an empty list. DO NOT GENERATE FROM YOUR OWN KNOWLEDGE.
        """,
        state_schema=State,
        response_format=FlightNodeResult,
    )

    try:
        result: FlightNodeResult = flight_db_agent.invoke(state)
        if result["structured_response"]["results"]:
            return Command(
                update={
                    "flight_results": result["structured_response"]["results"],
                    "task_history": ["flight_team_db"],
                    "next_step": None,
                },
                goto="generator",
            )
        else:
            return Command(
                update={
                    "flight_results": [],
                    "task_history": ["flight_team_db"],
                    "next_step": "search",
                },
                goto="flight_team_search",
            )
    except Exception as e:
        return Command(
            update={
                "error": str(e),
                "messages": [
                    HumanMessage(
                        content="An error occurred while querying the database. Please try again."
                    )
                ],
            },
            goto="generator",
        )


def flight_team_search_node(state: State) -> Command[Literal["generator"]]:
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    class FlightResult(TypedDict):
        airline: str
        date_time: str
        flight_number: str
        last_updated: str

    class FlightNodeResult(TypedDict):
        results: list[FlightResult]

    flight_search_agent = create_react_agent(
        model=llm,
        tools=[search_available_flights],
        prompt=f"""You are a flight search specialist. Your task is to search real-time flight 
        availability. 

        Today's date is: {datetime.now().strftime("%Y-%m-%d")} or in Jalaali calendar: {jdatetime.datetime.now().strftime("%Y-%m-%d")}

        Answer ONLY based on the search results. If there is no flight data available, 
        return an empty list.
        """,
        response_format=(
            "Your task is to format the response in the given structure. If there are no results, return an empty list.",
            FlightNodeResult,
        ),
    )

    try:
        result: FlightNodeResult = flight_search_agent.invoke(state)
    except Exception as e:
        return Command(
            update={"error": str(e)},
            goto="generator",
        )

    return Command(
        update={
            "messages": [
                AIMessage(
                    content=f"Here are the available flights:\n{json.dumps(result['structured_response']['results'], indent=2)}",
                    name="Flight-Team-Agent",
                )
            ],
            "flight_results": result["structured_response"]["results"],
            "task_history": ["flight_team_search"],
            "next_step": None,
        },
        goto="generator",
    )


def flight_team_node(state: State) -> Command[Literal["flight_team_prompt"]]:
    """Entry point node for flight team that routes to appropriate sub-nodes"""

    return Command(
        update={
            "task_history": ["flight_team"],
        },
        goto="flight_team_prompt",
    )


def flight_team_prompt_node(state: State) -> Command[Literal["flight_team_search"]]:
    """Process and refine the user query for flight team"""
    llm = ChatOpenAI(model="gpt-4o")

    prompt_processor = create_react_agent(
        model=llm,
        tools=[],
        prompt="""You are a flight query processor. Your task is to:
        1. Analyze the conversation history and the latest query
        2. Generate a clear, structured query focusing on flight search parameters
        3. Keep the language consistent with the user's original query
        4. Ensure all necessary flight information is preserved:
           - Origin and destination cities
           - Dates
           - Number of passengers
           - Class preferences (if specified)
        5. Remove conversational elements while maintaining essential information
        
        Format the query to be precise and search-friendly.""",
    )

    result = prompt_processor.invoke(state)
    processed_query = result["messages"][-1].content

    return Command(
        update={
            "messages": [
                HumanMessage(content=processed_query, name="Flight-Team-Agent")
            ],
            "task_history": ["flight_team_prompt"],
        },
        goto="flight_team_search",
    )
