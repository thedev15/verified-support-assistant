import unittest

try:
    from fastapi.testclient import TestClient

    from support_assistant.api import app
except ModuleNotFoundError:
    TestClient = None
    app = None


@unittest.skipIf(TestClient is None, "FastAPI is not installed in the local workbench")
class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_health(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(response.json()["documents"], 12)

    def test_ask_returns_citations(self) -> None:
        response = self.client.post("/api/ask", json={"question": "How long is a refund?"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["refused"])
        self.assertEqual(payload["citations"][0]["document_id"], "REF-001")
        self.assertEqual(len(payload["citations"]), 1)
        self.assertEqual(payload["citations"][0]["source"], "/policies/REF-001")

    def test_citation_opens_versioned_policy(self) -> None:
        response = self.client.get("/policies/REF-001")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Refund processing times", response.text)
        self.assertIn("VERSIONED SUPPORT POLICY", response.text)

    def test_unknown_policy_returns_404(self) -> None:
        response = self.client.get("/policies/UNKNOWN")
        self.assertEqual(response.status_code, 404)

    def test_request_validation(self) -> None:
        response = self.client.post("/api/ask", json={"question": "x"})
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()