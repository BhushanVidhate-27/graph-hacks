import React, { useState, useRef } from 'react';
import { CadCrosshair } from './CadCrosshair';
import { HeronButton } from './HeronButton';
import { 
  Network, AlertTriangle, CheckCircle2, ShieldCheck, 
  Terminal, User, Activity, AlertOctagon, Share2, Layers 
} from 'lucide-react';
import { DependencyNode } from '../types';

export const ViolationInspector: React.FC = () => {
  const [sliderPos, setSliderPos] = useState(52); // percentage
  const [isDragging, setIsDragging] = useState(false);
  const [activeNodeId, setActiveNodeId] = useState<string>('n1');

  const nodes: DependencyNode[] = [
    {
      id: 'n1',
      name: 'payments-gateway',
      category: 'critical-path',
      tier: 'Tier 1 (Critical)',
      owningTeam: 'Platform Team',
      onCall: 'Ravi Menon (Active)',
      blastRadius: ['checkout-api', 'ledger-service', 'fraud-engine', 'subscription-worker'],
      hopDepth: 3,
      status: 'healthy',
      cypherQuery: "MATCH (s:Service {name: 'payments-gateway'})-[:HAS_DEPENDENT*1..3]->(downstream)\nMATCH (s)-[:OWNED_BY]->(t:Team)<-[:ON_CALL]-(m:Person)\nRETURN s, downstream, t, m",
      summary: "Priya Sharma has 14 commits (departed April 2026, stale). Ravi Menon committed recently (2026-09-28). Ask Ravi Menon. 4 downstream services will fail if this goes down.",
      groundTruthFact: "Fact 01 & Fact 08: Volume trap vs recency resolved.",
      x: 35,
      y: 42
    },
    {
      id: 'n2',
      name: 'config-service',
      category: 'unowned',
      tier: 'Tier 2 (Internal)',
      owningTeam: 'NO TEAM OWNS THIS SERVICE',
      onCall: 'No rotation assigned',
      blastRadius: ['auth-service', 'user-profile-service'],
      hopDepth: 2,
      status: 'orphan',
      cypherQuery: "MATCH (s:Service {name: 'config-service'})\nOPTIONAL MATCH (s)-[:OWNED_BY]->(t:Team)\nRETURN s.name, t.name // Returns NULL for t",
      summary: "The graph contains no OWNED_BY edge for config-service. Helio explicitly reports no owner exists, refusing to hallucinate an owner.",
      groundTruthFact: "Fact 04: The failure test. Confident honest negative.",
      x: 72,
      y: 28
    },
    {
      id: 'n3',
      name: 'decision-d19',
      category: 'provenance',
      tier: 'Architecture Decision Record',
      owningTeam: 'Architecture Review Board',
      onCall: 'Elena Vasquez (Author)',
      blastRadius: ['payments-gateway', 'stripe-connector', 'adyen-vault'],
      hopDepth: 2,
      status: 'superseded',
      cypherQuery: "MATCH (d:Decision {id: 'D-19'})-[:SUPERSEDES]->(old:Document)\nRETURN d.summary, old.name, d.status",
      summary: "March docs claimed single-provider Stripe. Decision D-19 (2026-05-06) established dual-provider: Adyen primary, Stripe fallback. Helio surfaces this superseding path.",
      groundTruthFact: "Fact 09: Contradiction resolution via SUPERSEDES edge.",
      x: 52,
      y: 75
    },
    {
      id: 'n4',
      name: 'ledger-service',
      category: 'stale-edge',
      tier: 'Tier 1 (Financial Core)',
      owningTeam: 'Ledger Team',
      onCall: 'Diego Alvarez (This Week)',
      blastRadius: ['audit-pipeline', 'reconciliation-worker'],
      hopDepth: 2,
      status: 'healthy',
      cypherQuery: "MATCH (t:Team {name: 'Ledger'})<-[:ON_CALL]-(m:Person:Member)\nWHERE m.on_call_week = date()\nRETURN m.name // Diego Alvarez, NOT Ravi or Priya",
      summary: "Ravi Menon and Diego Alvarez are both on rotation. Diego is on call this week. Priya Sharma is on no rotation at all.",
      groundTruthFact: "Fact 11: Rotation membership vs active weekly on-call.",
      x: 22,
      y: 65
    }
  ];

  const containerRef = useRef<HTMLDivElement>(null);

  const handlePointerDown = () => setIsDragging(true);
  const handlePointerUp = () => setIsDragging(false);

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isDragging || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = Math.min(Math.max((x / rect.width) * 100, 5), 95);
    setSliderPos(percentage);
  };

  const currentNode = nodes.find((n) => n.id === activeNodeId) || nodes[0];

  return (
    <section id="inspector-section" className="relative w-full py-16 md:py-24 px-4 md:px-8 max-w-7xl mx-auto select-none">
      
      {/* Header bar */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8 cad-border-b pb-6">
        <div>
          <div className="flex items-center gap-2 text-[#e15c46] font-mono text-xs font-bold uppercase tracking-widest mb-2">
            <Network className="w-4 h-4" />
            <span>001 // Interactive Graph Topology & Blast Radius</span>
          </div>
          <h2 className="text-3xl md:text-5xl font-mono font-bold tracking-tight text-[#282828] uppercase">
            Click & drag to contrast<br />flat search vs. graph traversal
          </h2>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono text-[#5c5c56]">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-[#e15c46] inline-block border border-[#282828]" />
            <span>FLAT KEYWORD SEARCH (STALE / TRAPPED)</span>
          </div>
          <span>•</span>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-[#282828] inline-block border border-[#282828]" />
            <span>HELIO FALKORDB CYPHER (GROUND TRUTH)</span>
          </div>
        </div>
      </div>

      {/* Main Interactive Canvas Container */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Left 8 Cols: Interactive Split Canvas */}
        <div className="lg:col-span-8 relative">
          <div
            ref={containerRef}
            onPointerDown={handlePointerDown}
            onPointerUp={handlePointerUp}
            onPointerLeave={handlePointerUp}
            onPointerMove={handlePointerMove}
            className="relative w-full aspect-[4/3] md:aspect-[16/10] bg-[#1c1c1b] cad-border overflow-hidden cursor-ew-resize select-none"
          >
            <CadCrosshair position="tl" />
            <CadCrosshair position="tr" />
            <CadCrosshair position="bl" />
            <CadCrosshair position="br" />

            {/* Background Layer: Ground Truth Graph Topology */}
            <div className="absolute inset-0 w-full h-full p-8 flex flex-col justify-between cad-grid-pattern bg-[#181817]">
              
              {/* Topology SVG Lines connecting nodes */}
              <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-50">
                <line x1="35%" y1="42%" x2="72%" y2="28%" stroke="#e15c46" strokeWidth="1.5" strokeDasharray="4 4" />
                <line x1="35%" y1="42%" x2="52%" y2="75%" stroke="#ffffff" strokeWidth="1.5" />
                <line x1="35%" y1="42%" x2="22%" y2="65%" stroke="#ffffff" strokeWidth="2" />
                <line x1="22%" y1="65%" x2="52%" y2="75%" stroke="#ffffff" strokeWidth="1" strokeDasharray="2 2" />
              </svg>

              <div className="flex justify-between items-start z-10">
                <span className="bg-[#282828]/90 text-white font-mono text-[10px] px-2.5 py-1 cad-border uppercase tracking-widest backdrop-blur-sm">
                  FALKORDB CYPHER TRAVERSAL // 20 VERIFIED NODES
                </span>
                <span className="text-[10px] text-white/50 font-mono">
                  GROUND TRUTH: PASS
                </span>
              </div>

              {/* Node Badges on Graph Layer */}
              {nodes.map((node) => (
                <button
                  key={node.id}
                  onClick={(e) => {
                    e.stopPropagation();
                    setActiveNodeId(node.id);
                  }}
                  style={{ top: `${node.y}%`, left: `${node.x}%` }}
                  className={`absolute -translate-x-1/2 -translate-y-1/2 z-20 transition-all duration-300 ${
                    activeNodeId === node.id ? 'scale-125 z-30 ring-2 ring-white' : 'hover:scale-110'
                  }`}
                >
                  <div className={`px-2.5 py-1.5 font-mono text-[10px] font-bold uppercase tracking-tight flex items-center gap-1.5 shadow-2xl cad-border ${
                    node.category === 'unowned'
                      ? 'bg-amber-600 text-white border-amber-400'
                      : node.category === 'provenance'
                      ? 'bg-purple-700 text-white border-purple-400'
                      : 'bg-[#e15c46] text-white border-black'
                  }`}>
                    <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping" />
                    <span>{node.name}</span>
                  </div>
                </button>
              ))}

              <div className="z-10 text-[10px] font-mono text-white/40 flex justify-between">
                <span>TRAVERSAL: HAS_DEPENDENT + SUPERSEDES</span>
                <span>FALKORDB PORT 6379</span>
              </div>
            </div>

            {/* Foreground Layer: Naive Flat Search Trap (Clipped by slider) */}
            <div
              className="absolute inset-0 w-full h-full overflow-hidden bg-[#262624]"
              style={{ clipPath: `inset(0 ${100 - sliderPos}% 0 0)` }}
            >
              <div className="absolute inset-0 p-8 flex flex-col justify-between font-mono text-xs">
                
                <div className="flex justify-between items-start">
                  <span className="bg-[#e15c46] text-white font-mono text-[10px] px-2.5 py-1 cad-border uppercase tracking-widest shadow-lg">
                    NAIVE FLAT SEARCH // TRAPS & STALE DOCUMENTS
                  </span>
                </div>

                {/* Stale Text Callouts */}
                <div className="space-y-4 max-w-sm text-white/80 text-[11px] bg-black/60 p-4 cad-border backdrop-blur-md">
                  <div className="text-[#e15c46] font-bold">⚠️ NAIVE RANK TRAP 01:</div>
                  <div>"Priya Sharma has 14 commits on payments-gateway. Returns Priya as #1 expert (she left 6 months ago)."</div>
                  
                  <div className="text-amber-400 font-bold pt-2 cad-border-t border-white/20">⚠️ CONTRADICTION TRAP 02:</div>
                  <div>"March document found: 'Single provider, Stripe.' Misses Decision D-19 completely."</div>

                  <div className="text-red-400 font-bold pt-2 cad-border-t border-white/20">⚠️ HALLUCINATION TRAP 03:</div>
                  <div>"Asked who owns config-service: LLM invents an owner rather than admitting no edge exists."</div>
                </div>

                <div className="text-[10px] text-white/40">
                  KEYWORD TF-IDF // NO EDGE RELATIONS
                </div>
              </div>
            </div>

            {/* Split Drag Line Divider */}
            <div
              className="absolute top-0 bottom-0 w-[2px] bg-white shadow-[0_0_12px_rgba(255,255,255,0.8)] z-30 pointer-events-none"
              style={{ left: `${sliderPos}%` }}
            >
              <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-[#e15c46] border-2 border-white flex items-center justify-center text-white shadow-xl">
                <div className="flex gap-0.5">
                  <div className="w-0.5 h-3 bg-white" />
                  <div className="w-0.5 h-3 bg-white" />
                </div>
              </div>
            </div>

            {/* Bottom instruction hint */}
            <div className="absolute bottom-3 left-1/2 -translate-x-1/2 bg-[#282828]/90 text-white text-[11px] font-mono px-4 py-1 rounded-full pointer-events-none backdrop-blur-sm z-30">
              ◄ DRAG TO REVEAL HOW GRAPH SOLVES THE TRAPS ►
            </div>
          </div>
        </div>

        {/* Right 4 Cols: Active Node Blast Radius Panel */}
        <div className="lg:col-span-4 bg-[#f4f4ec] cad-border p-6 relative">
          <CadCrosshair position="tl" />
          <CadCrosshair position="tr" />
          <CadCrosshair position="bl" />
          <CadCrosshair position="br" />

          <div className="flex items-center justify-between pb-4 cad-border-b mb-5 font-mono">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 bg-[#e15c46]" />
              <span className="text-xs font-bold text-[#e15c46] uppercase">Node Traversal Details</span>
            </div>
            <span className="text-[11px] text-[#5c5c56]">{currentNode.tier}</span>
          </div>

          {/* Node Title */}
          <div className="mb-4 font-mono">
            <div className="inline-block bg-[#e15c46]/10 text-[#e15c46] text-xs font-bold px-2 py-0.5 cad-border mb-2 uppercase">
              {currentNode.category}
            </div>
            <h3 className="font-bold text-xl text-[#282828] uppercase leading-tight">
              {currentNode.name}
            </h3>
            <div className="text-[11px] text-[#5c5c56] mt-1">
              OWNER: <span className="font-bold text-[#282828]">{currentNode.owningTeam}</span>
            </div>
            <div className="text-[11px] text-[#5c5c56]">
              ON-CALL: <span className="font-bold text-[#e15c46]">{currentNode.onCall}</span>
            </div>
          </div>

          {/* Ground truth analysis */}
          <p className="text-[12px] font-mono text-[#5c5c56] leading-relaxed mb-4">
            {currentNode.summary}
          </p>

          {/* Blast Radius Impact Chips */}
          <div className="bg-[#ecece4] cad-border p-3.5 mb-4 font-mono text-xs">
            <div className="font-bold text-[#282828] text-[11px] uppercase mb-2 flex items-center justify-between">
              <span>DOWNSTREAM BLAST RADIUS:</span>
              <span className="text-[#e15c46]">{currentNode.blastRadius.length} IMPACTED</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {currentNode.blastRadius.map((dep, idx) => (
                <span key={idx} className="bg-white px-2 py-0.5 cad-border text-[10px] text-[#282828]">
                  → {dep}
                </span>
              ))}
            </div>
          </div>

          {/* Executed Cypher Query Box */}
          <div className="bg-[#1c1c1b] text-emerald-400 p-3 cad-border font-mono text-[10px] leading-tight mb-5 overflow-x-auto">
            <div className="text-white/40 pb-1 mb-1 border-b border-white/10 font-bold uppercase">
              CYPHER QUERY EXECUTED:
            </div>
            <pre>{currentNode.cypherQuery}</pre>
          </div>

          {/* Ground Truth Citation */}
          <div className="pt-2 cad-border-t border-[#282828]/15 flex items-center justify-between font-mono text-[10px] text-[#5c5c56]">
            <span>{currentNode.groundTruthFact}</span>
            <span className="text-emerald-700 font-bold">VERIFIED</span>
          </div>

          {/* Node Picker Tabs */}
          <div className="grid grid-cols-4 gap-1 mt-4">
            {nodes.map((n, i) => (
              <button
                key={n.id}
                onClick={() => setActiveNodeId(n.id)}
                className={`py-1.5 font-mono text-[10px] font-bold cad-border transition-colors truncate px-1 ${
                  activeNodeId === n.id
                    ? 'bg-[#282828] text-white'
                    : 'bg-white text-[#282828] hover:bg-[#e15c46] hover:text-white'
                }`}
              >
                0{i + 1}
              </button>
            ))}
          </div>

        </div>

      </div>

    </section>
  );
};
