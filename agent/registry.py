from pathlib import Path
from typing import Dict, Any, List

BASE_DIR = Path(__file__).resolve().parent.parent / "data"

AGENT_REGISTRY: Dict[str, Dict[str, Any]] = {
    "ecommerce": {
        "id": "ecommerce",
        "name": "E-Commerce Operations Agent",
        "icon": "🛒",
        "db_path": BASE_DIR / "ecommerce.db",
        "chroma_collection": "ecommerce_policies",
        "docs_dir": BASE_DIR / "documents",
        "known_tables": ["products", "customers", "orders", "order_items"],
        "presets": [
            {"label": "💵 Total Electronics Revenue", "query": "What is the total revenue for Electronics category products?"},
            {"label": "👑 Top Spending Customers", "query": "Which customer has spent the most money overall?"},
            {"label": "📦 Opened Item Return Policy", "query": "What is our store's refund policy for opened electronics?"},
            {"label": "🛡️ 1-Year Warranty Coverage", "query": "What hardware issues are covered under the 1-year warranty?"}
        ]
    },
    "financial_saas": {
        "id": "financial_saas",
        "name": "Financial & SaaS Subscription Agent",
        "icon": "💳",
        "db_path": BASE_DIR / "financial_saas.db",
        "chroma_collection": "financial_policies",
        "docs_dir": BASE_DIR / "financial_documents",
        "known_tables": ["subscriptions", "invoices", "usage_metrics", "plans"],
        "presets": [
            {"label": "💳 Total Active Subscription Revenue", "query": "What is the total monthly revenue from active subscriptions?"},
            {"label": "📊 Top API Usage Accounts", "query": "Which account has used the highest number of API calls?"},
            {"label": "⚡ Uptime SLA & Credit Policy", "query": "What is our uptime SLA guarantee and credit policy for downtime?"},
            {"label": "🔒 SOC2 Security & Encryption", "query": "What data encryption and SOC2 compliance standards are maintained?"}
        ]
    }
}

def get_agent_config(agent_id: str) -> Dict[str, Any]:
    """Retrieves agent configuration by ID, defaulting to E-Commerce agent."""
    return AGENT_REGISTRY.get(agent_id, AGENT_REGISTRY["ecommerce"])
