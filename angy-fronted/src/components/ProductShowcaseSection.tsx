import React from 'react';
import { HeronButton } from './HeronButton';
import { CadCrosshair } from './CadCrosshair';
import { Terminal, Database, CheckSquare, Sparkles, Layers, GitFork } from 'lucide-react';
import { ViewMode } from '../types';

interface ProductShowcaseSectionProps {
  onSelectMode: (mode: ViewMode) => void;
}

export const ProductShowcaseSection: React.FC<ProductShowcaseSectionProps> = ({ onSelectMode }) => {
  return (
    <section className="relative w-full py-16 md:py-24 px-4 md:px-8 max-w-7xl mx-auto select-none">
      
      <div className="text-[#e15c46] font-mono text-xs font-bold uppercase tracking-widest mb-2">
        CAPABILITIES // THE GRAPH INTERFACES
      </div>
      <h2 className="text-3xl md:text-5xl font-mono font-bold tracking-tight text-[#282828] uppercase leading-tight mb-12">
        One graph. Two powerful lenses.
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Product 01: Helio Cypher Agent */}
        <div className="bg-[#f4f4ec] cad-border p-8 relative flex flex-col justify-between">
          <CadCrosshair position="tl" />
          <CadCrosshair position="tr" />
          <CadCrosshair position="bl" />
          <CadCrosshair position="br" />

          <div>
            <div className="flex items-center justify-between font-mono text-xs text-[#5c5c56] mb-4">
              <span className="text-[#e15c46] font-bold">[01] CYPHER AGENT</span>
              <span>NATURAL LANGUAGE → GRAPH</span>
            </div>

            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-[#e15c46] text-white flex items-center justify-center cad-border">
                <Terminal className="w-5 h-5" />
              </div>
              <h3 className="font-mono font-bold text-2xl text-[#282828] uppercase">
                Helio Natural Language Agent
              </h3>
            </div>

            <p className="font-mono text-sm text-[#5c5c56] leading-relaxed mb-6">
              Ask complex organizational questions in plain English. Helio maps your intent into Cypher queries,
              traverses FalkorDB edges, and returns verified paths with zero hallucination.
            </p>

            <div className="space-y-2.5 font-mono text-xs text-[#282828] mb-8 bg-[#ecece4] p-4 cad-border">
              <div className="flex items-center gap-2">
                <CheckSquare className="w-4 h-4 text-[#e15c46]" />
                <span>Translates questions into multi-hop Cypher queries automatically</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckSquare className="w-4 h-4 text-[#e15c46]" />
                <span>Displays full path chips: Person → CONTRIBUTED_TO → Service</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckSquare className="w-4 h-4 text-[#e15c46]" />
                <span>Answers unowned nodes cleanly: "The graph contains no OWNED_BY edge"</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <HeronButton variant="brand" onClick={() => onSelectMode('chat-widget')}>
              Launch Agent Simulator
            </HeronButton>
          </div>
        </div>

        {/* Product 02: Helio FalkorDB Console */}
        <div className="bg-[#f4f4ec] cad-border p-8 relative flex flex-col justify-between">
          <CadCrosshair position="tl" />
          <CadCrosshair position="tr" />
          <CadCrosshair position="bl" />
          <CadCrosshair position="br" />

          <div>
            <div className="flex items-center justify-between font-mono text-xs text-[#5c5c56] mb-4">
              <span className="text-[#e15c46] font-bold">[02] GRAPH EXPLORER</span>
              <span>TOPOLOGY & METRICS</span>
            </div>

            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-[#282828] text-white flex items-center justify-center cad-border">
                <Database className="w-5 h-5" />
              </div>
              <h3 className="font-mono font-bold text-2xl text-[#282828] uppercase">
                Helio FalkorDB Console
              </h3>
            </div>

            <p className="font-mono text-sm text-[#5c5c56] leading-relaxed mb-6">
              Visual overview of your entire engineering topology. Inspect service tiers, 
              live on-call rotation assignments, staleness indicators, and blast radius cascade depth in real time.
            </p>

            <div className="space-y-2.5 font-mono text-xs text-[#282828] mb-8 bg-[#ecece4] p-4 cad-border">
              <div className="flex items-center gap-2">
                <CheckSquare className="w-4 h-4 text-[#e15c46]" />
                <span>Interactive blast radius impact simulator across 20 services</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckSquare className="w-4 h-4 text-[#e15c46]" />
                <span>Weekly on-call rotation tracking (Diego Alvarez vs Ravi Menon)</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckSquare className="w-4 h-4 text-[#e15c46]" />
                <span>Automated 90-day staleness decay detection across documentation</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <HeronButton variant="dark" onClick={() => onSelectMode('dashboard')}>
              Launch Console Simulator
            </HeronButton>
          </div>
        </div>

      </div>

    </section>
  );
};
