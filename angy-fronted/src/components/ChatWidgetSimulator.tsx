import React, { useState } from 'react';
import { CadCrosshair } from './CadCrosshair';
import { HelioLogo } from './HelioLogo';
import { HeronButton } from './HeronButton';
import { 
  Send, Bot, User, CheckCircle2, AlertTriangle, ArrowRight, 
  Terminal, Database, Network, GitBranch, Sparkles 
} from 'lucide-react';

interface CypherMessage {
  id: string;
  sender: 'user' | 'helio';
  text: string;
  timestamp: string;
  cypherQuery?: string;
  graphPath?: string[];
  honestNegative?: boolean;
}

export const ChatWidgetSimulator: React.FC = () => {
  const [messages, setMessages] = useState<CypherMessage[]>([
    {
      id: 'm1',
      sender: 'helio',
      text: "Helio Cypher Agent initialized. Connected to FalkorDB on port 6379. Graph loaded: 120 Persons, 20 Services, 5 Teams, 40 Decisions.",
      timestamp: '14:48:01'
    },
    {
      id: 'm2',
      sender: 'user',
      text: 'Who knows about payments-gateway, what breaks if it goes down, and who gets paged?',
      timestamp: '14:48:15'
    },
    {
      id: 'm3',
      sender: 'helio',
      text: "The Platform team owns payments-gateway. Ravi Menon has worked on it most recently (2026-09-28). Priya Sharma has the most commits (14), but her last touch was 2026-04-15 and is flagged as stale. Ask Ravi Menon.\n\nBlast radius: 4 services cascade fail (checkout-api, ledger-service, fraud-engine, subscription-worker). On-call engineer to page: Ravi Menon.",
      timestamp: '14:48:18',
      cypherQuery: "MATCH (s:Service {name: 'payments-gateway'})-[:OWNED_BY]->(t:Team)\nMATCH (s)-[:HAS_DEPENDENT*1..2]->(d:Service)\nMATCH (t)<-[:ON_CALL]-(m:Person)\nRETURN s, t, d, m",
      graphPath: ["payments-gateway", "OWNED_BY", "Platform", "ON_CALL", "Ravi Menon", "HAS_DEPENDENT", "checkout-api"]
    }
  ]);

  const [inputVal, setInputVal] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const predefinedAnswers: Record<string, { text: string; cypher: string; path: string[]; honestNegative?: boolean }> = {
    'config': {
      text: "The graph contains no OWNED_BY edge for config-service. No team owns it. This is a structural unowned service.",
      cypher: "MATCH (s:Service {name: 'config-service'})\nOPTIONAL MATCH (s)-[:OWNED_BY]->(t:Team)\nRETURN s.name, t.name",
      path: ["config-service", "OWNED_BY (NULL)", "NO OWNER FOUND"],
      honestNegative: true
    },
    'stripe': {
      text: "The March document claiming 'single provider, Stripe' is stale and superseded. Decision D-19 (2026-05-06, authored by Elena Vasquez) established dual provider: Adyen primary, Stripe fallback.",
      cypher: "MATCH (d:Decision {id: 'D-19'})-[:SUPERSEDES]->(doc:Document)\nRETURN d.summary, doc.name, d.status",
      path: ["Decision D-19", "SUPERSEDES", "March Single-Provider Doc", "Adyen Primary"]
    },
    'ledger': {
      text: "The Ledger team owns ledger-service. Ravi Menon and Diego Alvarez are both on the rotation. Diego Alvarez is ON_CALL this week.",
      cypher: "MATCH (t:Team {name: 'Ledger'})<-[:ON_CALL]-(m:Person:Member)\nWHERE m.on_call_week = date()\nRETURN m.name",
      path: ["Ledger Team", "ON_CALL (Current Week)", "Diego Alvarez"]
    }
  };

  const handleSend = (overrideText?: string) => {
    const q = overrideText || inputVal;
    if (!q.trim()) return;

    const userMsg: CypherMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!overrideText) setInputVal('');
    setIsTyping(true);

    setTimeout(() => {
      setIsTyping(false);
      let matched = predefinedAnswers['config'];
      const lower = q.toLowerCase();
      if (lower.includes('stripe') || lower.includes('decision') || lower.includes('provider')) {
        matched = predefinedAnswers['stripe'];
      } else if (lower.includes('ledger') || lower.includes('on call') || lower.includes('diego')) {
        matched = predefinedAnswers['ledger'];
      } else if (!lower.includes('config') && !lower.includes('own')) {
        matched = {
          text: `Traversed FalkorDB for "${q}". Returned exact entity path with 100% ground-truth confidence.`,
          cypher: `MATCH (n {name: '${q.slice(0, 16)}'})-[r*1..2]-(m) RETURN n, r, m`,
          path: [q.slice(0, 16), "TRAVERSED", "FalkorDB Engine"]
        };
      }

      const botResponse: CypherMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'helio',
        text: matched.text,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        cypherQuery: matched.cypher,
        graphPath: matched.path,
        honestNegative: matched.honestNegative
      };

      setMessages((prev) => [...prev, botResponse]);
    }, 1000);
  };

  return (
    <div className="max-w-4xl mx-auto my-8 p-4 md:p-8 select-none">
      
      {/* Top Header */}
      <div className="bg-[#282828] text-white p-4 cad-border flex items-center justify-between font-mono text-xs">
        <div className="flex items-center gap-3">
          <span className="w-2.5 h-2.5 rounded-full bg-[#e15c46] animate-pulse" />
          <span className="font-bold tracking-wider">HELIO NATURAL LANGUAGE CYPHER AGENT</span>
        </div>
        <div className="flex items-center gap-4 text-white/60 text-[11px]">
          <span>ENGINE: FALKORDB</span>
          <span>•</span>
          <span className="text-[#e15c46]">GROUND-TRUTH VERIFIED</span>
        </div>
      </div>

      {/* Main Chat Box Container */}
      <div className="bg-[#f4f4ec] cad-border p-6 relative">
        <CadCrosshair position="tl" />
        <CadCrosshair position="tr" />
        <CadCrosshair position="bl" />
        <CadCrosshair position="br" />

        {/* Message Log */}
        <div className="h-[460px] overflow-y-auto space-y-4 pr-2 font-mono text-xs">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
            >
              <div className="flex items-center gap-2 mb-1 text-[10px] text-[#5c5c56]">
                {m.sender === 'user' ? (
                  <>
                    <span>ENGINEER (YOU)</span>
                    <User className="w-3 h-3 text-[#282828]" />
                  </>
                ) : (
                  <>
                    <Bot className="w-3 h-3 text-[#e15c46]" />
                    <span className="text-[#e15c46] font-bold">HELIO GRAPH BRAIN</span>
                  </>
                )}
                <span>[{m.timestamp}]</span>
              </div>

              {/* Message Bubble */}
              <div
                className={`max-w-[85%] p-4 cad-border leading-relaxed whitespace-pre-line ${
                  m.sender === 'user'
                    ? 'bg-[#282828] text-white'
                    : m.honestNegative
                    ? 'bg-amber-50 text-[#282828] border-amber-500'
                    : 'bg-[#ecece4] text-[#282828]'
                }`}
              >
                {m.text}

                {/* Graph Path Chips */}
                {m.graphPath && (
                  <div className="mt-3 pt-3 cad-border-t border-[#282828]/15">
                    <div className="text-[10px] text-[#5c5c56] font-bold uppercase mb-1.5 flex items-center gap-1">
                      <Network className="w-3 h-3 text-[#e15c46]" />
                      <span>TRAVERSED GRAPH PATH:</span>
                    </div>
                    <div className="flex flex-wrap gap-1 text-[10px]">
                      {m.graphPath.map((node, i) => (
                        <span
                          key={i}
                          className={`px-2 py-0.5 cad-border font-bold ${
                            i % 2 === 1
                              ? 'bg-[#e15c46] text-white'
                              : 'bg-white text-[#282828]'
                          }`}
                        >
                          {node}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Cypher Query Box */}
                {m.cypherQuery && (
                  <div className="mt-3 p-2.5 bg-[#1c1c1b] text-emerald-400 font-mono text-[10px] cad-border overflow-x-auto">
                    <div className="text-white/40 pb-1 font-bold uppercase">
                      CYPHER TRAVERSAL:
                    </div>
                    <pre>{m.cypherQuery}</pre>
                  </div>
                )}
              </div>
            </div>
          ))}

          {isTyping && (
            <div className="flex items-center gap-2 text-xs font-mono text-[#e15c46] pt-2">
              <Sparkles className="w-4 h-4 animate-spin" />
              <span>Helio is generating Cypher and traversing FalkorDB edges...</span>
            </div>
          )}
        </div>

        {/* Prompt Input */}
        <div className="mt-6 pt-4 cad-border-t flex items-center gap-3">
          <input
            type="text"
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask Helio (e.g. 'Who owns config-service?' or 'Is Stripe decision current?')..."
            className="flex-1 bg-white cad-border px-4 py-2.5 font-mono text-xs text-[#282828] placeholder:text-[#5c5c56]/60 focus:outline-none focus:border-[#e15c46]"
          />
          <HeronButton variant="brand" size="md" onClick={() => handleSend()} icon={false}>
            <Send className="w-4 h-4" />
          </HeronButton>
        </div>

        {/* Quick Ground Truth Question Chips */}
        <div className="mt-3 flex flex-wrap gap-2 text-[10px] font-mono text-[#5c5c56]">
          <span className="font-bold text-[#282828]">Planted Questions:</span>
          <button
            onClick={() => handleSend("Who owns config-service?")}
            className="bg-[#ecece4] px-2 py-0.5 cad-border hover:bg-[#e15c46] hover:text-white"
          >
            Fact 04: Who owns config-service?
          </button>
          <button
            onClick={() => handleSend("Is single-provider Stripe decision current?")}
            className="bg-[#ecece4] px-2 py-0.5 cad-border hover:bg-[#e15c46] hover:text-white"
          >
            Fact 09: Stripe vs Adyen Decision
          </button>
          <button
            onClick={() => handleSend("Who is on call for Ledger this week?")}
            className="bg-[#ecece4] px-2 py-0.5 cad-border hover:bg-[#e15c46] hover:text-white"
          >
            Fact 11: Ledger On-Call Person
          </button>
        </div>

      </div>

    </div>
  );
};
