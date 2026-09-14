import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "financial_saas.db"
DOCS_DIR = BASE_DIR / "financial_documents"
CHROMA_DIR = BASE_DIR / "chroma_db"

CHROMADB_AVAILABLE = False
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


def init_financial_sqlite_db():
    print(f"Initializing Financial & SaaS SQLite DB at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.executescript("""
        DROP TABLE IF EXISTS usage_metrics;
        DROP TABLE IF EXISTS invoices;
        DROP TABLE IF EXISTS subscriptions;
        DROP TABLE IF EXISTS plans;
    """)

    # Plans Table
    cursor.execute("""
        CREATE TABLE plans (
            plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            monthly_price REAL NOT NULL,
            max_api_calls INTEGER NOT NULL,
            max_storage_gb INTEGER NOT NULL
        );
    """)

    # Subscriptions Table
    cursor.execute("""
        CREATE TABLE subscriptions (
            subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_name TEXT NOT NULL,
            plan_name TEXT NOT NULL,
            monthly_fee REAL NOT NULL,
            status TEXT NOT NULL,
            start_date TEXT NOT NULL
        );
    """)

    # Invoices Table
    cursor.execute("""
        CREATE TABLE invoices (
            invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_name TEXT NOT NULL,
            invoice_date TEXT NOT NULL,
            amount REAL NOT NULL,
            payment_status TEXT NOT NULL
        );
    """)

    # Usage Metrics Table
    cursor.execute("""
        CREATE TABLE usage_metrics (
            metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_name TEXT NOT NULL,
            api_calls_count INTEGER NOT NULL,
            storage_used_gb REAL NOT NULL,
            compute_hours INTEGER NOT NULL
        );
    """)

    # Populate Plans
    plans_data = [
        ("Starter", 49.00, 50000, 50),
        ("Professional", 199.00, 500000, 500),
        ("Enterprise", 999.00, 10000000, 5000),
    ]
    cursor.executemany("INSERT INTO plans (name, monthly_price, max_api_calls, max_storage_gb) VALUES (?, ?, ?, ?);", plans_data)

    # Populate Subscriptions
    subscriptions_data = [
        ("Acme Corp", "Enterprise", 999.00, "Active", "2026-01-15"),
        ("TechStart Inc", "Professional", 199.00, "Active", "2026-03-01"),
        ("Global Logistics", "Enterprise", 999.00, "Active", "2026-02-10"),
        ("CloudScale Analytics", "Professional", 199.00, "Active", "2026-04-12"),
        ("DevOps Studio", "Starter", 49.00, "Active", "2026-05-20"),
        ("DataFlow Systems", "Enterprise", 999.00, "Canceled", "2026-01-01"),
    ]
    cursor.executemany("INSERT INTO subscriptions (account_name, plan_name, monthly_fee, status, start_date) VALUES (?, ?, ?, ?, ?);", subscriptions_data)

    # Populate Invoices
    invoices_data = [
        ("Acme Corp", "2026-08-01", 999.00, "Paid"),
        ("TechStart Inc", "2026-08-01", 199.00, "Paid"),
        ("Global Logistics", "2026-08-01", 999.00, "Paid"),
        ("CloudScale Analytics", "2026-08-01", 199.00, "Overdue"),
        ("DevOps Studio", "2026-08-01", 49.00, "Paid"),
        ("Acme Corp", "2026-09-01", 999.00, "Paid"),
        ("TechStart Inc", "2026-09-01", 199.00, "Processing"),
    ]
    cursor.executemany("INSERT INTO invoices (account_name, invoice_date, amount, payment_status) VALUES (?, ?, ?, ?);", invoices_data)

    # Populate Usage Metrics
    usage_data = [
        ("Acme Corp", 4500000, 1200.5, 450),
        ("TechStart Inc", 320000, 180.0, 120),
        ("Global Logistics", 8900000, 4100.0, 980),
        ("CloudScale Analytics", 410000, 310.5, 210),
        ("DevOps Studio", 28000, 15.0, 40),
    ]
    cursor.executemany("INSERT INTO usage_metrics (account_name, api_calls_count, storage_used_gb, compute_hours) VALUES (?, ?, ?, ?);", usage_data)

    conn.commit()
    conn.close()
    print("Financial SQLite DB initialized successfully!")


def init_financial_documents():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    sla_guarantee = """# SaaS Service Level Agreement (SLA) & Uptime Guarantee

## 1. Uptime Commitment
We guarantee a **99.9% Monthly Uptime** for all SaaS API endpoints and web services.

## 2. SLA Service Credits
If uptime drops below commitment levels in a billing cycle:
- **99.0% - 99.8% Uptime**: 10% invoice credit.
- **95.0% - 98.9% Uptime**: 25% invoice credit.
- **Below 95.0% Uptime**: 50% invoice credit.

## 3. Incident Reporting & Maintenance
Scheduled maintenance windows are executed on Sundays between 02:00 UTC and 04:00 UTC with 48-hour advance notification.
"""

    billing_refund = """# Financial Billing & Subscription Refund Policy

## 1. Subscription Billing Cycle
Subscriptions are billed automatically in advance on a monthly or annual basis.

## 2. Cancellation & Refund Rules
- **Monthly Plans**: Cancellations take effect at the end of the current monthly billing period. No mid-month partial refunds.
- **Annual Plans**: Cancellations within **14 days** of purchase are eligible for a full 100% refund.
- **Invoice Disputes**: Billing discrepancies must be submitted in writing within 30 days of invoice date.
"""

    api_limits = """# API Quotas & Overage Charge Guidelines

## 1. Plan Quotas
- **Starter Plan**: Up to 50,000 API calls/month.
- **Professional Plan**: Up to 500,000 API calls/month.
- **Enterprise Plan**: Up to 10,000,000 API calls/month.

## 2. Overage Rates
API calls exceeding monthly plan quotas incur standard overage charges:
- **Professional / Enterprise**: $0.0005 per additional API call.
"""

    compliance = """# SOC2 Compliance & Data Privacy Guidelines

## 1. Enterprise Security & Compliance
Our SaaS platform maintains **SOC2 Type II Certification** and full compliance with GDPR, CCPA, and HIPAA security standards.

## 2. Data Encryption
All customer data is encrypted in transit using TLS 1.3 and at rest using AES-256 bit encryption.
"""

    (DOCS_DIR / "sla_guarantee.md").write_text(sla_guarantee, encoding="utf-8")
    (DOCS_DIR / "billing_refund_policy.md").write_text(billing_refund, encoding="utf-8")
    (DOCS_DIR / "api_usage_limits.md").write_text(api_limits, encoding="utf-8")
    (DOCS_DIR / "compliance_gdpr.md").write_text(compliance, encoding="utf-8")
    print("Financial policy documents initialized successfully!")


def init_financial_chroma_collection():
    if not CHROMADB_AVAILABLE:
        return None

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(
        name="financial_policies",
        metadata={"hnsw:space": "cosine"}
    )

    if collection.count() > 0:
        return collection

    chunks = []
    for filepath in DOCS_DIR.glob("*.md"):
        content = filepath.read_text(encoding="utf-8")
        sections = content.split("\n## ")
        for idx, sec in enumerate(sections):
            sec_text = ("## " + sec if idx > 0 else sec).strip()
            if sec_text:
                chunks.append({
                    "chunk_id": f"{filepath.name}#sec-{idx}",
                    "text": sec_text,
                    "metadata": {"source": filepath.name, "doc_title": filepath.stem.replace("_", " ").title()}
                })

    if chunks:
        collection.add(
            ids=[c["chunk_id"] for c in chunks],
            documents=[c["text"] for c in chunks],
            metadatas=[c["metadata"] for c in chunks]
        )
        print(f"Financial ChromaDB Collection initialized with {collection.count()} vector chunks!")
    return collection

if __name__ == "__main__":
    init_financial_sqlite_db()
    init_financial_documents()
    init_financial_chroma_collection()
