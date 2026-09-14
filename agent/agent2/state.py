import sys
from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict

class AgentState(TypedDict):
    question: str
    intent: str  # 'sql', 'rag', 'direct'
    intent_reasoning: str
    generated_sql: Optional[str]
    sql_result: Optional[List[Dict[str, Any]]]
    sql_error: Optional[str]
    retrieved_context: Optional[List[Dict[str, Any]]]
    final_answer: str
    final_answer_source: str
    final_answer_model: str
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    execution_trace: List[Dict[str, Any]]
