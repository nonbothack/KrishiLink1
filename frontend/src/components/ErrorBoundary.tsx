import { Component, type ReactNode } from 'react';
import { Link } from 'react-router-dom';

interface ErrorBoundaryProps {
  children: ReactNode;
  resetKey?: string;
  title: string;
  retry: string;
  home: string;
}

interface ErrorBoundaryState {
  failed: boolean;
  attempt: number;
}

export default class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { failed: false, attempt: 0 };

  static getDerivedStateFromError(): Partial<ErrorBoundaryState> {
    return { failed: true };
  }

  componentDidUpdate(previousProps: Readonly<ErrorBoundaryProps>) {
    if (previousProps.resetKey !== this.props.resetKey && this.state.failed) {
      this.setState((state) => ({ failed: false, attempt: state.attempt + 1 }));
    }
  }

  render() {
    if (this.state.failed) {
      return (
        <div className="data-state error-boundary" role="alert" aria-live="assertive">
          <h1>{this.props.title}</h1>
          <button
            className="button"
            type="button"
            onClick={() =>
              this.setState((state) => ({ failed: false, attempt: state.attempt + 1 }))
            }
          >
            {this.props.retry}
          </button>
          <Link className="text-link" to="/">
            {this.props.home}
          </Link>
        </div>
      );
    }

    return <div key={this.state.attempt}>{this.props.children}</div>;
  }
}
