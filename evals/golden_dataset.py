from typing import List, Dict, Any

GOLDEN_TEST_CASES: List[Dict[str, Any]] = [
    {
        "id": "TC-001",
        "question": "What is the total revenue for Electronics category products?",
        "expected_intent": "sql",
        "category": "Text-to-SQL",
        "expected_tables": ["orders", "products", "order_items"],
        "expected_output_keywords": ["revenue", "$", "Electronics"],
        "difficulty": "Medium"
    },
    {
        "id": "TC-002",
        "question": "Which customer has spent the most money overall?",
        "expected_intent": "sql",
        "category": "Text-to-SQL",
        "expected_tables": ["customers"],
        "expected_output_keywords": ["Fiona Gallagher", "spent", "$"],
        "difficulty": "Easy"
    },
    {
        "id": "TC-003",
        "question": "List all products in Furniture category with stock and price.",
        "expected_intent": "sql",
        "category": "Text-to-SQL",
        "expected_tables": ["products"],
        "expected_output_keywords": ["Furniture", "Ergonomic Mesh Chair", "Standing Electric Desk"],
        "difficulty": "Easy"
    },
    {
        "id": "TC-004",
        "question": "What is our store's refund policy for opened electronics?",
        "expected_intent": "rag",
        "category": "Document RAG",
        "expected_doc": "refund_policy.md",
        "expected_output_keywords": ["30 days", "restocking fee", "10%"],
        "difficulty": "Easy"
    },
    {
        "id": "TC-005",
        "question": "What hardware issues are covered under the 1-year warranty?",
        "expected_intent": "rag",
        "category": "Document RAG",
        "expected_doc": "warranty_policy.md",
        "expected_output_keywords": ["1-Year Limited", "battery failure", "dead pixels"],
        "difficulty": "Medium"
    },
    {
        "id": "TC-006",
        "question": "How long does standard shipping take and is it free?",
        "expected_intent": "rag",
        "category": "Document RAG",
        "expected_doc": "shipping_guide.md",
        "expected_output_keywords": ["3-5 business days", "Free", "$50"],
        "difficulty": "Easy"
    },
    {
        "id": "TC-007",
        "question": "What perks do Platinum tier members receive?",
        "expected_intent": "rag",
        "category": "Document RAG",
        "expected_doc": "security_privacy.md",
        "expected_output_keywords": ["Platinum", "24/7 dedicated", "express returns"],
        "difficulty": "Medium"
    },
    {
        "id": "TC-008",
        "question": "Show all orders shipped to New York city.",
        "expected_intent": "sql",
        "category": "Text-to-SQL",
        "expected_tables": ["orders"],
        "expected_output_keywords": ["New York", "Delivered"],
        "difficulty": "Easy"
    },
    {
        "id": "TC-009",
        "question": "Can I return clearance items bought on final sale?",
        "expected_intent": "rag",
        "category": "Document RAG",
        "expected_doc": "refund_policy.md",
        "expected_output_keywords": ["Ineligible", "clearance", "final sale"],
        "difficulty": "Hard"
    },
    {
        "id": "TC-010",
        "question": "What is the average rating of our highest priced products?",
        "expected_intent": "sql",
        "category": "Text-to-SQL",
        "expected_tables": ["products"],
        "expected_output_keywords": ["rating", "UltraBook Pro", "4.8"],
        "difficulty": "Hard"
    }
]
