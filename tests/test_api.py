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

    def test_request_validation(self) -> None:
        response = self.client.post("/api/ask", json={"question": "x"})
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()