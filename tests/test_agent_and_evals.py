import unittest
from agent.graph import run_agent_workflow
from evals.evaluator import evaluate_agent_execution
from agent.sql_tool import execute_sql_query, validate_sql_schema_alignment, generate_llm_sql
from agent.rag_tool import search_documents, init_chroma_collection
from agent.registry import AGENT_REGISTRY, get_agent_config
from agent.agent1.graph import run_agent_workflow as run_ecommerce_workflow

class TestMultiAgentAndEvals(unittest.TestCase):
    
    def test_multi_agent_registry(self):
        ecom_cfg = get_agent_config("ecommerce")
        fin_cfg = get_agent_config("financial_saas")
        self.assertEqual(ecom_cfg["id"], "ecommerce")
        self.assertEqual(fin_cfg["id"], "financial_saas")
        self.assertIn("subscriptions", fin_cfg["known_tables"])

    def test_ecommerce_agent_workflow(self):
        state = run_agent_workflow("What is the total revenue for Electronics category products?", agent_id="ecommerce")
        self.assertEqual(state["intent"], "sql")
        self.assertIsNotNone(state["generated_sql"])
        self.assertIsNotNone(state["final_answer"])
        
    def test_financial_saas_agent_workflow(self):
        state = run_agent_workflow("What is the total revenue from active SaaS subscriptions?", agent_id="financial_saas")
        state["agent_id"] = "financial_saas"
        self.assertEqual(state["intent"], "sql")
        self.assertIsNotNone(state["generated_sql"])
        self.assertIsNotNone(state["final_answer"])
        
        eval_res = evaluate_agent_execution(state)
        self.assertGreaterEqual(eval_res["overall_score"], 80)
        self.assertGreaterEqual(eval_res["tool_correctness"]["score"], 0.80)

    def test_financial_saas_rag_workflow(self):
        state = run_agent_workflow("What is our uptime SLA guarantee and credit policy for downtime?", agent_id="financial_saas")
        state["agent_id"] = "financial_saas"
        self.assertEqual(state["intent"], "rag")
        self.assertIsNotNone(state["retrieved_context"])
        self.assertGreater(len(state["retrieved_context"]), 0)
        
        eval_res = evaluate_agent_execution(state)
        self.assertGreaterEqual(eval_res["faithfulness"]["score"], 0.75)

    def test_direct_route_has_final_answer_and_output_metrics(self):
        state = run_ecommerce_workflow("Hello, what can you help me with?")
        state["agent_id"] = "ecommerce"

        self.assertEqual(state["intent"], "direct")
        self.assertTrue(state["final_answer"].strip())
        self.assertIn(state["final_answer_source"], {"llm", "fallback"})

        eval_res = evaluate_agent_execution(state)
        output_metrics = eval_res["final_answer_quality"]
        self.assertTrue(output_metrics["has_content"])
        self.assertGreater(output_metrics["word_count"], 0)

if __name__ == "__main__":
    unittest.main()
