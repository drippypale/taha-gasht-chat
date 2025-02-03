# TahaGasht Agency Assistant

A conversational AI assistant for TahaGasht travel agency that helps users find flights and get travel information using a multi-agent system built with LangGraph.

<p align="center">
  <img src="https://github.com/user-attachments/assets/746d589c-ce1c-4675-9ecf-8c6527969787" alt="workflow" height=600 />
</p>

## Features

- Flight search capabilities
- Travel blog information retrieval
- Multi-agent system with specialized teams
- Gradio web interface

## Prerequisites

- Python 3.12+
- Poetry for dependency management

## Installation

```bash
poetry install
```

Create a `.env` file in the root directory and add the following environment variables:

```bash
OPENAI_API_KEY=your_openai_api_key
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=your_project_name
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

## Usage

1. Activate the virtual environment:

```bash
poetry shell
```

2. Run the Gradio web interface:

```bash
python gradio_interface.py
```

3. Open your browser and navigate to:

```
http://localhost:7860/
```
