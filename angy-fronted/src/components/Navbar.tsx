import React, { useState } from 'react';
import { HelioLogo } from './HelioLogo';
import { HeronButton } from './HeronButton';
import { Menu, X, ChevronDown, Network, Database, Sparkles, Terminal } from 'lucide-react';
import { CadCrosshair } from './CadCrosshair';
import { ViewMode } from '../types';

interface NavbarProps {
  currentMode: ViewMode;
  onSelectMode: (mode: ViewMode) => void;
  onNavigateSection: (sectionId: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentMode, onSelectMode, onNavigateSection }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [productDropdownOpen, setProductDropdownOpen] = useState(false);

  return (
    <nav className="relative w-full cad-border-b bg-[#ecece4]/95 backdrop-blur-md sticky top-0 z-40 select-none">
      <CadCrosshair position="tl" />
      <CadCrosshair position="tr" />

      <div className="max-w-7xl mx-auto px-4 md:px-8 h-16 md:h-20 flex items-center justify-between">
        
        {/* Left: Helio Logo */}
        <div 
          className="cursor-pointer flex items-center"
          onClick={() => {
            onSelectMode('website');
            window.scrollTo({ top: 0, behavior: 'smooth' });
          }}
        >
          <HelioLogo showText={true} />
        </div>

        {/* Center: Desktop Navigation Links */}
        <div className="hidden lg:flex items-center gap-8 text-[13px] font-mono tracking-wider">
          
          {/* Product Dropdown */}
          <div 
            className="relative group py-2"
            onMouseEnter={() => setProductDropdownOpen(true)}
            onMouseLeave={() => setProductDropdownOpen(false)}
          >
            <button className="flex items-center gap-1.5 hover:text-[#e15c46] transition-colors py-1">
              <span>EXPLORE</span>
              <ChevronDown className="w-3.5 h-3.5" />
            </button>

            {productDropdownOpen && (
              <div className="absolute top-full left-0 w-72 bg-[#f4f4ec] cad-border shadow-xl p-2 z-50 flex flex-col gap-1">
                <button
                  onClick={() => {
                    onSelectMode('chat-widget');
                    setProductDropdownOpen(false);
                  }}
                  className="w-full text-left p-3 hover:bg-[#282828] hover:text-white transition-colors group flex items-start gap-2.5"
                >
                  <Terminal className="w-4 h-4 text-[#e15c46] mt-0.5 flex-shrink-0" />
                  <div>
                    <div className="font-bold text-[12px]">HELIO CYPHER AGENT</div>
                    <div className="text-[10px] text-[#5c5c56] group-hover:text-white/70">Natural language graph traversal</div>
                  </div>
                </button>

                <button
                  onClick={() => {
                    onSelectMode('dashboard');
                    setProductDropdownOpen(false);
                  }}
                  className="w-full text-left p-3 hover:bg-[#282828] hover:text-white transition-colors group flex items-start gap-2.5 cad-border-t"
                >
                  <Database className="w-4 h-4 text-[#e15c46] mt-0.5 flex-shrink-0" />
                  <div>
                    <div className="font-bold text-[12px]">FALKORDB GRAPH CONSOLE</div>
                    <div className="text-[10px] text-[#5c5c56] group-hover:text-white/70">Topology, on-call & blast radius</div>
                  </div>
                </button>
              </div>
            )}
          </div>

          <button 
            onClick={() => onNavigateSection('inspector-section')} 
            className="hover:text-[#e15c46] transition-colors"
          >
            BLAST RADIUS INSPECTOR
          </button>

          <button 
            onClick={() => onNavigateSection('problems-section')} 
            className="hover:text-[#e15c46] transition-colors"
          >
            THE 4 TRAPS
          </button>

          <button 
            onClick={() => onNavigateSection('workflow-section')} 
            className="hover:text-[#e15c46] transition-colors"
          >
            HOW IT WORKS
          </button>

          <button 
            onClick={() => onNavigateSection('pricing-section')} 
            className="hover:text-[#e15c46] transition-colors"
          >
            PLANS
          </button>

          <button 
            onClick={() => onNavigateSection('faq-section')} 
            className="hover:text-[#e15c46] transition-colors"
          >
            FAQS
          </button>
        </div>

        {/* Right CTA / Mode Launcher */}
        <div className="hidden sm:flex items-center gap-3">
          <HeronButton 
            variant="outline" 
            size="sm" 
            onClick={() => onSelectMode('chat-widget')}
          >
            Query Agent
          </HeronButton>

          <HeronButton 
            variant="brand" 
            size="sm" 
            onClick={() => onSelectMode('dashboard')}
          >
            Graph Console
          </HeronButton>
        </div>

        {/* Mobile Menu Button */}
        <div className="lg:hidden flex items-center">
          <button 
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 cad-border text-[#282828]"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden cad-border-t bg-[#f4f4ec] px-6 py-6 flex flex-col gap-4 font-mono text-[13px]">
          <button
            onClick={() => {
              onSelectMode('website');
              onNavigateSection('inspector-section');
              setMobileMenuOpen(false);
            }}
            className="text-left py-2 hover:text-[#e15c46]"
          >
            BLAST RADIUS INSPECTOR
          </button>
          <button
            onClick={() => {
              onSelectMode('chat-widget');
              setMobileMenuOpen(false);
            }}
            className="text-left py-2 text-[#e15c46] font-bold"
          >
            HELIO CYPHER AGENT
          </button>
          <button
            onClick={() => {
              onSelectMode('dashboard');
              setMobileMenuOpen(false);
            }}
            className="text-left py-2 text-[#e15c46] font-bold"
          >
            FALKORDB GRAPH CONSOLE
          </button>
          <button
            onClick={() => {
              onNavigateSection('problems-section');
              setMobileMenuOpen(false);
            }}
            className="text-left py-2 hover:text-[#e15c46]"
          >
            THE 4 TRAPS
          </button>
          <button
            onClick={() => {
              onNavigateSection('faq-section');
              setMobileMenuOpen(false);
            }}
            className="text-left py-2 hover:text-[#e15c46]"
          >
            FAQS
          </button>
          <div className="pt-2 flex flex-col gap-2">
            <HeronButton variant="brand" onClick={() => onSelectMode('dashboard')}>
              ENTER GRAPH CONSOLE
            </HeronButton>
          </div>
        </div>
      )}
    </nav>
  );
};
