import React, { useState } from 'react';
import { 
  Globe, Terminal, Database, Monitor, 
  Smartphone, Tablet, Sparkles, X, ChevronUp, Layers 
} from 'lucide-react';
import { ViewMode } from '../types';

interface WebsiteViewModuleProps {
  currentMode: ViewMode;
  onSelectMode: (mode: ViewMode) => void;
  viewportDevice: 'desktop' | 'tablet' | 'mobile';
  onChangeViewportDevice: (device: 'desktop' | 'tablet' | 'mobile') => void;
}

export const WebsiteViewModule: React.FC<WebsiteViewModuleProps> = ({
  currentMode,
  onSelectMode,
  viewportDevice,
  onChangeViewportDevice
}) => {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 select-none max-w-[95vw]">
      {collapsed ? (
        <button
          onClick={() => setCollapsed(false)}
          className="flex items-center gap-2 bg-[#282828] text-white px-4 py-2 font-mono text-xs font-bold cad-border shadow-2xl hover:bg-[#e15c46] transition-colors"
        >
          <Layers className="w-4 h-4 text-[#e15c46]" />
          <span>OPEN VIEW CONTROL MODULE</span>
          <ChevronUp className="w-3.5 h-3.5 ml-1" />
        </button>
      ) : (
        <div className="bg-[#282828] text-white p-2.5 cad-border shadow-[0_8px_30px_rgb(0,0,0,0.35)] flex flex-wrap items-center gap-2 font-mono text-xs">
          
          {/* Header indicator */}
          <div className="flex items-center gap-2 px-2 text-[#e15c46] font-bold border-r border-white/20 pr-3">
            <span className="w-2 h-2 rounded-full bg-[#e15c46] animate-pulse" />
            <span className="text-[11px] hidden sm:inline">HELIO CONTROL:</span>
          </div>

          {/* Mode Switchers */}
          <div className="flex items-center gap-1">
            <button
              onClick={() => onSelectMode('website')}
              className={`flex items-center gap-1.5 px-3 py-1.5 transition-colors font-bold ${
                currentMode === 'website'
                  ? 'bg-[#e15c46] text-white'
                  : 'bg-white/10 hover:bg-white/20 text-white/80'
              }`}
            >
              <Globe className="w-3.5 h-3.5" />
              <span>Full Website</span>
            </button>

            <button
              onClick={() => onSelectMode('chat-widget')}
              className={`flex items-center gap-1.5 px-3 py-1.5 transition-colors font-bold ${
                currentMode === 'chat-widget'
                  ? 'bg-[#e15c46] text-white'
                  : 'bg-white/10 hover:bg-white/20 text-white/80'
              }`}
            >
              <Terminal className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Cypher</span>
              <span>Agent</span>
            </button>

            <button
              onClick={() => onSelectMode('dashboard')}
              className={`flex items-center gap-1.5 px-3 py-1.5 transition-colors font-bold ${
                currentMode === 'dashboard'
                  ? 'bg-[#e15c46] text-white'
                  : 'bg-white/10 hover:bg-white/20 text-white/80'
              }`}
            >
              <Database className="w-3.5 h-3.5" />
              <span>FalkorDB Console</span>
            </button>

            <button
              onClick={() => onSelectMode('viewport')}
              className={`flex items-center gap-1.5 px-3 py-1.5 transition-colors font-bold ${
                currentMode === 'viewport'
                  ? 'bg-[#e15c46] text-white'
                  : 'bg-white/10 hover:bg-white/20 text-white/80'
              }`}
            >
              <Monitor className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Device</span>
              <span>Frame</span>
            </button>
          </div>

          {/* Viewport device controls if in viewport mode */}
          {currentMode === 'viewport' && (
            <div className="flex items-center gap-1 pl-2 border-l border-white/20">
              <button
                onClick={() => onChangeViewportDevice('desktop')}
                className={`p-1.5 ${viewportDevice === 'desktop' ? 'bg-[#e15c46] text-white' : 'bg-white/10 text-white/70'}`}
                title="Desktop 1440px"
              >
                <Monitor className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => onChangeViewportDevice('tablet')}
                className={`p-1.5 ${viewportDevice === 'tablet' ? 'bg-[#e15c46] text-white' : 'bg-white/10 text-white/70'}`}
                title="Tablet 768px"
              >
                <Tablet className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => onChangeViewportDevice('mobile')}
                className={`p-1.5 ${viewportDevice === 'mobile' ? 'bg-[#e15c46] text-white' : 'bg-white/10 text-white/70'}`}
                title="Mobile 390px"
              >
                <Smartphone className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* Close / Collapse button */}
          <button
            onClick={() => setCollapsed(true)}
            className="p-1 hover:bg-white/20 text-white/60 hover:text-white transition-colors ml-1"
            title="Minimize Bar"
          >
            <X className="w-4 h-4" />
          </button>

        </div>
      )}
    </div>
  );
};
