from typing import Literal
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.types import Command
from langchain.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from agents.orchestrator.state import State
from langgraph.prebuilt import create_react_agent


def initialize_rag_chain():
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    vectorstore = Chroma(
        collection_name="blog_posts",
        embedding_function=embeddings,
        persist_directory="./blog_posts_vectorstore",
    )

    template = """You are an assistant for question-answering tasks. 
    Use the following pieces of retrieved context to answer the question. 
    For each sentence that you generate, provide the url of the blog post that you used to generate the sentence (cite the source).
    If you don't know the answer, just say that you don't know. 
    Use three sentences maximum and keep the answer concise.
    Question: {question}
    Context: {context}
    Answer:"""

    prompt = ChatPromptTemplate([SystemMessagePromptTemplate.from_template(template)])

    return vectorstore, prompt


def blog_team_rag_node(state: State) -> Command[Literal["generator"]]:
    llm = ChatOpenAI(model="gpt-4o")
    vectorstore, prompt = initialize_rag_chain()

    query = state["messages"][-1].content
    retrieved_docs = vectorstore.similarity_search(query)

    context = "\n\n".join(
        f"URL: {doc.metadata['url']}\nContent: {doc.page_content}"
        for doc in retrieved_docs
    )

    messages = prompt.invoke({"question": query, "context": context})

    response = llm.invoke(messages)

    blog_results = response.content

    return Command(
        update={
            "messages": [AIMessage(content=blog_results, name="Blog-Team-Agent")],
            "blog_results": blog_results,
            "next_step": None,
        },
        goto="generator",
    )


def blog_team_node(state: State) -> Command[Literal["blog_team_prompt"]]:
    """Entry point node for blog team that routes to appropriate sub-nodes"""

    return Command(
        update={
            "task_history": ["blog_team"],
        },
        goto="blog_team_prompt",
    )


def blog_team_prompt_node(state: State) -> Command[Literal["blog_team_rag"]]:
    """Process and refine the user query for blog team"""
    llm = ChatOpenAI(model="gpt-4o")

    prompt_processor = create_react_agent(
        model=llm,
        tools=[],
        prompt="""You are a travel information query processor. Your task is to:
        1. Analyze the conversation history and the latest query
        2. Generate a clear, focused query that will help find relevant travel blog information
        3. Keep the language consistent with the user's original query
        4. Maintain key location names and specific requirements
        5. Remove any irrelevant information or conversational elements
        
        Format the query to be concise but complete.""",
    )

    result = prompt_processor.invoke(state)
    processed_query = result["messages"][-1].content

    return Command(
        update={
            "messages": [HumanMessage(content=processed_query, name="Blog-Team-Agent")],
            "task_history": ["blog_team_prompt"],
        },
        goto="blog_team_rag",
    )
