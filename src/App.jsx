import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from './assets/vite.svg'
import heroImg from './assets/hero.png'
import LinkSection from './components/LinkSection'
import Divider from './components/Divider'
import './App.css'

const docLinks = [
  { href: 'https://vite.dev/', icon: viteLogo, label: 'Explore Vite', iconType: 'img', iconClassName: 'logo' },
  { href: 'https://react.dev/', icon: reactLogo, label: 'Learn more', iconType: 'img' },
]

const socialLinks = [
  { href: 'https://github.com/vitejs/vite', icon: '/icons.svg#github-icon', label: 'GitHub' },
  { href: 'https://chat.vite.dev/', icon: '/icons.svg#discord-icon', label: 'Discord' },
  { href: 'https://x.com/vite_js', icon: '/icons.svg#x-icon', label: 'X.com' },
  { href: 'https://bsky.app/profile/vite.dev', icon: '/icons.svg#bluesky-icon', label: 'Bluesky' },
]

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      <section id="center">
        <div className="hero">
          <img src={heroImg} className="base" width="170" height="179" alt="" />
          <img src={reactLogo} className="framework" alt="React logo" />
          <img src={viteLogo} className="vite" alt="Vite logo" />
        </div>
        <div>
          <h1>Asena AI Projesine Hoş Geldiniz</h1>
          <p>
            Edit <code>src/App.jsx</code> and save to test <code>HMR</code>
          </p>
        </div>
        <button
          type="button"
          className="counter"
          onClick={() => setCount((count) => count + 1)}
        >
          Count is {count}
        </button>
      </section>

      <Divider />

      <section id="next-steps">
        <LinkSection
          id="docs"
          iconHref="/icons.svg#documentation-icon"
          title="Documentation"
          subtitle="Your questions, answered"
          links={docLinks}
        />
        <LinkSection
          id="social"
          iconHref="/icons.svg#social-icon"
          title="Connect with us"
          subtitle="Join the Vite community"
          links={socialLinks}
        />
      </section>

      <Divider />
      <section id="spacer"></section>
    </>
  )
}

export default App
