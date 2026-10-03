import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  failed: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { failed: false };

  static getDerivedStateFromError(): State {
    return { failed: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("VSA interface error", error, info);
  }

  render() {
    if (this.state.failed) {
      return (
        <main className="fatal-state">
          <p className="eyebrow">Interface recovery</p>
          <h1>The studio could not finish rendering.</h1>
          <p>Your question was not submitted. Reload the page to restore the verified interface.</p>
          <button className="primary-button" type="button" onClick={() => window.location.reload()}>
            Reload studio
          </button>
        </main>
      );
    }
    return this.props.children;
  }
}