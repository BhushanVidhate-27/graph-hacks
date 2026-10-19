import React from 'react';
import { HeronLogo } from './HeronLogo';
import { CadCrosshair } from './CadCrosshair';
import { ExternalLink, ArrowUpRight } from 'lucide-react';
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
            <HeronLogo showText={true} />
            <p className="font-mono text-xs text-[#5c5c56] max-w-sm leading-relaxed">
              Heron AI is an autonomous BIM agent operating natively inside Revit, Rhino, ArchiCAD, and SketchUp.
              Designed for continuous building code compliance and precision model edits.
            </p>

            <div className="bg-[#ecece4] cad-border p-4 text-[11px] font-mono text-[#5c5c56] space-y-1">
              <div className="text-[#282828] font-bold">OFFICES:</div>
              <div>1801 California St. Suite 2400, Denver, CO 80202</div>
              <div>60 Martin Pl, Sydney, NSW 2000, Australia</div>
              <div className="text-[#e15c46] pt-1 font-bold">CONTACT: hello@heronaiapp.com</div>
            </div>
          </div>

          {/* Col 6-7: Product */}
          <div className="lg:col-span-2 space-y-3 font-mono text-xs">
            <div className="text-[#282828] font-bold uppercase tracking-wider mb-2">
              PRODUCT
            </div>
            <div>
              <button 
                onClick={() => onSelectMode('chat-widget')} 
                className="hover:text-[#e15c46] transition-colors"
              >
                Heron Chat Widget
              </button>
            </div>
            <div>
              <button 
                onClick={() => onSelectMode('dashboard')} 
                className="hover:text-[#e15c46] transition-colors"
              >
                Heron Dashboard
              </button>
            </div>
            <div>
              <a href="#pricing-section" className="hover:text-[#e15c46] transition-colors">
                Pricing Plans
              </a>
            </div>
            <div>
              <a href="#inspector-section" className="hover:text-[#e15c46] transition-colors">
                CAD Inspector
              </a>
            </div>
          </div>

          {/* Col 8-9: Ecosystem */}
          <div className="lg:col-span-2 space-y-3 font-mono text-xs">
            <div className="text-[#282828] font-bold uppercase tracking-wider mb-2">
              ECOSYSTEM
            </div>
            <div className="text-[#5c5c56]">Autodesk Revit</div>
            <div className="text-[#5c5c56]">McNeel Rhino</div>
            <div className="text-[#5c5c56]">Graphisoft ArchiCAD</div>
            <div className="text-[#5c5c56]">Trimble SketchUp</div>
            <div className="text-[#5c5c56]">Speckle / IFC.js</div>
          </div>

          {/* Col 10-12: Design Credits & Recognition */}
          <div className="lg:col-span-3 space-y-3 font-mono text-xs">
            <div className="text-[#282828] font-bold uppercase tracking-wider mb-2">
              RECOGNITION
            </div>
            <p className="text-[#5c5c56] text-[11px] leading-relaxed">
              Crafted as an architectural showcase inspired by the Awwwards Site of the Day by Bearplus Agency.
            </p>
            <div className="flex flex-col gap-1.5 pt-2 text-[11px] font-bold">
              <span className="text-[#e15c46] flex items-center gap-1">
                <span>AWWWARDS SITE OF THE DAY</span>
                <ArrowUpRight className="w-3 h-3" />
              </span>
              <span className="text-[#282828] flex items-center gap-1">
                <span>FWA OF THE DAY WINNER</span>
                <ArrowUpRight className="w-3 h-3" />
              </span>
            </div>
          </div>

        </div>

        {/* Bottom Bar */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 font-mono text-[11px] text-[#5c5c56]">
          <div>
            © 2026 HERON AI. ALL RIGHTS RESERVED.
          </div>
          <div className="flex items-center gap-6">
            <span className="hover:text-[#282828] cursor-pointer">PRIVACY POLICY</span>
            <span>•</span>
            <span className="hover:text-[#282828] cursor-pointer">TERMS & CONDITIONS</span>
            <span>•</span>
            <span className="hover:text-[#282828] cursor-pointer">COOKIE POLICY</span>
          </div>
        </div>

      </div>
    </footer>
  );
};
