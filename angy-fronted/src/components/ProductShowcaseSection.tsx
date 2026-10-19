import React from 'react';
import { HeronButton } from './HeronButton';
import { CadCrosshair } from './CadCrosshair';
import { MessageSquareCode, LayoutDashboard, CheckSquare, Sparkles, Layers } from 'lucide-react';
import { ViewMode } from '../types';

interface ProductShowcaseSectionProps {
  onSelectMode: (mode: ViewMode) => void;
}

export const ProductShowcaseSection: React.FC<ProductShowcaseSectionProps> = ({ onSelectMode }) => {
  return (
    <section className="relative w-full py-16 md:py-24 px-4 md:px-8 max-w-7xl mx-auto select-none">
      
      <div className="text-[#e15c46] font-mono text-xs font-bold uppercase tracking-widest mb-2">
        PRODUCTS // THE ECOSYSTEM
      </div>
      <h2 className="text-3xl md:text-5xl font-mono font-bold tracking-tight text-[#282828] uppercase leading-tight mb-12">
        Your model. Your tools. Connected.
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Product 01: Heron Chat Widget */}
        <div className="bg-[#f4f4ec] cad-border p-8 relative flex flex-col justify-between">
          <CadCrosshair position="tl" />
          <CadCrosshair position="tr" />
          <CadCrosshair position="bl" />
          <CadCrosshair position="br" />

          <div>
            <div className="flex items-center justify-between font-mono text-xs text-[#5c5c56] mb-4">
              <span className="text-[#e15c46] font-bold">[01] IN-TOOL PLUGIN</span>
              <span>REVIT / RHINO / ARCHICAD</span>
            </div>

            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-[#e15c46] text-white flex items-center justify-center cad-border">
                <MessageSquareCode className="w-5 h-5" />
              </div>
              <h3 className="font-mono font-bold text-2xl text-[#282828] uppercase">
                Heron Chat Widget
              </h3>
            </div>

            <p className="font-mono text-sm text-[#5c5c56] leading-relaxed mb-6">
              A chat that floats over your design tool. Ask it about your model or tell it what to change,
              and it acts inside the software on your approval.
            </p>

            <div className="space-y-2.5 font-mono text-xs text-[#282828] mb-8 bg-[#ecece4] p-4 cad-border">
              <div className="flex items-center gap-2">
                <CheckSquare className="w-4 h-4 text-[#e15c46]" />
                <span>Sees your live 3D geometric context in real time</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckSquare className="w-4 h-4 text-[#e15c46]" />
                <span>Plain language instructions: "Reverse door swing in Room 2"</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckSquare className="w-4 h-4 text-[#e15c46]" />
                <span>Approval first: nothing updates without your say-so</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <HeronButton variant="brand" onClick={() => onSelectMode('chat-widget')}>
              Launch Chat Widget Simulator
            </HeronButton>
          </div>
        </div>

        {/* Product 02: Heron Dashboard */}
        <div className="bg-[#f4f4ec] cad-border p-8 relative flex flex-col justify-between">
          <CadCrosshair position="tl" />
          <CadCrosshair position="tr" />
          <CadCrosshair position="bl" />
          <CadCrosshair position="br" />

          <div>
            <div className="flex items-center justify-between font-mono text-xs text-[#5c5c56] mb-4">
              <span className="text-[#e15c46] font-bold">[02] WEB PLATFORM</span>
              <span>OVERSIGHT & AUDITING</span>
            </div>

            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-[#282828] text-white flex items-center justify-center cad-border">
                <LayoutDashboard className="w-5 h-5" />
              </div>
              <h3 className="font-mono font-bold text-2xl text-[#282828] uppercase">
                Heron Dashboard
              </h3>
            </div>

            <p className="font-mono text-sm text-[#5c5c56] leading-relaxed mb-6">
              Ask code questions about your building and get answers that reflect how the code applies to your
              layout, occupancy, and conditions, not just what requirements say in isolation.
            </p>

            <div className="space-y-2.5 font-mono text-xs text-[#282828] mb-8 bg-[#ecece4] p-4 cad-border">
              <div className="flex items-center gap-2">
                <CheckSquare className="w-4 h-4 text-[#e15c46]" />
                <span>Centralized approval queue across all firm projects</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckSquare className="w-4 h-4 text-[#e15c46]" />
                <span>Complete audit history with timestamped rationale</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckSquare className="w-4 h-4 text-[#e15c46]" />
                <span>Ingests and enforces custom firm drawing standards</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <HeronButton variant="dark" onClick={() => onSelectMode('dashboard')}>
              Launch Dashboard Simulator
            </HeronButton>
          </div>
        </div>

      </div>

    </section>
  );
};
