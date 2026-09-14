================================================================================
          AI AGENTIC EVALUATION PLATFORM ("EVAL-AS-A-SERVICE" POC)
================================================================================

OVERVIEW
--------
This POC demonstrates a enterprise-grade AI Agentic Q&A and Evaluation system.
It builds an autonomous LangGraph agent that dynamically routes user queries either to:
1. Text-to-SQL Engine: Querying an E-Commerce SQLite database (sales, orders, products, revenue).
2. Document Vector RAG Engine: Performing semantic similarity search over company policies in ChromaDB.

As the agentic workflow executes, a comprehensive DeepEval (deepeval) metric suite evaluates:
- Tool Selection & Correctness
- Agent LLM Reasoning Coherence (GEval)
- Trajectory Step Efficiency
- Faithfulness & Hallucination Grounding
- Answer Relevancy & Goal Completion
- Contextual Precision

All metric scores, execution traces, and batch benchmark analytics are displayed on an interactive 
2-Tab Streamlit Dashboard.


PROJECT STRUCTURE
-----------------
eval-as-a-service/
│
├── app.py                       # Main 2-Tab Streamlit Dashboard UI
├── requirements.txt             # Python dependencies (groq, deepeval, chromadb, etc.)
├── .env                         # Provisioning environment file for GROQ_API_KEY
├── README.txt                   # Project documentation and quickstart guide
│
├── agent/                       # LangGraph Agentic Workflow
│   ├── graph.py                 # LangGraph state machine (Router -> Tool -> Synthesizer)
│   ├── state.py                 # AgentState TypedDict definition
│   ├── sql_tool.py              # Text-to-SQL generation (Groq Llama-3.3-70B) & SQLite execution
│   └── rag_tool.py              # ChromaDB vector store creation & similarity retrieval
│
├── evals/                       # DeepEval Evaluation Framework
│   ├── evaluator.py             # Agentic Behavior Metrics & Quality Evaluator
│   └── golden_dataset.py        # 10 labeled ground-truth benchmark test cases
│
├── data/                        # Datasets & Persistent Stores
│   ├── ecommerce.db             # SQLite Database (orders, products, customers, items)
│   ├── documents/               # Markdown Policy Docs (Refunds, Warranty, Shipping, Privacy)
│   ├── chroma_db/               # Persistent ChromaDB Vector Collection
│   └── init_db.py               # Database and ChromaDB initialization script
│
└── tests/                       # Test Suite
    └── test_agent_and_evals.py  # Unit & Integration tests


KEY FEATURES
------------
1. Groq LLM API Integration:
   - Uses `llama-3.3-70b-versatile` for ultra-fast intent classification and Text-to-SQL query generation.
   - Automatically loads GROQ_API_KEY from the .env file.

2. ChromaDB Vector Store:
   - Indexes document section chunks into `ecommerce_policies` collection.
   - Computes vector similarity scores for RAG retrieval.

3. DeepEval Agentic Behavior Suite:
   - Tool Selection & Correctness: Validates router tool choice and schema parameters.
   - Agent Reasoning Coherence: GEval metric grading logical clarity of LLM intent reasoning.
   - Step Trajectory Efficiency: Evaluates graph step efficiency without redundant loops.
   - Faithfulness: Verifies 100% grounding on retrieved context/SQL output without hallucination.

4. 2-Tab Streamlit Dashboard:
   - Tab 1: Live Q&A Playground with real-time score cards and LangGraph state trace viewer.
   - Tab 2: Batch Benchmark Analytics runner with aggregate KPIs and Plotly charts.


QUICKSTART INSTRUCTIONS
-----------------------

1. Environment Setup:
   Ensure Python 3.10+ is installed. Create and activate a virtual environment:
   $ python3 -m venv venv
   $ source venv/bin/activate    # On macOS/Linux
   $ pip install -r requirements.txt

2. Provision Groq API Key:
   Open the `.env` file in the project root and add your Groq API key:
   GROQ_API_KEY=gsk_your_actual_groq_key_here

3. Initialize Database & ChromaDB Vector Store:
   $ PYTHONPATH=. python3 data/init_db.py

4. Run the Streamlit Dashboard:
   $ streamlit run app.py
   Access the UI at: http://localhost:8501

5. Run Automated Unit Tests:
   $ python -m unittest tests/test_agent_and_evals.py


REQUIREMENTS
------------
streamlit >= 1.30.0
langgraph >= 0.0.20
groq >= 0.15.0
chromadb >= 0.4.22
deepeval >= 0.20.0
pandas >= 2.0.0
plotly >= 5.18.0
python-dotenv >= 1.0.0

================================================================================
