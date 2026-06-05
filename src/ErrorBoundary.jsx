import { Component } from 'react'

class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('Uncaught rendering error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '2rem', textAlign: 'center' }}>
          <h1>Something went wrong</h1>
          <p style={{ color: 'var(--text)' }}>
            The application encountered an unexpected error.
          </p>
          <pre
            style={{
              textAlign: 'left',
              maxWidth: '600px',
              margin: '1rem auto',
              padding: '1rem',
              background: 'var(--code-bg)',
              borderRadius: '4px',
              overflow: 'auto',
            }}
          >
            {this.state.error?.message}
          </pre>
          <button
            type="button"
            className="counter"
            onClick={() => this.setState({ hasError: false, error: null })}
          >
            Try again
          </button>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
