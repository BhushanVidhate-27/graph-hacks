import React from 'react';
import { HeronButton } from './HeronButton';
import { CadCrosshair } from './CadCrosshair';
import { ArrowDown, Box, Cpu, FileCheck2, Sparkles, Workflow } from 'lucide-react';
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
        <span>REPRESENTING NEXT-GEN AUTONOMOUS CAD / BIM AGENTS</span>
      </div>

      {/* Hero Grid Container */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-end cad-border-b pb-16">
        
        {/* Left 8 Cols: Massive Headline */}
        <div className="lg:col-span-8">
          <h1 className="text-4xl sm:text-6xl md:text-7xl lg:text-8xl font-mono font-bold tracking-tighter text-[#282828] uppercase leading-[0.95]">
            Works inside<br />
            your design<br />
            <span className="text-[#e15c46]">tools.</span>
          </h1>

          <div className="mt-8 max-w-2xl text-[14px] md:text-[16px] font-mono text-[#5c5c56] leading-relaxed">
            Heron sees your model, spots building code issues, and suggests fixes as you design.
            When you approve, it makes the edit itself — all without leaving the software you already use.
          </div>

          <div className="mt-8 flex flex-wrap gap-4 items-center">
            <HeronButton 
              variant="brand" 
              size="lg" 
              onClick={() => onSelectMode('chat-widget')}
            >
              Test In-Tool Plugin
            </HeronButton>

            <HeronButton 
              variant="outline" 
              size="lg" 
              onClick={() => onNavigateSection('inspector-section')}
            >
              Inspect Model Violations
            </HeronButton>

            <HeronButton 
              variant="dark" 
              size="lg" 
              onClick={() => onSelectMode('dashboard')}
            >
              Launch Dashboard
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
            <span>SPECIFICATION // v2.6</span>
            <span className="text-[#e15c46] font-bold">ONLINE</span>
          </div>

          <div className="space-y-4 font-mono text-[12px]">
            <div className="flex items-start gap-3">
              <Box className="w-4 h-4 text-[#e15c46] flex-shrink-0 mt-0.5" />
              <div>
                <div className="font-bold text-[#282828]">FASTER ITERATIONS</div>
                <div className="text-[11px] text-[#5c5c56]">Bypass repetitive drafting bottlenecks in real-time.</div>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <FileCheck2 className="w-4 h-4 text-[#e15c46] flex-shrink-0 mt-0.5" />
              <div>
                <div className="font-bold text-[#282828]">FEWER MISTAKES</div>
                <div className="text-[11px] text-[#5c5c56]">Continuous IBC 2024 and ADA geometric audits.</div>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <Workflow className="w-4 h-4 text-[#e15c46] flex-shrink-0 mt-0.5" />
              <div>
                <div className="font-bold text-[#282828]">LESS BUSYWORK</div>
                <div className="text-[11px] text-[#5c5c56]">Approve suggested changes and watch CAD auto-edit.</div>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 cad-border-t text-[10px] font-mono text-[#5c5c56] flex items-center justify-between">
            <span>NATIVE API HOOKS:</span>
            <span className="text-[#282828] font-bold">REVIT • RHINO • ARCHICAD</span>
          </div>
        </div>

      </div>

      {/* Sub-bar: Supported tools ticker */}
      <div className="pt-6 flex flex-wrap items-center justify-between gap-4 font-mono text-xs text-[#5c5c56]">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 bg-[#282828]" />
          <span className="font-bold text-[#282828]">COMPATIBLE ECOSYSTEM:</span>
          <span>Autodesk Revit 2021–2025, McNeel Rhino 7/8, Graphisoft ArchiCAD, Trimble SketchUp</span>
        </div>

        <button 
          onClick={() => onNavigateSection('inspector-section')}
          className="flex items-center gap-1.5 text-[#e15c46] hover:underline"
        >
          <span>SCROLL TO EXPLORE</span>
          <ArrowDown className="w-3.5 h-3.5" />
        </button>
      </div>

    </section>
  );
};
