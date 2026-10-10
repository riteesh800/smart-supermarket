import React, { useState, useRef, useEffect } from 'react';
import { api } from '../services/api';
import { CHART_COLORS } from '../constants/colors';
import {
  ResponsiveContainer, BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, Cell, PieChart, Pie
} from 'recharts';

const QUICK_ACTIONS = [
  { label: '💰 Revenue', msg: 'total revenue' },
  { label: '🏆 Top Products', msg: 'best sellers' },
  { label: '📦 Low Stock', msg: 'low stock' },
  { label: '👥 Customers', msg: 'total customers' },
  { label: '📊 Profit', msg: 'profit margins' },
  { label: '🕐 Peak Hours', msg: 'peak hours' },
];

function renderMarkdown(text) {
  // Split on **bold** markers and newlines, returning React elements
  // React's default escaping protects against XSS — no dangerouslySetInnerHTML needed
  const parts = [];
  const segments = text.split(/(\*\*.+?\*\*)/g);
  segments.forEach((segment, i) => {
    const boldMatch = segment.match(/^\*\*(.+)\*\*$/);
    if (boldMatch) {
      // Render bold segments
      const inner = boldMatch[1].split('\n');
      inner.forEach((line, j) => {
        if (j > 0) parts.push(React.createElement('br', { key: `br-${i}-${j}` }));
        parts.push(React.createElement('strong', { key: `b-${i}-${j}` }, line));
      });
    } else {
      // Render plain text with newline support
      const lines = segment.split('\n');
      lines.forEach((line, j) => {
        if (j > 0) parts.push(React.createElement('br', { key: `br-${i}-${j}` }));
        if (line) parts.push(React.createElement(React.Fragment, { key: `t-${i}-${j}` }, line));
      });
    }
  });
  return parts;
}

function MiniChart({ type, data }) {
  if (!data || data.length === 0) return null;

  const isLine = type === 'line';
  const isBar = type === 'bar';
  const isPie = type === 'pie';

  if (isPie) {
    const COLORS = CHART_COLORS;
    return (
      <div className="chat-chart-wrapper pie">
        <ResponsiveContainer width="100%" height={120}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={25}
              outerRadius={45}
              paddingAngle={2}
              dataKey="value"
              nameKey="label"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', fontSize: 10, padding: '4px 8px' }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="chat-chart-legend">
          {data.slice(0, 4).map((d, i) => (
            <div key={i} className="legend-item">
              <span className="legend-dot" style={{ backgroundColor: COLORS[i % COLORS.length] }}></span>
              <span className="legend-label">{d.label}: {d.value}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="chat-chart-wrapper">
      <ResponsiveContainer width="100%" height={110}>
        {isLine ? (
          <LineChart data={data} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
            <XAxis dataKey="label" tick={{ fill: '#9898b8', fontSize: 8 }} />
            <YAxis tick={{ fill: '#9898b8', fontSize: 8 }} />
            <Tooltip
              contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', fontSize: 10, padding: '4px 8px' }}
            />
            <Line type="monotone" dataKey="value" stroke="#00d4ff" strokeWidth={1.5} dot={{ r: 1 }} activeDot={{ r: 3 }} />
          </LineChart>
        ) : (
          <BarChart data={data} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
            <XAxis dataKey="label" tick={{ fill: '#9898b8', fontSize: 8 }} />
            <YAxis tick={{ fill: '#9898b8', fontSize: 8 }} />
            <Tooltip
              contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', fontSize: 10, padding: '4px 8px' }}
            />
            <Bar dataKey="value" fill="#7c3aed" radius={[2, 2, 0, 0]}>
              {data.map((entry, index) => {
                return <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />;
              })}
            </Bar>
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}

export default function ChatBot() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'bot', text: "Hey! 👋 I'm **SmartBot**. Ask me anything about your store data — sales, inventory, customers, and more!\n\nTry a quick action below or type a question.", type: 'text' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [pulse, setPulse] = useState(true);
  const messagesEnd = useRef(null);
  const inputRef = useRef(null);
  const sessionId = useRef(crypto.randomUUID());

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (open) {
      setPulse(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [open]);

  async function sendMessage(text) {
    if (!text.trim()) return;
    const userMsg = { role: 'user', text: text.trim() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await api.sendChat(text.trim(), sessionId.current);
      setMessages(prev => [...prev, {
        role: 'bot',
        text: res.reply,
        type: res.type,
        suggestions: res.suggestions,
        chartType: res.chart_type,
        chartData: res.chart_data
      }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'bot', text: '❌ Failed to get response. Is the backend running?', type: 'error' }]);
    }
    setLoading(false);
  }

  function handleSubmit(e) {
    e.preventDefault();
    sendMessage(input);
  }

  return (
    <>
      {/* Floating Chat Button */}
      <button
        className={`chat-fab ${pulse ? 'pulse' : ''}`}
        onClick={() => setOpen(o => !o)}
        title="Chat with SmartBot"
      >
        {open ? '✕' : '💬'}
      </button>

      {/* Chat Window */}
      {open && (
        <div className="chat-window">
          <div className="chat-header">
            <div className="chat-header-info">
              <span className="chat-avatar">🤖</span>
              <div>
                <div className="chat-header-title">SmartBot</div>
                <div className="chat-header-sub">Store Data Assistant</div>
              </div>
            </div>
            <button className="chat-close" onClick={() => setOpen(false)}>✕</button>
          </div>

          <div className="chat-messages">
            {messages.map((m, i) => (
              <div key={i} className={`chat-msg-container ${m.role}`}>
                <div className={`chat-msg ${m.role}`}>
                  {m.role === 'bot' && <span className="chat-msg-avatar">🤖</span>}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxWidth: '85%' }}>
                    <div className={`chat-bubble ${m.role} ${m.type || ''}`}>
                      {renderMarkdown(m.text)}
                    </div>
                    {m.role === 'bot' && m.chartType && (
                      <MiniChart type={m.chartType} data={m.chartData} />
                    )}
                  </div>
                </div>
              </div>
            ))}
            {loading && (
              <div className="chat-msg bot">
                <span className="chat-msg-avatar">🤖</span>
                <div className="chat-bubble bot typing">
                  <span className="dot"></span><span className="dot"></span><span className="dot"></span>
                </div>
              </div>
            )}
            <div ref={messagesEnd} />
          </div>

          {/* Dynamic Suggestion Chips */}
          {!loading && messages.length > 0 && messages[messages.length - 1].role === 'bot' && messages[messages.length - 1].suggestions && messages[messages.length - 1].suggestions.length > 0 ? (
            <div className="chat-suggestions-container">
              {messages[messages.length - 1].suggestions.map((s, idx) => (
                <button
                  key={idx}
                  className="chat-suggestion-chip"
                  onClick={() => sendMessage(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          ) : (
            /* Fallback to Quick Actions on start */
            messages.length <= 1 && (
              <div className="chat-quick-actions">
                {QUICK_ACTIONS.map((a, i) => (
                  <button key={i} className="chat-quick-btn" onClick={() => sendMessage(a.msg)}>
                    {a.label}
                  </button>
                ))}
              </div>
            )
          )}

          <form className="chat-input-area" onSubmit={handleSubmit}>
            <input
              ref={inputRef}
              className="chat-input"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask about sales, stock, customers..."
              disabled={loading}
            />
            <button className="chat-send" type="submit" disabled={loading || !input.trim()}>
              ➤
            </button>
          </form>
        </div>
      )}
    </>
  );
}
