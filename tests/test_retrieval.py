import unittest
from pathlib import Path

from support_assistant.knowledge import load_documents
from support_assistant.retrieval import TfidfRetriever


class RetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.retriever = TfidfRetriever(load_documents(Path("data/knowledge_base.json")))

    def test_refund_question_ranks_refund_policy_first(self) -> None:
        results = self.retriever.search("How long does a refund take?", top_k=3)
        self.assertEqual(results[0].id, "REF-001")

    def test_security_question_ranks_security_policy_first(self) -> None:
        results = self.retriever.search("Should I share my password or one-time code?", top_k=3)
        self.assertEqual(results[0].id, "SEC-001")

    def test_unrelated_query_has_no_strong_match(self) -> None:
        results = self.retriever.search("Who won the football championship?", top_k=3)
        self.assertTrue(not results or results[0].score < 0.12)


if __name__ == "__main__":
    unittest.main()
