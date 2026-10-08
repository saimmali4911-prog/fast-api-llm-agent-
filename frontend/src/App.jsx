import { useState } from 'react'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export default function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: 'Hello! I can manage employee records for you. Ask me to add, view, update, or delete records.' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSend = async (e) => {
    e.preventDefault()
    const userMessage = input.trim()
    if (!userMessage || loading) return

    setError('')
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', text: userMessage }])
    setLoading(true)

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage })
      })

      if (!response.ok) {
        let errorDetail = `Server returned error status ${response.status}`
        try {
          const errJson = await response.json()
          if (errJson.detail) {
            errorDetail = errJson.detail
          }
        } catch (_) {}
        throw new Error(errorDetail)
      }

      const data = await response.json()
      setMessages((prev) => [...prev, { role: 'assistant', text: data.response }])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <h2>Employee Database AI Agent</h2>
      <p style={{ fontSize: '13px', color: '#666' }}>Connected to: {API_BASE_URL}</p>

      {error && <div style={{ color: 'red', marginBottom: '10px' }}>{error}</div>}

      <div className="chat-box">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            <strong>{msg.role === 'user' ? 'You' : 'Agent'}:</strong>
            <div>{msg.text}</div>
          </div>
        ))}
        {loading && <div className="message assistant"><em>Agent is thinking and querying database...</em></div>}
      </div>

      <form onSubmit={handleSend} className="input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="e.g. List all employees or Add Sarah in Sales"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  )
}
