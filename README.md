# Delishes Chatbot

An AI-powered data analytics chatbot built for **Delishes**; a fictional social media platform where food creators share recipes, cooking videos, and exclusive content with subscribers.

This project demonstrates end-to-end AI agent development: from LangGraph orchestration and dynamic tool use, to real-time streaming UI with Streamlit.

## AI Skills Demonstrated

| Skill | How It's Used |
|---|---|
| **LangGraph Agent Orchestration** | StateGraph with conditional routing between chatbot and tool nodes |
| **Tool Use / Function Calling** | Agent dynamically calls SQL query and visualization tools based on user intent |
| **SQL Generation** | LLM writes and executes PostgreSQL queries against a live database |
| **Dynamic Visualization** | Agent generates Plotly code on-the-fly, executed server-side and rendered in the UI |
| **Streaming with Intermediate State** | Real-time streaming separates thinking/tool calls (in dropdowns) from the final response |
| **Stateful Conversations** | LangGraph checkpointer maintains conversation memory across turns |
| **Custom State Management** | Pydantic state model with custom reducers (e.g., chart_json always takes the latest) |

## Architecture

```
User ──► Streamlit UI ──► LangGraph Agent (Scout)
                              │
                    ┌─────────┴──────────┐
                    │                    │
              query_db tool     generate_visualization tool
                    │                    │
              PostgreSQL DB        Plotly (server-side)
              (Supabase)           JSON ──► UI render
```

**Flow:** User asks a question ➜ Scout plans an approach ➜ calls tools (SQL queries, Plotly charts) ➜ returns a synthesized answer. The Streamlit frontend streams this in real-time, showing the agent's thinking process in collapsible dropdowns.

## Tech Stack

- **Agent Framework:** LangGraph + LangChain
- **LLM:** OpenAI GPT-4o-mini
- **Frontend:** Streamlit (real-time streaming chat)
- **Visualization:** Plotly (dynamic chart generation)
- **Database:** PostgreSQL via Supabase
- **ORM:** SQLAlchemy with connection pooling
- **Observability:** LangSmith (optional)
- **Deployment:** Docker + LangGraph CLI + Render (optional)

## Project Structure

```
delishes-chatbot/
├── frontend/
│   └── app.py                 # Streamlit chat interface with streaming
├── scout/
│   ├── graph.py               # LangGraph agent definition (StateGraph, routing)
│   ├── tools.py               # Tool implementations (query_db, generate_visualization)
│   ├── env.py                 # Environment variable loader
│   └── prompts/
│       ├── prompts.py         # System prompt loader
│       └── scout.md           # Scout's system prompt
├── sample_data/               # CSV files for database seeding
│   ├── creators_2023.csv
│   ├── customers_2023.csv
│   └── transactions_2023_2024.csv
├── pyproject.toml             # Project config and dependencies
├── langgraph.json             # LangGraph server configuration
├── Dockerfile                 # Docker build for LangGraph API deployment
└── .env.example               # Environment variable template
```

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- OpenAI API key
- Supabase account (free tier) for the PostgreSQL database

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/delishes-chatbot.git
cd delishes-chatbot

uv venv
uv sync
uv pip install -e .
```

### 2. Configure environment

```bash
cp .env.example .env
```

Fill in your API keys in `.env`:
- `OPENAI_API_KEY` — required
- `SUPABASE_URL` — required (see Database Setup below)

### 3. Set up the database

1. Create a free Supabase project at [supabase.com](https://supabase.com)
2. Save the database password in your `.env` file
3. Copy the **Transaction Pooler** connection string to `SUPABASE_URL` in `.env`
4. Copy the **Session Pooler** connection string to `DATABASE_URI` in `.env` (only needed for deployment)
5. Replace the password placeholder in both connection strings
6. In the Supabase Table Editor, create a new schema called `delishes`
7. Under the `delishes` schema, create three tables by importing the CSVs from `sample_data/`:
   - `creators` (set `id` as primary key)
   - `customers` (set `id` as primary key)
   - `transactions` (set `id` as primary key)

### 4. Run the chatbot

```bash
streamlit run frontend/app.py
```

The chat interface opens in your browser. Try asking Scout:
- *"Show me a preview of the creators table"*
- *"Who are the top 5 creators by total revenue?"*
- *"Create a bar chart of monthly revenue for 2024"*

## Database Schema

The `delishes` schema models a creator economy platform:

- **creators** — Food content creators (chefs, food bloggers)
- **customers** — Subscribers who follow creators and purchase content
- **transactions** — Subscriptions, exclusive content purchases, tips

## Optional: LangSmith Tracing

For observability and debugging, create a free account at [smith.langchain.com](https://smith.langchain.com) and add your API key to `.env`. This enables trace logging of every LLM call, tool invocation, and state transition.

## Optional: Deployment

The project includes a `Dockerfile` and `langgraph.json` for deploying the LangGraph server API:

```bash
# Build the Docker image using LangGraph CLI
langgraph build -t delishes-chatbot
```

Deploy to Render or any Docker-compatible hosting. The LangGraph server exposes a REST API that the frontend (or any client) can call.

## Demo


