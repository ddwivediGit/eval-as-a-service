# ⚡ AI Agentic Evaluation Platform ("Eval-as-a-Service" POC)

An enterprise POC showcasing **AI Agentic Evaluation Functionality** for a Q&A agent routing between **Text-to-SQL** (SQLite) and **Document RAG** (ChromaDB Vector Store) powered by **Groq Llama-3.3-70B API** and evaluated via **DeepEval (`deepeval`)**.

---

## 🏗️ System Architecture

```
User Prompt ──► Streamlit UI ──► LangGraph State Machine
                                      │
                   ┌──────────────────┴──────────────────┐
                   ▼                                     ▼
        Text-to-SQL Node (SQLite)               ChromaDB Vector RAG Node
                   │                                     │
                   └──────────────────┬──────────────────┘
                                      ▼
                             Synthesizer Node
                                      │
                                      ▼
                        DeepEval Evaluation Engine
       (Tool Selection, Reasoning Coherence, Faithfulness, Relevancy)
```

---

## 📁 Repository Structure

```
eval-as-a-service/
├── app.py                       # 2-Tab Streamlit Dashboard UI
├── requirements.txt             # Project dependencies
├── .env.example                 # Safe local environment-variable template
├── README.txt                   # Plain text guide
├── README.md                    # Markdown documentation
│
├── agent/                       # LangGraph Agent Engine
│   ├── graph.py                 # LangGraph State Machine (Router -> Tool -> Synthesizer)
│   ├── state.py                 # AgentState TypedDict
│   ├── sql_tool.py              # Groq Text-to-SQL Generator & SQLite Executor
│   └── rag_tool.py              # ChromaDB Vector Store & Retriever
│
├── evals/                       # DeepEval Metric Suite
│   ├── evaluator.py             # Agentic Behavior & Quality Evaluator
│   └── golden_dataset.py        # 10 Ground-Truth Golden Test Cases
│
├── data/                        # Data & Persistent Vector Storage
│   ├── ecommerce.db             # SQLite E-Commerce Database
│   ├── documents/               # Policy Markdown Documents
│   ├── chroma_db/               # Persistent ChromaDB Collection
│   └── init_db.py               # Database & Vector Indexing Script
│
└── tests/                       # Unit Test Suite
    └── test_agent_and_evals.py  # Unit & Integration Tests
```

---

## 🚀 Quickstart Guide

### 1. Installation
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Groq API Key
Add your key to `.env`:
```ini
GROQ_API_KEY=gsk_your_actual_groq_key_here
```

### 3. Initialize Databases
```bash
PYTHONPATH=. python3 data/init_db.py
```

### 4. Run Dashboard
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your web browser.

### 5. Run Test Suite
```bash
python -m unittest tests/test_agent_and_evals.py
```

---

## Deploy to Streamlit Community Cloud

1. Push this project to a GitHub repository. The included `.gitignore` keeps
   `.env`, local virtual environments, and ChromaDB runtime files out of Git.
2. In [Streamlit Community Cloud](https://share.streamlit.io/), select **Create app**,
   choose the repository and branch, and set the main file path to `app.py`.
3. Before deploying, open **Advanced settings → Secrets** and add the provider
   key you plan to use:

   ```toml
   GROQ_API_KEY = "gsk_your_key_here"
   # OPENAI_API_KEY = "..."
   # GEMINI_API_KEY = "..."
   ```

   Streamlit keeps these values server-side. Never add API keys to GitHub or
   paste them into source files.
4. Deploy. On first use, the app rebuilds its ChromaDB index from the tracked
   Markdown documents. Community Cloud storage is ephemeral, so that index may
   rebuild after a restart.

The sidebar also accepts a password-masked per-session key for demos. That key
is sent to the running app to make the provider request and is not written to
the repository; server-side Streamlit secrets are safer for a shared deployment.
