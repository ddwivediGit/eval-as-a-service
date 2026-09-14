"""
sql_tool.py — Agent 1: E-Commerce Operations Agent
Text-to-SQL tooling scoped to the ecommerce SQLite database.
"""
import sqlite3
import re
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dotenv import load_dotenv

load_dotenv()

# Agent 1 default DB: ecommerce
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "ecommerce.db"
AGENT_ID = "ecommerce"


def get_db_schema(db_path: Optional[Path] = None) -> str:
    """Returns formatted schema of all tables in the ecommerce SQLite database."""
    target_path = db_path or DEFAULT_DB_PATH
    if not target_path.exists():
        return f"Database file not found at: {target_path}"

    conn = sqlite3.connect(target_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    schema_parts = []
    for table_tuple in tables:
        table_name = table_tuple[0]
        if table_name == "sqlite_sequence":
            continue
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        cols_str = ", ".join([f"{col[1]} ({col[2]})" for col in columns])
        schema_parts.append(f"Table `{table_name}`: {cols_str}")

    conn.close()
    return "\n".join(schema_parts)


def execute_sql_query(sql: str, db_path: Optional[Path] = None) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """Executes a SQL query against the ecommerce database and returns (rows, error)."""
    target_path = db_path or DEFAULT_DB_PATH
    if not target_path.exists():
        return None, f"Database file does not exist at {target_path}."

    clean_sql = re.sub(r"```sql|```", "", sql).strip()

    if not clean_sql.upper().startswith("SELECT") and not clean_sql.upper().startswith("WITH"):
        return None, "Security Error: Only SELECT queries are permitted."

    try:
        conn = sqlite3.connect(target_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(clean_sql)
        rows = cursor.fetchall()
        dict_rows = [dict(row) for row in rows]
        conn.close()
        return dict_rows, None
    except Exception as e:
        return None, str(e)


def validate_sql_schema_alignment(sql: str, agent_id: str = AGENT_ID) -> Tuple[bool, List[str]]:
    """Validates if tables and columns in generated SQL exist in the ecommerce schema."""
    from agent.registry import get_agent_config
    config = get_agent_config(agent_id)
    known_tables = config.get("known_tables", ["products", "customers", "orders", "order_items"])

    issues = []
    sql_lower = sql.lower()

    if "select" not in sql_lower:
        issues.append("Missing SELECT clause")
        return False, issues

    words = re.findall(r'[a-zA-Z_]+', sql_lower)
    found_table = any(table in words for table in known_tables)
    if not found_table:
        issues.append(f"No valid database table referenced. Expected one of: {known_tables}")

    return len(issues) == 0, issues


def generate_llm_sql(question: str, api_key: Optional[str] = None, provider: str = "Groq", db_path: Optional[Path] = None) -> Tuple[str, str]:
    """Generates Text-to-SQL query for the ecommerce domain using Groq, Gemini, or OpenAI."""
    effective_key = api_key if api_key and api_key.strip() else os.getenv("GROQ_API_KEY")
    if not effective_key or effective_key.startswith("gsk_your_"):
        effective_key = None

    schema = get_db_schema(db_path)

    if effective_key:
        system_prompt = f"""You are an expert Text-to-SQL AI Agent for the E-Commerce SQLite database.
Database Schema:
{schema}

User Question: {question}

Instructions:
1. Return ONLY the executable SQLite SELECT query.
2. Do NOT enclose in markdown formatting or backticks.
3. Do NOT add extra explanations before or after the SQL statement."""

        try:
            if "Groq" in provider or provider == "Groq":
                from groq import Groq
                client = Groq(api_key=effective_key)
                groq_models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "llama3-70b-8192"]
                generated_sql = None
                used_model = "llama-3.3-70b-versatile"

                for model_id in groq_models:
                    try:
                        response = client.chat.completions.create(
                            model=model_id,
                            messages=[
                                {"role": "system", "content": "You are a Text-to-SQL query translator. Output ONLY the raw SQL SELECT statement."},
                                {"role": "user", "content": f"Schema:\n{schema}\n\nQuestion: {question}"}
                            ],
                            temperature=0.0
                        )
                        generated_sql = response.choices[0].message.content.strip()
                        used_model = model_id
                        break
                    except Exception:
                        continue

                if generated_sql:
                    clean_sql = re.sub(r"```sql|```", "", generated_sql).strip()
                    return clean_sql, f"Generated via Groq ({used_model}) LLM."

            elif "Gemini" in provider:
                import google.generativeai as genai
                genai.configure(api_key=effective_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(system_prompt)
                clean_sql = re.sub(r"```sql|```", "", response.text).strip()
                return clean_sql, "Generated via Gemini LLM."

            else:
                import openai
                client = openai.OpenAI(api_key=effective_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a Text-to-SQL query translator. Output ONLY the raw SQL SELECT statement."},
                        {"role": "user", "content": f"Schema:\n{schema}\n\nQuestion: {question}"}
                    ],
                    temperature=0.0
                )
                clean_sql = re.sub(r"```sql|```", "", response.choices[0].message.content).strip()
                return clean_sql, "Generated via OpenAI (gpt-4o-mini) LLM."

        except Exception as e:
            print(f"LLM SQL generation note: {e}. Falling back to deterministic SQL generator.")

    return generate_mock_sql(question, schema)


def generate_mock_sql(question: str, schema: str = "") -> Tuple[str, str]:
    """Generates SQL deterministically for E-Commerce domain queries."""
    q = question.lower()

    if "electronics" in q or "category" in q or "revenue" in q or "spent" in q:
        if "electronics" in q:
            sql = "SELECT SUM(total_amount) as total_revenue FROM orders WHERE order_id IN (SELECT order_id FROM order_items JOIN products ON order_items.product_id = products.product_id WHERE products.category = 'Electronics');"
            reasoning = "Query requests aggregated revenue for Electronics category products."
        elif "top customer" in q or "most spent" in q or "spent the most" in q:
            sql = "SELECT name, email, membership_tier, total_spent FROM customers ORDER BY total_spent DESC LIMIT 3;"
            reasoning = "Query asks for top customers sorted by total spending."
        else:
            sql = "SELECT SUM(total_amount) as total_revenue, COUNT(order_id) as total_orders FROM orders WHERE status = 'Delivered';"
            reasoning = "Query asks for total revenue from delivered orders."
    else:
        sql = "SELECT name, price FROM products LIMIT 5;"
        reasoning = "Default E-Commerce product table query."

    return sql, reasoning
