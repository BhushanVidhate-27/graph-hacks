import React, { useState, useEffect } from 'react';
import { Terminal, Activity, ShieldCheck, Cpu } from 'lucide-react';

export const LiveCoordinatesHUD: React.FC = () => {
  const [coords, setCoords] = useState<{ x: number; y: number }>({ x: 1131, y: 1131 });
  const [activeStep, setActiveStep] = useState(8);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setCoords({ x: Math.round(e.clientX), y: Math.round(e.clientY) });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStep((prev) => (prev % 10) + 1);
    }, 2800);
    return () => clearInterval(interval);
  }, []);

  const systemDiagnostics = [
    "001 INITIALIZE CORE SYSTEM",
    "002 LOAD AI MODELS",
    "003 CONFIGURE DATA PIPELINES",
    "004 SYNC DISTRIBUTED NODES",
    "005 VALIDATE INPUT STREAMS",
    "006 OPTIMIZE INFERENCE ENGINE",
    "007 DEPLOY TEST ENVIRONMENT",
    "008 ENABLE REAL-TIME PROCESSING",
    "009 RUN DIAGNOSTICS",
    "010 START EXECUTION"
  ];

  return (
    <div className="w-full cad-border-b bg-[#ecece4]/90 backdrop-blur-sm text-[11px] font-mono text-[#282828] select-none py-2 px-4 md:px-8">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-y-2 gap-x-6">
        
        {/* Left: Metadata & Type */}
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-1.5 text-[#e15c46] font-bold">
            <span className="w-2 h-2 rounded-full bg-[#e15c46] animate-pulse inline-block" />
            <span>HERON // BIM-AI v2.6</span>
          </div>
          <span className="text-[#282828]/40 hidden md:inline">|</span>
          <div className="hidden lg:flex items-center gap-3 text-[#5c5c56]">
            <span>TYPE: AI/CAD Integration</span>
            <span>•</span>
            <span>FOCUS: IBC & ADA Compliance</span>
          </div>
        </div>

        {/* Center: Live Terminal Diagnostic Status */}
        <div className="hidden md:flex items-center gap-2 text-[#282828]">
          <Terminal className="w-3.5 h-3.5 text-[#e15c46]" />
          <span className="text-[#e15c46] font-bold">SYS:</span>
          <span className="tracking-tight font-medium text-[#282828]/90">
            {systemDiagnostics[activeStep - 1]}
          </span>
        </div>

        {/* Right: Live Mouse Coordinates Tracker */}
        <div className="flex items-center gap-4 ml-auto">
          <div className="flex items-center gap-3 bg-[#282828]/5 px-2.5 py-1 border border-[#282828]/15 font-bold tracking-wider">
            <span className="text-[#5c5c56]">X:</span>
            <span className="text-[#e15c46] w-12 text-right">{coords.x}</span>
            <span className="text-[#5c5c56]">PX</span>
            <span className="text-[#282828]/30">/</span>
            <span className="text-[#5c5c56]">Y:</span>
            <span className="text-[#e15c46] w-12 text-right">{coords.y}</span>
            <span className="text-[#5c5c56]">PX</span>
          </div>

          <div className="hidden sm:flex items-center gap-1.5 text-[10px] text-[#5c5c56]">
            <ShieldCheck className="w-3 h-3 text-[#e15c46]" />
            <span>IBC 2024 READY</span>
          </div>
        </div>

      </div>
    </div>
  );
};
