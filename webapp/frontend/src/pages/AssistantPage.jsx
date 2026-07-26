import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, FileText, Ticket, Star } from 'lucide-react';
import api from '../api';

const EXAMPLE_QUESTIONS = [
  "How long do customers have to return an item?",
  "Can loyalty points be combined with a promo code?",
  "What's our policy on damaged or defective items?",
  "Customer 43677 has an open ticket about late delivery — refund or discount?",
];

const SOURCE_ICON = { kb_article: FileText, ticket: Ticket, review: Star };

function Citation({ c }) {
  const Icon = SOURCE_ICON[c.source_type] || FileText;
  return (
    <div className="citation-card">
      <div className="citation-head">
        <Icon size={13} />
        <span>[{c.ref}] {c.source_type.replace('_', ' ')} · {c.source_id}</span>
      </div>
      <div className="citation-snippet">{c.snippet}</div>
    </div>
  );
}

export default function AssistantPage() {
  const [question, setQuestion] = useState('');
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history, loading]);

  async function submit(q) {
    const text = (q ?? question).trim();
    if (!text || loading) return;
    setQuestion('');
    setLoading(true);
    setHistory((h) => [...h, { question: text, answer: null, citations: [] }]);
    try {
      const res = await api.post('/assistant/ask/', { question: text });
      setHistory((h) => {
        const copy = [...h];
        copy[copy.length - 1] = { question: text, answer: res.data.answer, citations: res.data.citations };
        return copy;
      });
    } catch (e) {
      setHistory((h) => {
        const copy = [...h];
        copy[copy.length - 1] = { question: text, answer: 'Something went wrong answering that — check the backend log.', citations: [], error: true };
        return copy;
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="assistant-page">
      <h2>AI Assistant</h2>
      <p className="section-desc">
        Ask a support or analyst question. Answers combine vector search over support tickets, product reviews,
        and internal policy docs with live lookups against structured order/customer data — synthesized by Gemini,
        with every claim traceable back to a source below.
      </p>

      {history.length === 0 && (
        <div className="example-chips">
          {EXAMPLE_QUESTIONS.map((q) => (
            <button key={q} className="chip" onClick={() => submit(q)}>{q}</button>
          ))}
        </div>
      )}

      <div className="chat-thread">
        {history.map((turn, i) => (
          <div key={i} className="chat-turn">
            <div className="chat-bubble user">
              <User size={15} />
              <span>{turn.question}</span>
            </div>
            <div className="chat-bubble bot">
              <Bot size={15} />
              <div>
                {turn.answer === null ? (
                  <span className="typing">Thinking…</span>
                ) : (
                  <>
                    <p className={turn.error ? 'error-state' : ''}>{turn.answer}</p>
                    {turn.citations.length > 0 && (
                      <div className="citation-grid">
                        {turn.citations.map((c) => <Citation key={c.ref} c={c} />)}
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input-bar">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && submit()}
          placeholder="Ask about policies, tickets, reviews, or a specific customer..."
          disabled={loading}
        />
        <button onClick={() => submit()} disabled={loading || !question.trim()}>
          <Send size={16} />
        </button>
      </div>
    </div>
  );
}
