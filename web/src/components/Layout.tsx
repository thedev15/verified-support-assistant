import { useQuery } from "@tanstack/react-query";
import { NavLink, Outlet } from "react-router-dom";

import { getMetadata } from "../api/client";
import { useTheme } from "../hooks/useTheme";

function navClass({ isActive }: { isActive: boolean }) {
  return isActive ? "nav-link active" : "nav-link";
}

export function Layout() {
  const { theme, toggleTheme } = useTheme();
  const metadata = useQuery({
    queryKey: ["metadata"],
    queryFn: ({ signal }) => getMetadata(signal),
    staleTime: 60_000,
  });

  return (
    <div className="site-shell">
      <a className="skip-link" href="#content">
        Skip to content
      </a>
      <header className="topbar">
        <NavLink className="brand" to="/assistant" aria-label="Verified Support home">
          <span className="brand-mark" aria-hidden="true">
            ✓
          </span>
          <span>
            Verified Support <small>Studio</small>
          </span>
        </NavLink>
        <nav className="nav-links" aria-label="Primary navigation">
          <NavLink className={navClass} to="/assistant">
            Assistant
          </NavLink>
          <NavLink className={navClass} to="/policies">
            Policies
          </NavLink>
          <NavLink className={navClass} to="/evaluations">
            Evaluations
          </NavLink>
          <NavLink className={navClass} to="/about">
            About
          </NavLink>
          <a className="nav-link" href="/docs">
            API
          </a>
          <button
            className="icon-button"
            type="button"
            onClick={toggleTheme}
            aria-label={`Use ${theme === "dark" ? "light" : "dark"} theme`}
            title="Change color theme"
          >
            {theme === "dark" ? "☼" : "◐"}
          </button>
        </nav>
      </header>

      <div className="runtime-strip" role="status">
        <span className={metadata.isError ? "live-dot offline" : "live-dot"} aria-hidden="true" />
        <span>
          {metadata.data
            ? `${metadata.data.document_count} policies · ${metadata.data.evaluation_count} evals · ${metadata.data.backend} · v${metadata.data.version}`
            : metadata.isError
              ? "Policy service unavailable"
              : "Connecting to verification service…"}
        </span>
      </div>

      <main id="content">
        <Outlet />
      </main>

      <footer className="site-footer">
        <span>Verified Support Studio · Synthetic demonstration policies</span>
        <span>
          <NavLink to="/about">Limitations</NavLink> · <a href="/docs">OpenAPI</a>
        </span>
      </footer>
    </div>
  );
}