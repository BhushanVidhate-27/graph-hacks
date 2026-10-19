import React, { useState } from 'react';
import { CadCrosshair } from './CadCrosshair';
import { HeronLogo } from './HeronLogo';
import { HeronButton } from './HeronButton';
import { 
  Send, Bot, User, CheckCircle2, AlertTriangle, ArrowRight, 
  RotateCcw, Sparkles, Terminal, Layers, Box, Cpu 
} from 'lucide-react';

interface ChatMessage {
  id: string;
  sender: 'user' | 'heron';
  text: string;
  timestamp: string;
  actionProposal?: {
    code: string;
    target: string;
    details: string;
    status: 'pending' | 'approved' | 'rejected';
  };
}

export const ChatWidgetSimulator: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'm1',
      sender: 'heron',
      text: "Heron CAD Agent initialized. Connected to active Autodesk Revit 2025 document 'Denver_Atrium_Tower_Rev4.rvt'. Monitoring 1,420 model elements.",
      timestamp: '14:28:01'
    },
    {
      id: 'm2',
      sender: 'user',
      text: 'Scan Level 3 conference room corridor for IBC egress clearance.',
      timestamp: '14:28:15'
    },
    {
      id: 'm3',
      sender: 'heron',
      text: "Scan complete. Detected 1 code conflict under IBC 1010.1.2.1. In Level 3 Room 304, the door leaf encroaches 9.2 inches into the required 44-inch egress corridor when fully opened.",
      timestamp: '14:28:18',
      actionProposal: {
        code: 'IBC 1010.1.2.1',
        target: 'Door [ID: 849201 - 36"x84" Single Flush]',
        details: 'Reverse swing direction into room interior to maintain 44" unobstructed corridor egress.',
        status: 'pending'
      }
    }
  ]);

  const [inputVal, setInputVal] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const handleSend = () => {
    if (!inputVal.trim()) return;
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: inputVal,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputVal('');
    setIsTyping(true);

    setTimeout(() => {
      setIsTyping(false);
      const botResponse: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'heron',
        text: `Understood. I have inspected the relevant elements for "${userMsg.text}". All geometric parameters align with municipal codes. Proposed transaction prepared for your review.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        actionProposal: {
          code: 'IBC 1015.3',
          target: 'Balcony Railing [ID: 994012]',
          details: 'Increase top rail height from 36" to 42" above finished floor.',
          status: 'pending'
        }
      };
      setMessages((prev) => [...prev, botResponse]);
    }, 1200);
  };

  const handleAction = (msgId: string, status: 'approved' | 'rejected') => {
    setMessages((prev) =>
      prev.map((m) =>
        m.id === msgId && m.actionProposal
          ? { ...m, actionProposal: { ...m.actionProposal, status } }
          : m
      )
    );
  };

  return (
    <div className="max-w-4xl mx-auto my-8 p-4 md:p-8 select-none">
      
      {/* Top Header */}
      <div className="bg-[#282828] text-white p-4 cad-border flex items-center justify-between font-mono text-xs">
        <div className="flex items-center gap-3">
          <span className="w-2.5 h-2.5 rounded-full bg-[#e15c46] animate-pulse" />
          <span className="font-bold tracking-wider">HERON IN-TOOL HUD // SIMULATOR</span>
        </div>
        <div className="flex items-center gap-4 text-white/60 text-[11px]">
          <span>TARGET: AUTODESK REVIT v2025</span>
          <span>•</span>
          <span className="text-[#e15c46]">IPC CONNECTED</span>
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
                    <span>ARCHITECT (YOU)</span>
                    <User className="w-3 h-3 text-[#282828]" />
                  </>
                ) : (
                  <>
                    <Bot className="w-3 h-3 text-[#e15c46]" />
                    <span className="text-[#e15c46] font-bold">HERON AI AGENT</span>
                  </>
                )}
                <span>[{m.timestamp}]</span>
              </div>

              {/* Message Bubble */}
              <div
                className={`max-w-[85%] p-4 cad-border leading-relaxed ${
                  m.sender === 'user'
                    ? 'bg-[#282828] text-white'
                    : 'bg-[#ecece4] text-[#282828]'
                }`}
              >
                {m.text}

                {/* If Heron proposed an edit */}
                {m.actionProposal && (
                  <div className="mt-4 pt-4 cad-border-t border-[#282828]/20 bg-[#f4f4ec] p-3 text-[11px] text-[#282828]">
                    <div className="flex items-center justify-between mb-2">
                      <span className="bg-[#e15c46] text-white px-2 py-0.5 font-bold text-[10px]">
                        {m.actionProposal.code}
                      </span>
                      <span className="font-bold text-[#5c5c56]">
                        {m.actionProposal.target}
                      </span>
                    </div>

                    <p className="text-[#282828] mb-3 leading-normal font-medium">
                      {m.actionProposal.details}
                    </p>

                    {m.actionProposal.status === 'pending' ? (
                      <div className="flex items-center gap-2 pt-2 cad-border-t border-[#282828]/10">
                        <button
                          onClick={() => handleAction(m.id, 'approved')}
                          className="flex-1 py-1.5 bg-[#e15c46] text-white hover:bg-[#282828] font-bold text-[11px] cad-border transition-colors uppercase tracking-wider"
                        >
                          Approve & Commit Edit
                        </button>
                        <button
                          onClick={() => handleAction(m.id, 'rejected')}
                          className="px-3 py-1.5 bg-transparent text-[#5c5c56] hover:bg-[#282828]/10 font-bold text-[11px] cad-border transition-colors uppercase"
                        >
                          Dismiss
                        </button>
                      </div>
                    ) : m.actionProposal.status === 'approved' ? (
                      <div className="flex items-center gap-2 text-emerald-700 font-bold text-[11px] pt-1">
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Committed to model database (Revit Transaction #9401)</span>
                      </div>
                    ) : (
                      <div className="text-[#5c5c56] italic text-[11px] pt-1">
                        Proposal rejected by user.
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}

          {isTyping && (
            <div className="flex items-center gap-2 text-xs font-mono text-[#e15c46] pt-2">
              <Sparkles className="w-4 h-4 animate-spin" />
              <span>Heron is querying active BIM geometry...</span>
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
            placeholder="Instruct Heron (e.g. 'Check stair handrail returns on stair 2' or 'Verify ADA turn circle in washroom')..."
            className="flex-1 bg-white cad-border px-4 py-2.5 font-mono text-xs text-[#282828] placeholder:text-[#5c5c56]/60 focus:outline-none focus:border-[#e15c46]"
          />
          <HeronButton variant="brand" size="md" onClick={handleSend} icon={false}>
            <Send className="w-4 h-4" />
          </HeronButton>
        </div>

        {/* Quick Suggestion Chips */}
        <div className="mt-3 flex flex-wrap gap-2 text-[10px] font-mono text-[#5c5c56]">
          <span className="font-bold text-[#282828]">Quick Commands:</span>
          <button
            onClick={() => setInputVal("Audit atrium balcony glass rail for IBC 1015.3 height")}
            className="bg-[#ecece4] px-2 py-0.5 cad-border hover:bg-[#e15c46] hover:text-white"
          >
            Check Balcony Railing
          </button>
          <button
            onClick={() => setInputVal("Verify 60 inch turning radius in Restroom ADA-01")}
            className="bg-[#ecece4] px-2 py-0.5 cad-border hover:bg-[#e15c46] hover:text-white"
          >
            Verify ADA Turning Space
          </button>
          <button
            onClick={() => setInputVal("Calculate travel distance to nearest exit stair")}
            className="bg-[#ecece4] px-2 py-0.5 cad-border hover:bg-[#e15c46] hover:text-white"
          >
            Calculate Exit Travel Distance
          </button>
        </div>

      </div>

    </div>
  );
};
