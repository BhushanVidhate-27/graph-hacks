import React from 'react';
import { HelioLogo } from './HelioLogo';
import { CadCrosshair } from './CadCrosshair';
import { ExternalLink, ArrowUpRight, GitBranch, Mail } from 'lucide-react';
import { ViewMode } from '../types';

interface FooterProps {
  onSelectMode: (mode: ViewMode) => void;
}

export const Footer: React.FC<FooterProps> = ({ onSelectMode }) => {
  return (
    <footer className="relative w-full cad-border-t bg-[#f4f4ec] select-none pt-16 pb-12 px-4 md:px-8">
      <div className="max-w-7xl mx-auto">
        
        {/* Top Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-12 pb-16 cad-border-b">
          
          {/* Col 1-5: Brand & Mission */}
          <div className="lg:col-span-5 space-y-6">
            <HelioLogo showText={true} />
            <p className="font-mono text-xs text-[#5c5c56] max-w-sm leading-relaxed">
              Helio is an organizational knowledge graph engine built on FalkorDB.
              Answering who knows what, what breaks if it dies, and where decisions were made —
              with complete Cypher provenance and zero hallucination.
            </p>

            <div className="bg-[#ecece4] cad-border p-4 text-[11px] font-mono text-[#5c5c56] space-y-2">
              <div className="text-[#282828] font-bold">CONTACT & INQUIRIES:</div>
              <a 
                href="mailto:bhushanvidhate002@gmail.com" 
                className="text-[#e15c46] font-bold text-xs hover:underline flex items-center gap-1.5"
              >
                <Mail className="w-3.5 h-3.5" />
                <span>bhushanvidhate002@gmail.com</span>
              </a>
              <div className="text-[10px] text-[#5c5c56] pt-1">
                Track 03: Company Brain · Graph Hacks · Ground Truth Verified
              </div>
            </div>
          </div>

          {/* Col 6-7: Product */}
          <div className="lg:col-span-2 space-y-3 font-mono text-xs">
            <div className="text-[#282828] font-bold uppercase tracking-wider mb-2">
              INTERFACES
            </div>
            <div>
              <button 
                onClick={() => onSelectMode('chat-widget')} 
                className="hover:text-[#e15c46] transition-colors"
              >
                Cypher Agent
              </button>
            </div>
            <div>
              <button 
                onClick={() => onSelectMode('dashboard')} 
                className="hover:text-[#e15c46] transition-colors"
              >
                FalkorDB Console
              </button>
            </div>
            <div>
              <a href="#inspector-section" className="hover:text-[#e15c46] transition-colors">
                Blast Radius Map
              </a>
            </div>
            <div>
              <a href="#problems-section" className="hover:text-[#e15c46] transition-colors">
                The 4 Failure Traps
              </a>
            </div>
          </div>

          {/* Col 8-9: Schema & Graph */}
          <div className="lg:col-span-2 space-y-3 font-mono text-xs">
            <div className="text-[#282828] font-bold uppercase tracking-wider mb-2">
              GRAPH SCHEMA
            </div>
            <div className="text-[#5c5c56]">HAS_DEPENDENT</div>
            <div className="text-[#5c5c56]">SUPERSEDES</div>
            <div className="text-[#5c5c56]">OWNED_BY</div>
            <div className="text-[#5c5c56]">ON_CALL</div>
            <div className="text-[#5c5c56]">CONTRIBUTED_TO</div>
          </div>

          {/* Col 10-12: Hackathon & Recognition */}
          <div className="lg:col-span-3 space-y-3 font-mono text-xs">
            <div className="text-[#282828] font-bold uppercase tracking-wider mb-2">
              TRACK 03: GRAPH HACKS
            </div>
            <p className="text-[#5c5c56] text-[11px] leading-relaxed">
              Company Brain Track · Built for Graph Hacks with ground truth-first architecture.
            </p>
            <div className="flex flex-col gap-1.5 pt-2 text-[11px] font-bold">
              <a 
                href="https://github.com/BhushanVidhate-27/graph-hacks-company-brain" 
                target="_blank" 
                rel="noreferrer"
                className="text-[#282828] hover:text-[#e15c46] flex items-center gap-1.5 transition-colors"
              >
                <GitBranch className="w-3.5 h-3.5" />
                <span>GITHUB REPOSITORY</span>
                <ArrowUpRight className="w-3 h-3" />
              </a>
              <span className="text-[#e15c46] flex items-center gap-1">
                <span>FALKORDB CERTIFIED PASS</span>
              </span>
            </div>
          </div>

        </div>

        {/* Bottom Bar */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 font-mono text-[11px] text-[#5c5c56]">
          <div>
            © 2026 HELIO — A COMPANY BRAIN. ALL RIGHTS RESERVED.
          </div>
          <div className="flex items-center gap-6">
            <a href="mailto:bhushanvidhate002@gmail.com" className="hover:text-[#282828] transition-colors">
              bhushanvidhate002@gmail.com
            </a>
            <span>•</span>
            <span>GROUND_TRUTH.MD</span>
            <span>•</span>
            <span>SCHEMA.MD</span>
          </div>
        </div>

      </div>
    </footer>
  );
};
