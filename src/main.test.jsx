import { describe, it, expect, beforeEach, afterEach } from 'vitest'

describe('main', () => {
  let originalRoot

  beforeEach(() => {
    originalRoot = document.getElementById('root')
    if (originalRoot) {
      originalRoot.remove()
    }
    const root = document.createElement('div')
    root.id = 'root'
    document.body.appendChild(root)
  })

  afterEach(() => {
    const root = document.getElementById('root')
    if (root) {
      root.innerHTML = ''
    }
  })

  it('renders the App inside the root element', async () => {
    await import('./main.jsx')
    // Allow React to flush
    await new Promise((resolve) => setTimeout(resolve, 0))
    const root = document.getElementById('root')
    expect(root.innerHTML).not.toBe('')
  })

  it('root element exists in the document', () => {
    const root = document.getElementById('root')
    expect(root).toBeInTheDocument()
  })
})
