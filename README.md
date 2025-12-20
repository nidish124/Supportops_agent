# SupportOps Agent

**SupportOps Agent** is an intelligent, autonomous system designed to streamline technical support operations. Leveraging the power of Large Language Models (LLMs) and agentic workflows, it automates the triage process, runs diagnostics, and executes safe remediation actions for support tickets.

## 🚀 Features

- **Automated Triage**: Analyzes incoming support tickets to determine severity, category, and required actions using **LangChain** and **OpenAI**.
- **Intelligent Diagnostics**: Connects to product APIs and databases (MongoDB) to gather context and verify reported issues.
- **Safe Action Execution**: Capable of executing predefined safe actions (e.g., config resets, restarting services) to resolve common problems automatically.
- **Integration Ready**: Built with **FastAPI** for easy integration into existing support platforms (Slack, Jira, etc.).
- **Containerized**: Fully Dockerized for consistent deployment across environments.

## 🛠️ Tech Stack

- **Core**: Python 3.12+
- **API Framework**: FastAPI
- **AI/LLM**: LangChain, LangGraph, OpenAI GPT-4
- **Database**: MongoDB (via PyMongo)
- **Containerization**: Docker
- **Testing**: Pytest

## 📂 Project Structure

```bash
Supportops_agent/
├── app/
│   ├── graph/          # LangGraph workflows for agent logic
│   ├── llm/            # LLM interaction handlers
│   ├── tools/          # Custom tools for diagnostics and actions
│   ├── db/             # Database connection and queries
│   ├── schemas.py      # Pydantic models for data validation
│   └── main.py         # FastAPI application entry point
├── tests/              # Unit and integration tests
├── Dockerfile          # Docker build configuration
├── pyproject.toml      # Project dependencies and configuration
└── .env.example        # Example environment variables
```

## ⚡ Getting Started

### Prerequisites

- Python 3.12 or higher
- Docker (optional, for containerized execution)
- OpenAI API Key
- MongoDB URI (or use the mock setup for testing)

### Local Development Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/nidish124/Supportops_agent.git
    cd Supportops_agent
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # macOS/Linux
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    # OR using uv/pip tools if applicable based on pyproject.toml
    pip install .
    ```

4.  **Configure Environment:**
    Create a `.env` file in the root directory (copy from default or set manually):
    ```env
    OPENAI_API_KEY=your_openai_api_key
    MONGO_URI=mongodb://localhost:27017/supportops
    GITHUB_TOKEN=your_github_pat  # Optional: for GitHub integration features
    ```

### ▶️ Running the Application

**Using Uvicorn (Local):**

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.
Explore the interactive API docs at `http://localhost:8000/docs`.

**Using Docker:**

```bash
docker build -t supportops-agent .
docker run -p 8000:8000 --env-file .env supportops-agent
```

## 🧪 Testing

Run natural language tests and unit tests using `pytest`:

```bash
pytest
```

## 🛡️ License

This project is licensed under the MIT License.
