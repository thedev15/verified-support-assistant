import { Navigate, Route, Routes } from "react-router-dom";

import { Layout } from "./components/Layout";
import { AboutPage } from "./pages/AboutPage";
import { AssistantPage } from "./pages/AssistantPage";
import { EvaluationsPage } from "./pages/EvaluationsPage";
import { PoliciesPage } from "./pages/PoliciesPage";
import { PolicyDetailPage } from "./pages/PolicyDetailPage";

export function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Navigate replace to="/assistant" />} />
        <Route path="assistant" element={<AssistantPage />} />
        <Route path="policies" element={<PoliciesPage />} />
        <Route path="policies/:documentId" element={<PolicyDetailPage />} />
        <Route path="evaluations" element={<EvaluationsPage />} />
        <Route path="about" element={<AboutPage />} />
        <Route path="*" element={<Navigate replace to="/assistant" />} />
      </Route>
    </Routes>
  );
}