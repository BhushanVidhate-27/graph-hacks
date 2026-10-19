import React, { useState, useRef } from 'react';
import { CadCrosshair } from './CadCrosshair';
import { HeronButton } from './HeronButton';
import { AlertTriangle, CheckCircle2, ChevronRight, Sparkles, Scan, ZoomIn, Eye } from 'lucide-react';
import { Violation } from '../types';

export const ViolationInspector: React.FC = () => {
  const [sliderPos, setSliderPos] = useState(52); // percentage
  const [isDragging, setIsDragging] = useState(false);
  const [activeViolation, setActiveViolation] = useState<string>('v1');
  const [violations, setViolations] = useState<Violation[]>([
    {
      id: 'v1',
      code: 'IBC 1015.3',
      title: 'Guardrail Required for Fall Protection',
      description: 'Openings located more than 30 inches above the floor or grade below require protective guards not less than 42 inches in height.',
      category: 'safety',
      x: 32,
      y: 38,
      status: 'flagged',
      elementId: 'GUARD-301-B',
      recommendation: 'Insert 42" glass panel guardrail along atrium balcony edge.'
    },
    {
      id: 'v2',
      code: 'IBC 1011.11',
      title: 'Continuous Handrails Required',
      description: 'Stairways shall have handrails on each side that return to a wall, guard or walking surface continuously.',
      category: 'egress',
      x: 68,
      y: 62,
      status: 'flagged',
      elementId: 'STAIR-E2-NORTH',
      recommendation: 'Extend wall-mounted handrail 12" past top and bottom risers.'
    },
    {
      id: 'v3',
      code: 'IBC 1017.2',
      title: 'Exit Access Travel Distance Exceeded',
      description: 'Assembly occupancies without automatic sprinklers are limited to 75 ft travel distance. Measured path is currently 94.2 ft.',
      category: 'egress',
      x: 48,
      y: 24,
      status: 'flagged',
      elementId: 'ROOM-104-CONF',
      recommendation: 'Reconfigure secondary exit corridor door or designate as NFPA 13 sprinklered zone.'
    },
    {
      id: 'v4',
      code: 'ICC A117.1 §604.3.1',
      title: 'Accessible Restroom 60" Turning Clearance',
      description: 'Accessible restrooms require an unobstructed 60-inch circular turning space. Vanity fixture encroaches by 8.5 inches.',
      category: 'accessibility',
      x: 82,
      y: 42,
      status: 'flagged',
      elementId: 'RESTROOM-ADA-01',
      recommendation: 'Shift lavatory cabinet 10" northeast to clear turning radius.'
    }
  ]);

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

  const handleFixViolation = (id: string) => {
    setViolations((prev) =>
      prev.map((v) => (v.id === id ? { ...v, status: 'remediated' } : v))
    );
  };

  const currentV = violations.find((v) => v.id === activeViolation) || violations[0];

  return (
    <section id="inspector-section" className="relative w-full py-16 md:py-24 px-4 md:px-8 max-w-7xl mx-auto select-none">
      
      {/* Header bar */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8 cad-border-b pb-6">
        <div>
          <div className="flex items-center gap-2 text-[#e15c46] font-mono text-xs font-bold uppercase tracking-widest mb-2">
            <Scan className="w-4 h-4" />
            <span>001 // Live Interactive CAD Inspection</span>
          </div>
          <h2 className="text-3xl md:text-5xl font-mono font-bold tracking-tight text-[#282828] uppercase">
            Click & drag your mouse<br />to reveal violations
          </h2>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono text-[#5c5c56]">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-[#e15c46] inline-block border border-[#282828]" />
            <span>BEFORE (MANUAL FLAGGED)</span>
          </div>
          <span>•</span>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-[#282828] inline-block border border-[#282828]" />
            <span>AFTER (HERON EDITED)</span>
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

            {/* Background 1: After / Remediated model */}
            <div className="absolute inset-0 w-full h-full">
              <img
                src="/images/after_model.jpg"
                alt="After Heron AI remediation"
                className="w-full h-full object-cover brightness-95"
                onError={(e) => {
                  // Fallback high-tech placeholder if image fails
                  (e.target as HTMLElement).style.display = 'none';
                }}
              />
              {/* After Grid Label */}
              <div className="absolute top-4 right-4 bg-[#282828]/80 text-white font-mono text-[10px] px-2.5 py-1 cad-border uppercase tracking-widest backdrop-blur-sm">
                HERON COMPLIANT MODEL // REV 02
              </div>
            </div>

            {/* Background 2: Before / Violations Model (Clipped by slider) */}
            <div
              className="absolute inset-0 w-full h-full overflow-hidden"
              style={{ clipPath: `inset(0 ${100 - sliderPos}% 0 0)` }}
            >
              <img
                src="/images/heron_model.jpg"
                alt="Before Heron AI inspection"
                className="w-full h-full object-cover brightness-90 contrast-110"
                onError={(e) => {
                  (e.target as HTMLElement).style.display = 'none';
                }}
              />

              {/* Before Grid Label */}
              <div className="absolute top-4 left-4 bg-[#e15c46] text-white font-mono text-[10px] px-2.5 py-1 cad-border uppercase tracking-widest shadow-lg">
                MANUAL UNCHECKED CAD // REV 01
              </div>

              {/* Interactive Violation Badges inside the unclipped area */}
              {violations.map((v) => (
                <button
                  key={v.id}
                  onClick={(e) => {
                    e.stopPropagation();
                    setActiveViolation(v.id);
                  }}
                  style={{ top: `${v.y}%`, left: `${v.x}%` }}
                  className={`absolute -translate-x-1/2 -translate-y-1/2 z-20 group transition-all duration-300 ${
                    activeViolation === v.id ? 'scale-125 z-30' : 'hover:scale-110'
                  }`}
                >
                  <div className={`relative px-2 py-1 font-mono text-[10px] font-bold uppercase tracking-tighter flex items-center gap-1.5 shadow-2xl cad-border ${
                    v.status === 'remediated' 
                      ? 'bg-emerald-600 text-white border-emerald-400' 
                      : 'bg-[#e15c46] text-white border-black'
                  }`}>
                    <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping" />
                    <span>{v.code}</span>
                  </div>

                  {/* Connecting CAD line */}
                  <div className="w-[1px] h-6 bg-[#e15c46] mx-auto opacity-75" />
                </button>
              ))}
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
            <div className="absolute bottom-3 left-1/2 -translate-x-1/2 bg-[#282828]/85 text-white text-[11px] font-mono px-4 py-1 rounded-full pointer-events-none backdrop-blur-sm z-30">
              ◄ DRAG TO COMPARE BEFORE & AFTER ►
            </div>
          </div>
        </div>

        {/* Right 4 Cols: Active Violation Detail Panel */}
        <div className="lg:col-span-4 bg-[#f4f4ec] cad-border p-6 relative">
          <CadCrosshair position="tl" />
          <CadCrosshair position="tr" />
          <CadCrosshair position="bl" />
          <CadCrosshair position="br" />

          <div className="flex items-center justify-between pb-4 cad-border-b mb-5">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 bg-[#e15c46]" />
              <span className="font-mono text-xs font-bold text-[#e15c46] uppercase">Active Violation Callout</span>
            </div>
            <span className="font-mono text-[11px] text-[#5c5c56]">ID: {currentV.elementId}</span>
          </div>

          {/* Violation Code & Title */}
          <div className="mb-4">
            <div className="inline-block bg-[#e15c46]/10 text-[#e15c46] font-mono text-xs font-bold px-2 py-0.5 cad-border mb-2">
              {currentV.code}
            </div>
            <h3 className="font-mono font-bold text-lg text-[#282828] uppercase leading-snug">
              {currentV.title}
            </h3>
          </div>

          {/* Description */}
          <p className="text-[12px] font-mono text-[#5c5c56] leading-relaxed mb-6">
            {currentV.description}
          </p>

          {/* Heron AI Proposed Action */}
          <div className="bg-[#ecece4] cad-border p-4 mb-6">
            <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-[#282828] mb-1.5">
              <Sparkles className="w-3.5 h-3.5 text-[#e15c46]" />
              <span>HERON SUGGESTED EDIT:</span>
            </div>
            <p className="text-[11px] font-mono text-[#282828] leading-normal">
              {currentV.recommendation}
            </p>
          </div>

          {/* Action Button */}
          <div className="flex flex-col gap-3">
            {currentV.status === 'remediated' ? (
              <div className="flex items-center justify-center gap-2 py-3 bg-emerald-100 text-emerald-800 font-mono text-xs font-bold cad-border">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>VIOLATION REMEDIATED IN MODEL</span>
              </div>
            ) : (
              <HeronButton
                variant="brand"
                size="md"
                onClick={() => handleFixViolation(currentV.id)}
                className="w-full justify-center"
              >
                Apply Edit Automatically
              </HeronButton>
            )}

            {/* Quick Violation Navigator */}
            <div className="grid grid-cols-4 gap-1 mt-2">
              {violations.map((v, i) => (
                <button
                  key={v.id}
                  onClick={() => setActiveViolation(v.id)}
                  className={`py-1.5 font-mono text-[10px] font-bold cad-border transition-colors ${
                    activeViolation === v.id
                      ? 'bg-[#282828] text-white'
                      : v.status === 'remediated'
                      ? 'bg-emerald-50 text-emerald-700'
                      : 'bg-white text-[#282828] hover:bg-[#e15c46] hover:text-white'
                  }`}
                >
                  0{i + 1}
                </button>
              ))}
            </div>
          </div>

        </div>

      </div>

    </section>
  );
};
