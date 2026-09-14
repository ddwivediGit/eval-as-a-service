import sqlite3
import re
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dotenv import load_dotenv

load_dotenv()

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "ecommerce.db"


def get_db_schema(db_path: Optional[Path] = None) -> str:
    """Returns formatted schema of all tables in the specified SQLite database."""
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
    """Executes a SQL query against target database and returns (list of dict rows, error_message)."""
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


def validate_sql_schema_alignment(sql: str, agent_id: str = "ecommerce") -> Tuple[bool, List[str]]:
    """Validates if tables and columns in generated SQL exist in schema for agent."""
    from agent.registry import get_agent_config
    config = get_agent_config(agent_id)
    known_tables = config.get("known_tables", ["products", "customers", "orders", "order_items", "subscriptions", "invoices", "usage_metrics", "plans"])
    
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
    """Generates Text-to-SQL query using Groq, Gemini, or OpenAI LLM API if key available."""
    effective_key = api_key if api_key and api_key.strip() else os.getenv("GROQ_API_KEY")
    if not effective_key or effective_key.startswith("gsk_your_"):
        effective_key = None

    schema = get_db_schema(db_path)

    if effective_key:
        system_prompt = f"""You are an expert Text-to-SQL AI Agent for SQLite.
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
    """Generates SQL deterministically based on query domain keywords."""
    q = question.lower()
    
    # Financial SaaS Queries
    if "subscription" in q or "saas" in q or "account" in q or "plan" in q or "invoice" in q:
        if "revenue" in q or "total" in q:
            sql = "SELECT SUM(monthly_fee) as total_monthly_revenue FROM subscriptions WHERE status = 'Active';"
            reasoning = "Query asks for total monthly revenue from active SaaS subscriptions."
        elif "usage" in q or "api call" in q or "highest" in q:
            sql = "SELECT account_name, api_calls_count, storage_used_gb FROM usage_metrics ORDER BY api_calls_count DESC LIMIT 3;"
            reasoning = "Query requests top accounts by API call volume."
        elif "overdue" in q or "invoice" in q:
            sql = "SELECT account_name, invoice_date, amount, payment_status FROM invoices WHERE payment_status = 'Overdue';"
            reasoning = "Query filters overdue customer invoices."
        else:
            sql = "SELECT plan_name, COUNT(*) as active_subscribers FROM subscriptions WHERE status = 'Active' GROUP BY plan_name;"
            reasoning = "Query groups active subscribers by SaaS plan."
            
    # E-Commerce Queries
    elif "electronics" in q or "category" in q or "revenue" in q or "spent" in q:
        if "electronics" in q:
            sql = "SELECT SUM(total_amount) as total_revenue FROM orders WHERE order_id IN (SELECT order_id FROM order_items JOIN products ON order_items.product_id = products.product_id WHERE products.category = 'Electronics');"
            reasoning = "Query requests aggregated revenue for Electronics category products."
        elif "top customer" in q or "most spent" in q:
            sql = "SELECT name, email, membership_tier, total_spent FROM customers ORDER BY total_spent DESC LIMIT 3;"
            reasoning = "Query asks for top customers sorted by total spending."
        else:
            sql = "SELECT SUM(total_amount) as total_revenue, COUNT(order_id) as total_orders FROM orders WHERE status = 'Delivered';"
            reasoning = "Query asks for total revenue from delivered orders."
    else:
        sql = "SELECT * FROM subscriptions LIMIT 5;" if "subscriptions" in schema else "SELECT name, price FROM products LIMIT 5;"
        reasoning = "Default table query."
        
    return sql, reasoning
