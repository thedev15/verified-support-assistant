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
        self.assertEqual(response.json()["version"], "0.2.0")

    def test_ask_returns_citations(self) -> None:
        response = self.client.post("/api/ask", json={"question": "How long is a refund?"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["refused"])
        self.assertEqual(payload["citations"][0]["document_id"], "REF-001")
        self.assertEqual(len(payload["citations"]), 1)
        self.assertEqual(payload["citations"][0]["source"], "/policies/REF-001")
        self.assertEqual(len(payload["request_id"]), 32)
        self.assertGreaterEqual(payload["latency_ms"], 0)

    def test_metadata_describes_runtime(self) -> None:
        response = self.client.get("/api/meta")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["name"], "Verified Support Assistant")
        self.assertEqual(payload["version"], "0.2.0")
        self.assertEqual(payload["document_count"], 12)
        self.assertEqual(payload["links"]["policies"], "/policies")

    def test_policy_catalog_is_discoverable(self) -> None:
        response = self.client.get("/api/policies")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 12)
        self.assertEqual(response.json()[0]["document_id"], "SHIP-001")

    def test_human_policy_library_and_about_page(self) -> None:
        policies = self.client.get("/policies")
        about = self.client.get("/about")
        self.assertEqual(policies.status_code, 200)
        self.assertIn("Policy library", policies.text)
        self.assertIn("/policies/REF-001", policies.text)
        self.assertEqual(about.status_code, 200)
        self.assertIn("How verification works", about.text)

    def test_frontend_assets_are_served(self) -> None:
        stylesheet = self.client.get("/static/app.css")
        script = self.client.get("/static/app.js")
        self.assertEqual(stylesheet.status_code, 200)
        self.assertIn("text/css", stylesheet.headers["content-type"])
        self.assertEqual(script.status_code, 200)
        self.assertIn("submitQuestion", script.text)

    def test_citation_opens_versioned_policy(self) -> None:
        response = self.client.get("/policies/REF-001")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Refund processing times", response.text)
        self.assertIn("Versioned support policy", response.text)

    def test_unknown_policy_returns_404(self) -> None:
        response = self.client.get("/policies/UNKNOWN")
        self.assertEqual(response.status_code, 404)

    def test_request_validation(self) -> None:
        response = self.client.post("/api/ask", json={"question": "x"})
        self.assertEqual(response.status_code, 422)

    def test_whitespace_and_punctuation_only_question_is_rejected(self) -> None:
        response = self.client.post("/api/ask", json={"question": "  ???  "})
        self.assertEqual(response.status_code, 422)

    def test_security_and_cache_headers(self) -> None:
        response = self.client.get("/api/meta")
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["x-frame-options"], "DENY")
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertIn("frame-ancestors 'none'", response.headers["content-security-policy"])


if __name__ == "__main__":
    unittest.main()
