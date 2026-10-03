import re
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
        self.assertEqual(response.json()["version"], "0.3.0")

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
        self.assertEqual(payload["version"], "0.3.0")
        self.assertEqual(payload["document_count"], 12)
        self.assertEqual(payload["links"]["policies"], "/policies")

    def test_policy_catalog_is_discoverable(self) -> None:
        response = self.client.get("/api/policies")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 12)
        self.assertEqual(response.json()[0]["document_id"], "SHIP-001")

    def test_spa_routes_return_the_application_shell(self) -> None:
        policies = self.client.get("/policies")
        about = self.client.get("/about")
        self.assertEqual(policies.status_code, 200)
        self.assertIn("Verified Support", policies.text)
        self.assertEqual(about.status_code, 200)
        self.assertIn("Verified Support", about.text)

    def test_frontend_assets_are_served(self) -> None:
        index = self.client.get("/")
        stylesheet_path = re.search(r'href="(/assets/[^"]+\.css)"', index.text)
        script_path = re.search(r'src="(/assets/[^"]+\.js)"', index.text)
        self.assertIsNotNone(stylesheet_path)
        self.assertIsNotNone(script_path)
        stylesheet = self.client.get(stylesheet_path.group(1))
        script = self.client.get(script_path.group(1))
        self.assertEqual(stylesheet.status_code, 200)
        self.assertIn("text/css", stylesheet.headers["content-type"])
        self.assertEqual(script.status_code, 200)
        self.assertIn("javascript", script.headers["content-type"])

    def test_versioned_policy_api_returns_detail(self) -> None:
        response = self.client.get("/api/policies/REF-001")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "Refund processing times")
        self.assertIn("5 to 10 business days", response.json()["text"])

    def test_unknown_policy_api_returns_404(self) -> None:
        response = self.client.get("/api/policies/UNKNOWN")
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
