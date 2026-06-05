import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from './App'

describe('App', () => {
  it('renders the welcome heading', () => {
    render(<App />)
    expect(
      screen.getByRole('heading', { level: 1, name: /hoş geldiniz/i }),
    ).toBeInTheDocument()
  })

  it('renders the counter button with initial count of 0', () => {
    render(<App />)
    const button = screen.getByRole('button', { name: /count is 0/i })
    expect(button).toBeInTheDocument()
  })

  it('increments the counter when clicked', async () => {
    const user = userEvent.setup()
    render(<App />)

    const button = screen.getByRole('button', { name: /count is 0/i })
    await user.click(button)
    expect(button).toHaveTextContent('Count is 1')

    await user.click(button)
    expect(button).toHaveTextContent('Count is 2')
  })

  it('renders the HMR instruction text', () => {
    render(<App />)
    expect(screen.getByText(/edit/i)).toBeInTheDocument()
    expect(screen.getByText('src/App.jsx')).toBeInTheDocument()
    expect(screen.getByText('HMR')).toBeInTheDocument()
  })

  it('renders the hero images', () => {
    render(<App />)
    expect(screen.getByAltText('React logo')).toBeInTheDocument()
    expect(screen.getByAltText('Vite logo')).toBeInTheDocument()
  })

  describe('Documentation section', () => {
    it('renders the Documentation heading', () => {
      render(<App />)
      expect(
        screen.getByRole('heading', { level: 2, name: /documentation/i }),
      ).toBeInTheDocument()
    })

    it('renders Explore Vite link with correct href', () => {
      render(<App />)
      const link = screen.getByRole('link', { name: /explore vite/i })
      expect(link).toHaveAttribute('href', 'https://vite.dev/')
      expect(link).toHaveAttribute('target', '_blank')
    })

    it('renders Learn more link with correct href', () => {
      render(<App />)
      const link = screen.getByRole('link', { name: /learn more/i })
      expect(link).toHaveAttribute('href', 'https://react.dev/')
      expect(link).toHaveAttribute('target', '_blank')
    })
  })

  describe('Social section', () => {
    it('renders the Connect with us heading', () => {
      render(<App />)
      expect(
        screen.getByRole('heading', { level: 2, name: /connect with us/i }),
      ).toBeInTheDocument()
    })

    it('renders GitHub link', () => {
      render(<App />)
      const link = screen.getByRole('link', { name: /github/i })
      expect(link).toHaveAttribute('href', 'https://github.com/vitejs/vite')
      expect(link).toHaveAttribute('target', '_blank')
    })

    it('renders Discord link', () => {
      render(<App />)
      const link = screen.getByRole('link', { name: /discord/i })
      expect(link).toHaveAttribute('href', 'https://chat.vite.dev/')
      expect(link).toHaveAttribute('target', '_blank')
    })

    it('renders X.com link', () => {
      render(<App />)
      const link = screen.getByRole('link', { name: /x\.com/i })
      expect(link).toHaveAttribute('href', 'https://x.com/vite_js')
      expect(link).toHaveAttribute('target', '_blank')
    })

    it('renders Bluesky link', () => {
      render(<App />)
      const link = screen.getByRole('link', { name: /bluesky/i })
      expect(link).toHaveAttribute(
        'href',
        'https://bsky.app/profile/vite.dev',
      )
      expect(link).toHaveAttribute('target', '_blank')
    })
  })

  it('renders all expected external links', () => {
    render(<App />)
    const links = screen.getAllByRole('link')
    expect(links.length).toBe(6)
  })

  it('counter button has type="button"', () => {
    render(<App />)
    const button = screen.getByRole('button', { name: /count is/i })
    expect(button).toHaveAttribute('type', 'button')
  })
})
