import React from 'react';
import { HeronButton } from './HeronButton';
import { CadCrosshair } from './CadCrosshair';
import { ArrowDown, Network, ShieldCheck, GitBranch, Cpu, AlertOctagon } from 'lucide-react';
import { ViewMode } from '../types';

interface HeroSectionProps {
  onSelectMode: (mode: ViewMode) => void;
  onNavigateSection: (sectionId: string) => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ onSelectMode, onNavigateSection }) => {
  return (
    <section className="relative w-full pt-12 md:pt-20 pb-16 px-4 md:px-8 max-w-7xl mx-auto select-none">
      
      {/* Top Banner Tag */}
      <div className="flex items-center gap-3 font-mono text-[11px] text-[#e15c46] font-bold uppercase tracking-wider mb-6">
        <span className="w-2.5 h-2.5 bg-[#e15c46]" />
        <span>TRACK 03 // GRAPH HACKS · COMPANY BRAIN PLATFORM</span>
      </div>

      {/* Hero Grid Container */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-end cad-border-b pb-16">
        
        {/* Left 8 Cols: Massive Headline */}
        <div className="lg:col-span-8">
          <h1 className="text-4xl sm:text-6xl md:text-7xl lg:text-8xl font-mono font-bold tracking-tighter text-[#282828] uppercase leading-[0.95]">
            Know what breaks.<br />
            Before it dies.<br />
            <span className="text-[#e15c46]">In one traversal.</span>
          </h1>

          <div className="mt-8 max-w-2xl text-[14px] md:text-[16px] font-mono text-[#5c5c56] leading-relaxed">
            Existing enterprise search answers <span className="text-[#282828] font-bold">"where is the doc about X."</span> Helio
            answers <span className="text-[#282828] font-bold">who knows about X, what breaks if it goes down, where was that decided, and how current is that answer</span> —
            in one deterministic Cypher traversal, with the complete path shown. Text search is used only at the leaves.
          </div>

          <div className="mt-8 flex flex-wrap gap-4 items-center">
            <HeronButton 
              variant="brand" 
              size="lg" 
              onClick={() => onSelectMode('chat-widget')}
            >
              Ask Helio Agent
            </HeronButton>

            <HeronButton 
              variant="outline" 
              size="lg" 
              onClick={() => onNavigateSection('inspector-section')}
            >
              Inspect Blast Radius
            </HeronButton>

            <HeronButton 
              variant="dark" 
              size="lg" 
              onClick={() => onSelectMode('dashboard')}
            >
              FalkorDB Console
            </HeronButton>
          </div>
        </div>

        {/* Right 4 Cols: Technical Metadata HUD Card */}
        <div className="lg:col-span-4 bg-[#f4f4ec] cad-border p-6 relative">
          <CadCrosshair position="tl" />
          <CadCrosshair position="tr" />
          <CadCrosshair position="bl" />
          <CadCrosshair position="br" />

          <div className="font-mono text-[11px] text-[#5c5c56] uppercase tracking-wider mb-4 cad-border-b pb-3 flex justify-between items-center">
            <span>GROUND TRUTH BENCHMARK</span>
            <span className="text-[#e15c46] font-bold">20/20 PASSED</span>
          </div>

          <div className="space-y-4 font-mono text-[12px]">
            <div className="flex items-start gap-3">
              <Network className="w-4 h-4 text-[#e15c46] flex-shrink-0 mt-0.5" />
              <div>
                <div className="font-bold text-[#282828]">BLAST RADIUS TRAVERSAL</div>
                <div className="text-[11px] text-[#5c5c56]">Walks HAS_DEPENDENT with hop depth, owning team & on-call engineer.</div>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <GitBranch className="w-4 h-4 text-[#e15c46] flex-shrink-0 mt-0.5" />
              <div>
                <div className="font-bold text-[#282828]">EXPERTISE VOLUME VS RECENCY</div>
                <div className="text-[11px] text-[#5c5c56]">Reports both signals separately — never returns departed employees like Priya.</div>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <ShieldCheck className="w-4 h-4 text-[#e15c46] flex-shrink-0 mt-0.5" />
              <div>
                <div className="font-bold text-[#282828]">SUPERSEDES PROVENANCE</div>
                <div className="text-[11px] text-[#5c5c56]">D-19 shows as overriding old March docs: Adyen primary, Stripe fallback.</div>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <AlertOctagon className="w-4 h-4 text-[#e15c46] flex-shrink-0 mt-0.5" />
              <div>
                <div className="font-bold text-[#282828]">HONEST NEGATIVES</div>
                <div className="text-[11px] text-[#5c5c56]">5 questions have no answer in the graph. Helio states it plainly instead of hallucinating.</div>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 cad-border-t text-[10px] font-mono text-[#5c5c56] flex items-center justify-between">
            <span>GRAPH INFRASTRUCTURE:</span>
            <span className="text-[#282828] font-bold">FALKORDB + CYPHER</span>
          </div>
        </div>

      </div>

      {/* Sub-bar: Supported tools ticker */}
      <div className="pt-6 flex flex-wrap items-center justify-between gap-4 font-mono text-xs text-[#5c5c56]">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 bg-[#282828]" />
          <span className="font-bold text-[#282828]">ORGANIZATIONAL TOPOLOGY:</span>
          <span>Helio Fintech · 120 Persons · 5 Teams · 20 Services · 40 Decisions · 2,000 Messages</span>
        </div>

        <button 
          onClick={() => onNavigateSection('inspector-section')}
          className="flex items-center gap-1.5 text-[#e15c46] hover:underline"
        >
          <span>INTERACTIVE BLAST RADIUS</span>
          <ArrowDown className="w-3.5 h-3.5" />
        </button>
      </div>

    </section>
  );
};
