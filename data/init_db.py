import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "ecommerce.db"
DOCS_DIR = BASE_DIR / "documents"

def init_sqlite_db():
    print(f"Initializing SQLite database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Drop existing tables if re-running
    cursor.executescript("""
        DROP TABLE IF EXISTS order_items;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS customers;
    """)

    # Products Table
    cursor.execute("""
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock_quantity INTEGER NOT NULL,
            rating REAL NOT NULL
        );
    """)

    # Customers Table
    cursor.execute("""
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            membership_tier TEXT NOT NULL,
            total_spent REAL NOT NULL
        );
    """)

    # Orders Table
    cursor.execute("""
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            order_date TEXT NOT NULL,
            status TEXT NOT NULL,
            total_amount REAL NOT NULL,
            shipping_city TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
        );
    """)

    # Order Items Table
    cursor.execute("""
        CREATE TABLE order_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (order_id),
            FOREIGN KEY (product_id) REFERENCES products (product_id)
        );
    """)

    # Populate Products
    products_data = [
        ("UltraBook Pro 15", "Electronics", 1299.99, 45, 4.8),
        ("Noise-Canceling Headphones X", "Electronics", 249.99, 120, 4.6),
        ("Ergonomic Mesh Chair", "Furniture", 349.50, 30, 4.5),
        ("Mechanical RGB Keyboard", "Electronics", 119.00, 85, 4.7),
        ("4K Smart Monitor 27-inch", "Electronics", 429.99, 50, 4.9),
        ("Standing Electric Desk", "Furniture", 599.00, 15, 4.4),
        ("Wireless Gaming Mouse", "Electronics", 69.99, 200, 4.3),
        ("Stainless Steel Water Bottle", "Accessories", 24.99, 300, 4.9),
        ("Leather Executive Journal", "Accessories", 19.99, 150, 4.2),
        ("Smart Fitness Watch", "Electronics", 199.99, 90, 4.5),
    ]
    cursor.executemany("""
        INSERT INTO products (name, category, price, stock_quantity, rating)
        VALUES (?, ?, ?, ?, ?);
    """, products_data)

    # Populate Customers
    customers_data = [
        ("Alice Smith", "alice@example.com", "Gold", 3450.00),
        ("Bob Johnson", "bob@example.com", "Platinum", 7890.50),
        ("Charlie Davis", "charlie@example.com", "Silver", 850.25),
        ("Diana Prince", "diana@example.com", "Gold", 4120.00),
        ("Evan Wright", "evan@example.com", "Bronze", 210.00),
        ("Fiona Gallagher", "fiona@example.com", "Platinum", 9200.00),
    ]
    cursor.executemany("""
        INSERT INTO customers (name, email, membership_tier, total_spent)
        VALUES (?, ?, ?, ?);
    """, customers_data)

    # Populate Orders
    orders_data = [
        (1, "2026-08-01", "Delivered", 1549.98, "New York"),
        (2, "2026-08-05", "Delivered", 249.99, "San Francisco"),
        (3, "2026-08-10", "Shipped", 119.00, "Chicago"),
        (1, "2026-08-15", "Delivered", 429.99, "New York"),
        (4, "2026-08-20", "Processing", 599.00, "Austin"),
        (6, "2026-08-22", "Delivered", 1299.99, "Seattle"),
        (2, "2026-08-25", "Delivered", 768.99, "San Francisco"),
        (5, "2026-09-01", "Delivered", 199.99, "Boston"),
        (4, "2026-09-03", "Shipped", 69.99, "Austin"),
        (6, "2026-09-05", "Delivered", 349.50, "Seattle"),
    ]
    cursor.executemany("""
        INSERT INTO orders (customer_id, order_date, status, total_amount, shipping_city)
        VALUES (?, ?, ?, ?, ?);
    """, orders_data)

    # Populate Order Items
    order_items_data = [
        (1, 1, 1, 1299.99),
        (1, 2, 1, 249.99),
        (2, 2, 1, 249.99),
        (3, 4, 1, 119.00),
        (4, 5, 1, 429.99),
        (5, 6, 1, 599.00),
        (6, 1, 1, 1299.99),
        (7, 5, 1, 429.99),
        (7, 3, 1, 349.50),
        (8, 10, 1, 199.99),
        (9, 7, 1, 69.99),
        (10, 3, 1, 349.50),
    ]
    cursor.executemany("""
        INSERT INTO order_items (order_id, product_id, quantity, unit_price)
        VALUES (?, ?, ?, ?);
    """, order_items_data)

    conn.commit()
    conn.close()
    print("Database initialized successfully!")

def init_documents():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Creating policy documents at: {DOCS_DIR}")

    refund_policy = """# E-Commerce Refund & Return Policy

## 1. Return Window
Customers may return eligible items within **30 days** of delivery for a full refund or exchange. Items must be in original condition with intact packaging.

## 2. Eligibility Criteria
- **Eligible Items**: Electronics (unopened or defective), Furniture, Accessories.
- **Ineligible Items**: Custom personalized items, downloadable software, clearance items marked as final sale.

## 3. Refund Processing
- Once the returned item is inspected at our warehouse, refunds are processed to the original payment method within **3 to 5 business days**.
- Standard shipping charges are non-refundable unless the return is due to our error or a defective product.

## 4. Restocking Fees
- Electronics returned opened without defect incur a standard **10% restocking fee**.
- Furniture returns require a flat **$25 return pickup fee**.
"""

    warranty_policy = """# Hardware & Product Warranty Guidelines

## 1. Coverage Overview
All hardware products purchased through our store (including Laptops, Monitors, Headphones, and Keyboards) come with a **1-Year Limited Manufacturer Warranty** against defects in materials and workmanship.

## 2. What Is Covered
- Defective electronic components or motherboard failure.
- Battery failure within the first 6 months of purchase.
- Display screen dead pixels (3 or more dead pixels).

## 3. What Is Excluded
- Accidental liquid damage or drops.
- Cosmetic wear and tear (scratches, dents).
- Unauthorized repairs or modifications.

## 4. How to Submit a Claim
Contact support with your original Order ID and serial number. We will provide a pre-paid shipping label for warranty inspection or repair.
"""

    shipping_guide = """# Shipping & Delivery Guidelines

## 1. Domestic Shipping Rates
- **Standard Shipping (3-5 business days)**: Free on all orders over $50. Otherwise flat $4.99.
- **Express Shipping (1-2 business days)**: Flat rate of $14.99 regardless of order total.

## 2. Shipping Cities & Warehouses
We ship nationwide within the United States from regional fulfillment hubs in **New York, San Francisco, Chicago, Austin, and Seattle**.

## 3. Order Tracking & Delivery Status
- Orders marked as **Processing** ship within 24 hours.
- Orders marked as **Shipped** include an active tracking number via email.
- Delivery issues or lost packages must be reported within 7 days of estimated delivery date.
"""

    security_privacy = """# Account Security & Customer Escalations

## 1. Account Protection
We use industry-standard encryption to protect customer account details, payment credentials, and transaction histories.

## 2. Tier Benefits & Support Escalation
- **Platinum Members**: Priority 24/7 dedicated support phone line and free express returns.
- **Gold Members**: Dedicated email support with guaranteed response within 2 hours.
- **Silver & Bronze Members**: Standard customer support assistance within 24 hours.

## 3. Data Deletion & Privacy Requests
Customers may request a copy of their personal data or submit a data deletion request under GDPR/CCPA regulations by emailing privacy@example.com.
"""

    (DOCS_DIR / "refund_policy.md").write_text(refund_policy, encoding="utf-8")
    (DOCS_DIR / "warranty_policy.md").write_text(warranty_policy, encoding="utf-8")
    (DOCS_DIR / "shipping_guide.md").write_text(shipping_guide, encoding="utf-8")
    (DOCS_DIR / "security_privacy.md").write_text(security_privacy, encoding="utf-8")
    print("Documents initialized successfully!")
    
    # Initialize ChromaDB vector database
    try:
        from agent.rag_tool import init_chroma_collection
        init_chroma_collection()
    except Exception as e:
        print(f"ChromaDB initialization note: {e}")

if __name__ == "__main__":
    init_sqlite_db()
    init_documents()

