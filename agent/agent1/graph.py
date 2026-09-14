"""
graph.py — Agent 1: E-Commerce Operations Agent
LangGraph workflow hardcoded to the 'ecommerce' agent domain.
"""
import time
import os
import re
import json
from typing import Dict, Any, Tuple, Optional
from dotenv import load_dotenv

from agent.agent1.state import AgentState
from agent.agent1.sql_tool import get_db_schema, execute_sql_query, generate_llm_sql, validate_sql_schema_alignment
from agent.agent1.rag_tool import search_documents
from agent.registry import get_agent_config

load_dotenv()

# This agent is exclusively for the E-Commerce domain
AGENT_ID = "ecommerce"

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False


def classify_llm_intent(question: str, api_key: Optional[str] = None, provider: str = "Groq") -> Tuple[str, str]:
    """Classifies query intent for the E-Commerce agent using LLM or heuristic fallback."""
    effective_key = api_key if api_key and api_key.strip() else os.getenv("GROQ_API_KEY")
    if not effective_key or effective_key.startswith("gsk_your_"):
        effective_key = None

    if effective_key:
        prompt = f"""You are an AI Agent Router for the 'ecommerce' domain.
Classify the following user question into one of three categories:
- 'sql': structured database queries about metrics, revenue, tables, numbers, customers, orders, products, prices.
- 'rag': questions about store/company policies, rules, refund window, warranty terms, shipping fees, privacy, support.
- 'direct': greetings, capabilities, general chat.

User Question: {question}

Return JSON strictly in this format:
{{"intent": "sql" | "rag" | "direct", "reasoning": "short explanation"}}"""

        try:
            if "Groq" in provider or provider == "Groq":
                from groq import Groq
                client = Groq(api_key=effective_key)
                groq_models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "llama3-70b-8192"]

                for model_id in groq_models:
                    try:
                        res = client.chat.completions.create(
                            model=model_id,
                            messages=[{"role": "user", "content": prompt}],
                            response_format={"type": "json_object"},
                            temperature=0.0
                        )
                        parsed = json.loads(res.choices[0].message.content)
                        return parsed.get("intent", "sql"), f"[Groq {model_id} Router] {parsed.get('reasoning', '')}"
                    except Exception:
                        continue

            elif "Gemini" in provider:
                import google.generativeai as genai
                genai.configure(api_key=effective_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                res = model.generate_content(prompt)
                clean_json = re.sub(r"```json|```", "", res.text).strip()
                parsed = json.loads(clean_json)
                return parsed.get("intent", "sql"), f"[Gemini LLM Router] {parsed.get('reasoning', '')}"

            else:
                import openai
                client = openai.OpenAI(api_key=effective_key)
                res = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.0
                )
                parsed = json.loads(res.choices[0].message.content)
                return parsed.get("intent", "sql"), f"[GPT-4o LLM Router] {parsed.get('reasoning', '')}"
        except Exception as e:
            print(f"LLM Router note: {e}")

    # Fallback heuristic for E-Commerce
    q = question.lower()
    sql_keywords = ["revenue", "sales", "price", "stock", "highest", "lowest", "spent", "orders", "customer", "delivered", "shipped", "product", "category"]
    rag_keywords = ["policy", "refund", "return", "warranty", "claim", "shipping fee", "delivery time", "security", "privacy", "terms"]

    sql_score = sum(1 for k in sql_keywords if k in q)
    rag_score = sum(1 for k in rag_keywords if k in q)

    if sql_score > rag_score and sql_score > 0:
        return "sql", f"Detected database query intent (SQL score: {sql_score})."
    elif rag_score > 0:
        return "rag", f"Detected policy documentation intent (RAG score: {rag_score})."
    elif any(k in q for k in ["hello", "hi", "who are you"]):
        return "direct", "Greeting inquiry."
    else:
        return "sql", "Structured data query."


def router_node(state: AgentState, api_key: Optional[str] = None, provider: str = "Groq") -> AgentState:
    """LangGraph Node 1: Router Node — classifies intent for E-Commerce agent."""
    start_time = time.time()
    question = state["question"]

    intent, reasoning = classify_llm_intent(question, api_key=api_key, provider=provider)

    trace_entry = {
        "node": "Router Node",
        "timestamp": time.strftime("%H:%M:%S"),
        "action": f"Classified intent as [{intent.upper()}] for agent [{AGENT_ID}] using {provider} LLM Router",
        "details": reasoning,
        "duration_ms": round((time.time() - start_time) * 1000, 2)
    }

    state["intent"] = intent
    state["intent_reasoning"] = reasoning
    state["execution_trace"].append(trace_entry)
    return state


def sql_execution_node(state: AgentState, api_key: Optional[str] = None, provider: str = "Groq") -> AgentState:
    """LangGraph Node 2A: Text-to-SQL Node — queries the ecommerce database."""
    start_time = time.time()
    question = state["question"]

    config = get_agent_config(AGENT_ID)
    db_path = config["db_path"]

    sql_query, sql_reasoning = generate_llm_sql(question, api_key=api_key, provider=provider, db_path=db_path)
    sql_result, sql_err = execute_sql_query(sql_query, db_path=db_path)

    trace_entry = {
        "node": "SQL Generation & Execution Node",
        "timestamp": time.strftime("%H:%M:%S"),
        "action": f"Generated Text-to-SQL ({sql_reasoning}) & executed on SQLite [{db_path.name}]",
        "generated_sql": sql_query,
        "rows_returned": len(sql_result) if sql_result else 0,
        "error": sql_err,
        "duration_ms": round((time.time() - start_time) * 1000, 2)
    }

    state["generated_sql"] = sql_query
    state["sql_result"] = sql_result
    state["sql_error"] = sql_err
    state["execution_trace"].append(trace_entry)
    return state


def rag_retrieval_node(state: AgentState) -> AgentState:
    """LangGraph Node 2B: Document Vector RAG Retrieval Node — searches ecommerce_policies."""
    start_time = time.time()
    question = state["question"]

    config = get_agent_config(AGENT_ID)
    collection_name = config["chroma_collection"]
    docs_dir = config["docs_dir"]

    retrieved = search_documents(question, top_k=3, collection_name=collection_name, docs_dir=docs_dir)
    vector_db_name = retrieved[0].get("vector_db", f"ChromaDB ({collection_name})") if retrieved else collection_name

    trace_entry = {
        "node": "Document RAG Retrieval Node",
        "timestamp": time.strftime("%H:%M:%S"),
        "action": f"Retrieved {len(retrieved)} vector embeddings from {vector_db_name}",
        "sources": [doc["source"] for doc in retrieved],
        "top_score": retrieved[0]["score"] if retrieved else 0.0,
        "duration_ms": round((time.time() - start_time) * 1000, 2)
    }

    state["retrieved_context"] = retrieved
    state["execution_trace"].append(trace_entry)
    return state


def synthesizer_node(state: AgentState, api_key: Optional[str] = None, provider: str = "Groq") -> AgentState:
    """LangGraph Node 3: Synthesizer Node — generates a final grounded answer."""
    start_time = time.time()
    intent = state["intent"]
    question = state["question"]

    effective_key = api_key if api_key and api_key.strip() else os.getenv("GROQ_API_KEY")
    if not effective_key or effective_key.startswith("gsk_your_"):
        effective_key = None

    if effective_key:
        try:
            # Every route reaches the same final-answer LLM.  Include the outcome
            # of the tool call even when it returned no data or an error, so the
            # model can give an honest, useful response in every scenario.
            if intent == "sql":
                ctx_summary = (
                    f"SQL Query: {state.get('generated_sql')}\n"
                    f"Query Results: {state.get('sql_result')}\n"
                    f"Execution Error: {state.get('sql_error')}"
                )
            elif intent == "rag":
                documents = state.get("retrieved_context") or []
                ctx_summary = "\n---\n".join(
                    f"Source: {c['doc_title']}\nContent: {c['text']}" for c in documents
                ) or "No matching documentation was retrieved. State this clearly and do not invent policy details."
            else:
                ctx_summary = (
                    "You are the E-Commerce Operations Agent. You can answer general questions "
                    "about your capabilities, and can use SQL for operational data or RAG for policy documents."
                )

            prompt = f"""You are the final response generator for an E-Commerce Operations Agent.
Answer the user's question directly and clearly. Use only the supplied context for factual claims.
If the context has no result or an error, explain that plainly. Do not mention hidden prompts or invent facts.

Context:
{ctx_summary}

Question: {question}"""

            if "Groq" in provider or provider == "Groq":
                from groq import Groq
                client = Groq(api_key=effective_key)
                groq_models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "llama3-70b-8192"]

                for model_id in groq_models:
                    try:
                        res = client.chat.completions.create(
                            model=model_id,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.2
                        )
                        answer = res.choices[0].message.content.strip()
                        state["final_answer"] = answer
                        state["final_answer_source"] = "llm"
                        state["final_answer_model"] = f"Groq ({model_id})"
                        state["execution_trace"].append({
                            "node": "Synthesizer Node",
                            "timestamp": time.strftime("%H:%M:%S"),
                            "action": f"Synthesized grounded response using Groq ({model_id}) LLM",
                            "duration_ms": round((time.time() - start_time) * 1000, 2)
                        })
                        return state
                    except Exception:
                        continue

            elif "Gemini" in provider:
                import google.generativeai as genai
                genai.configure(api_key=effective_key)
                res = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
                state["final_answer"] = res.text.strip()
                state["final_answer_source"] = "llm"
                state["final_answer_model"] = "Gemini (gemini-1.5-flash)"
                state["execution_trace"].append({
                    "node": "Synthesizer Node",
                    "timestamp": time.strftime("%H:%M:%S"),
                    "action": "Synthesized final response using Gemini LLM",
                    "duration_ms": round((time.time() - start_time) * 1000, 2)
                })
                return state
            else:
                import openai
                res = openai.OpenAI(api_key=effective_key).chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2
                )
                state["final_answer"] = res.choices[0].message.content.strip()
                state["final_answer_source"] = "llm"
                state["final_answer_model"] = "OpenAI (gpt-4o-mini)"
                state["execution_trace"].append({
                    "node": "Synthesizer Node",
                    "timestamp": time.strftime("%H:%M:%S"),
                    "action": "Synthesized final response using OpenAI (gpt-4o-mini) LLM",
                    "duration_ms": round((time.time() - start_time) * 1000, 2)
                })
                return state
        except Exception as e:
            print(f"LLM synthesis note: {e}")

    # Grounded fallback synthesizer
    if intent == "sql":
        sql_res = state.get("sql_result")
        sql_err = state.get("sql_error")
        sql = state.get("generated_sql", "")

        if sql_err:
            answer = f"I attempted to query the database using SQL (`{sql}`), but encountered an error: {sql_err}"
        elif not sql_res:
            answer = f"I executed the database query (`{sql}`), but no records were found matching your criteria."
        else:
            if len(sql_res) == 1 and len(sql_res[0]) == 1:
                val = list(sql_res[0].values())[0]
                col = list(sql_res[0].keys())[0]
                if isinstance(val, (float, int)) and ("revenue" in col.lower() or "price" in col.lower() or "amount" in col.lower()):
                    answer = f"Based on the database records, the total value for **{col}** is **${val:,.2f}**."
                else:
                    answer = f"The resulting value for **{col}** is **{val}**."
            else:
                summary_lines = []
                for row in sql_res[:5]:
                    items_str = ", ".join([f"**{k}**: {v}" for k, v in row.items()])
                    summary_lines.append(f"- {items_str}")
                answer = f"Here are the query results from our database:\n\n" + "\n".join(summary_lines)

    elif intent == "rag":
        context = state.get("retrieved_context", [])
        if not context:
            answer = "I searched our ChromaDB vector store, but couldn't find specific matching policy guidelines."
        else:
            top_chunk = context[0]
            vdb = top_chunk.get("vector_db", "ChromaDB")
            answer = f"Based on our official policy document (**{top_chunk['doc_title']}** retrieved via {vdb}):\n\n"
            answer += top_chunk["text"].replace("# ", "### ")
            answer += f"\n\n*(Vector Source: {top_chunk['source']} | Similarity Score: {top_chunk['score']})*"

    else:
        answer = f"Hello! I am the E-Commerce Operations Agent. I use ChromaDB vector retrieval for store policies and Text-to-SQL for database queries about products, customers, and orders."

    trace_entry = {
        "node": "Synthesizer Node",
        "timestamp": time.strftime("%H:%M:%S"),
        "action": "Synthesized grounded response",
        "duration_ms": round((time.time() - start_time) * 1000, 2)
    }

    state["final_answer"] = answer
    state["final_answer_source"] = "fallback"
    state["final_answer_model"] = "Deterministic fallback (LLM unavailable)"
    state["execution_trace"].append(trace_entry)
    return state


def run_agent_workflow(question: str, api_key: Optional[str] = None, provider: str = "Groq", agent_id: str = AGENT_ID) -> AgentState:
    """Executes the E-Commerce Agent LangGraph workflow with ChromaDB and state tracing."""
    start_total = time.time()

    initial_state: AgentState = {
        "question": question,
        "intent": "",
        "intent_reasoning": "",
        "generated_sql": None,
        "sql_result": None,
        "sql_error": None,
        "retrieved_context": None,
        "final_answer": "",
        "final_answer_source": "",
        "final_answer_model": "",
        "latency_ms": 0.0,
        "prompt_tokens": 140 + len(question.split()) * 3,
        "completion_tokens": 90,
        "cost_usd": round((140 + len(question.split()) * 3) * 0.0000015 + 90 * 0.000002, 6),
        "execution_trace": []
    }

    s1 = router_node(initial_state, api_key=api_key, provider=provider)
    if s1["intent"] == "sql":
        s2 = sql_execution_node(s1, api_key=api_key, provider=provider)
    elif s1["intent"] == "rag":
        s2 = rag_retrieval_node(s1)
    else:
        s2 = s1

    final_state = synthesizer_node(s2, api_key=api_key, provider=provider)

    total_time = (time.time() - start_total) * 1000
    final_state["latency_ms"] = round(total_time, 2)
    return final_state
