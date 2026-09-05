import { useState, useRef, useEffect } from 'react'
import { sendChatMessage } from '../services/queries'
import { Send, Bot, User, Sparkles, MessageSquare } from 'lucide-react'

interface Message {
  role: 'user' | 'assistant'
  content: string
  agent?: string
  time?: string
}

const SUGGESTIONS = [
  'Which district has the highest pollution?',
  'What are the main hotspots in Gujarat?',
  'Why is Vapi so polluted?',
  'What should I do during high air pollution?',
  'Compare Ahmedabad and Surat pollution levels.',
  'What is the water quality in Ankleshwar?',
  'Show me industrial pollution zones.',
  'How to report a pollution incident?',
]

const WELCOME_MSG: Message = {
  role: 'assistant',
  content: `Hello! I'm **EcoGuard**, your Gujarat Pollution Intelligence Assistant. I can help you with:\n\n• Current pollution levels by district or city\n• Industrial hotspot information\n• Health advice for different pollution conditions\n• Water, air, noise and industrial pollution data\n• Predictions and trend analysis\n• How to report pollution incidents\n\nWhat would you like to know about Gujarat's pollution?`,
  agent: 'EcoGuard Assistant',
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([WELCOME_MSG])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | undefined>()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (msg?: string) => {
    const text = msg || input.trim()
    if (!text || loading) return

    const userMsg: Message = { role: 'user', content: text, time: new Date().toLocaleTimeString() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const resp = await sendChatMessage(text, sessionId)
      setSessionId(resp.session_id)
      const assistantMsg: Message = {
        role: 'assistant',
        content: resp.assistant_response,
        agent: resp.agent_used,
        time: new Date().toLocaleTimeString(),
      }
      setMessages(prev => [...prev, assistantMsg])
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please check that the backend is running and try again.',
        agent: 'System',
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const formatContent = (content: string) => {
    // Simple markdown-ish formatting
    return content
      .split('\n')
      .map((line, i) => {
        if (line.startsWith('**') && line.endsWith('**')) {
          return <strong key={i} style={{ display: 'block', marginBottom: 4 }}>{line.slice(2, -2)}</strong>
        }
        if (line.startsWith('• ')) {
          return <div key={i} style={{ paddingLeft: 12, marginBottom: 2 }}>• {line.slice(2)}</div>
        }
        if (line.match(/^\d+\)/)) {
          return <div key={i} style={{ paddingLeft: 12, marginBottom: 2 }}>{line}</div>
        }
        if (line === '') return <div key={i} style={{ height: 8 }} />
        // Handle **bold** inline
        const boldParts = line.split(/\*\*(.*?)\*\*/g)
        if (boldParts.length > 1) {
          return (
            <span key={i} style={{ display: 'block', marginBottom: 2 }}>
              {boldParts.map((part, j) =>
                j % 2 === 1 ? <strong key={j}>{part}</strong> : part
              )}
            </span>
          )
        }
        return <span key={i} style={{ display: 'block', marginBottom: 2 }}>{line}</span>
      })
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 900, margin: '0 auto' }}>
      <div>
        <h1 className="page-heading">Ask EcoGuard</h1>
        <p className="page-sub">AI-powered pollution intelligence assistant — powered by IBM Granite</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 20 }}>
        {/* Chat area */}
        <div>
          <div className="chat-container">
            <div className="chat-messages">
              {messages.map((msg, i) => (
                <div key={i}>
                  {msg.role === 'user' ? (
                    <div className="chat-message user">
                      {msg.content}
                    </div>
                  ) : (
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                        <div style={{
                          width: 24, height: 24, borderRadius: '50%',
                          background: 'linear-gradient(135deg, var(--emerald), var(--teal))',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                        }}>
                          <Sparkles size={12} color="white" />
                        </div>
                        <span style={{ fontSize: 10, color: 'var(--muted)', fontWeight: 600 }}>
                          {msg.agent || 'EcoGuard'}
                        </span>
                        {msg.time && <span style={{ fontSize: 10, color: 'var(--muted2)' }}>{msg.time}</span>}
                      </div>
                      <div className="chat-message assistant">
                        {formatContent(msg.content)}
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {loading && (
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                    <div style={{
                      width: 24, height: 24, borderRadius: '50%',
                      background: 'linear-gradient(135deg, var(--emerald), var(--teal))',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      <Sparkles size={12} color="white" />
                    </div>
                    <span style={{ fontSize: 10, color: 'var(--muted)' }}>Analyzing…</span>
                  </div>
                  <div className="chat-message assistant">
                    <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                      <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--emerald)', animation: 'pulse-dot 1s ease-in-out 0s infinite' }} />
                      <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--emerald)', animation: 'pulse-dot 1s ease-in-out 0.2s infinite' }} />
                      <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--emerald)', animation: 'pulse-dot 1s ease-in-out 0.4s infinite' }} />
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            <div className="chat-input-row">
              <textarea
                className="chat-input"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about pollution in Gujarat…"
                rows={1}
                style={{ resize: 'none', minHeight: 38, maxHeight: 100 }}
                disabled={loading}
              />
              <button
                className="btn btn-primary chat-send-btn"
                onClick={() => handleSend()}
                disabled={!input.trim() || loading}
              >
                <Send size={15} />
              </button>
            </div>
          </div>

          <div style={{ marginTop: 8, fontSize: 11, color: 'var(--muted)', textAlign: 'center' }}>
            Press Enter to send · Shift+Enter for new line · Data is DEMO/SIMULATED
          </div>
        </div>

        {/* Suggestions */}
        <div>
          <div className="card">
            <div className="card-title">
              <MessageSquare size={14} /> Suggested Questions
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {SUGGESTIONS.map(s => (
                <button
                  key={s}
                  className="btn btn-outline btn-sm"
                  onClick={() => handleSend(s)}
                  disabled={loading}
                  style={{ textAlign: 'left', whiteSpace: 'normal', height: 'auto', padding: '8px 12px', lineHeight: 1.4 }}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div className="card" style={{ marginTop: 16 }}>
            <div className="card-title">
              <Bot size={14} /> About This Assistant
            </div>
            <div style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.7 }}>
              Powered by <strong style={{ color: 'var(--emerald2)' }}>IBM Granite AI</strong> with fallback 
              intelligence when AI is unavailable.
              <br /><br />
              <span style={{ color: 'var(--purple)', fontWeight: 600 }}>Note:</span> Responses are based on 
              simulated/estimated data and AI analysis. Not official government measurements.
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
