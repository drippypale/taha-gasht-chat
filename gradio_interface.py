import gradio as gr
from agents.workflow import create_workflow
from agents.orchestrator.state import State
from typing import Generator
from dotenv import load_dotenv

# Set environment variables
load_dotenv()

# Initialize workflow
workflow = create_workflow()


def process_message(message: str, history: list) -> Generator[str, None, None]:
    """Process a message and yield response chunks."""

    # Convert Gradio history format to workflow message format
    workflow_messages = []
    for human, assistant in history:
        if human:
            workflow_messages.append(("user", human))
        if assistant:
            workflow_messages.append(("assistant", assistant))

    # Add current message
    workflow_messages.append(("user", message))

    state = State(messages=workflow_messages)

    result = workflow.invoke(state, {"recursion_limit": 100})

    if "messages" in result and result["messages"]:
        last_message = result["messages"][-1]
        response_content = (
            last_message[1] if isinstance(last_message, tuple) else last_message.content
        )
        yield response_content


def create_demo() -> gr.Interface:
    """Create and configure the Gradio demo interface."""

    chat_interface = gr.ChatInterface(
        fn=process_message,
        title="TahaGasht Agency Assistant",
        description="TahaGasht Agency Assistant",
        examples=[
            ["پرواز تهران به مشهد برای فردا"],
            ["جاهای دیدنی دبی کجاست؟"],
        ],
        theme=gr.themes.Soft(),
    )

    return chat_interface


def main():
    demo = create_demo()

    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
    )


if __name__ == "__main__":
    main()
