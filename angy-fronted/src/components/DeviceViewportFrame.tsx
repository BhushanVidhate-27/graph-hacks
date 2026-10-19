import React from 'react';
import { Monitor, Tablet, Smartphone, Maximize2 } from 'lucide-react';

interface DeviceViewportFrameProps {
  device: 'desktop' | 'tablet' | 'mobile';
  children: React.ReactNode;
}

export const DeviceViewportFrame: React.FC<DeviceViewportFrameProps> = ({ device, children }) => {
  const getDeviceStyles = () => {
    switch (device) {
      case 'mobile':
        return {
          container: 'max-w-[410px] my-6 rounded-[36px] p-3 bg-[#1c1c1b] shadow-2xl border-4 border-[#333]',
          screen: 'w-full h-[840px] overflow-y-auto rounded-[24px] bg-[#ecece4] relative',
          label: 'Apple iPhone 15 Pro (390 x 844 px)'
        };
      case 'tablet':
        return {
          container: 'max-w-[820px] my-6 rounded-[28px] p-4 bg-[#1c1c1b] shadow-2xl border-4 border-[#333]',
          screen: 'w-full h-[980px] overflow-y-auto rounded-[18px] bg-[#ecece4] relative',
          label: 'Apple iPad Air (820 x 1180 px)'
        };
      case 'desktop':
      default:
        return {
          container: 'w-full max-w-[1340px] my-6 rounded-[12px] p-2 bg-[#1c1c1b] shadow-2xl border-2 border-[#333]',
          screen: 'w-full h-[820px] overflow-y-auto rounded-[8px] bg-[#ecece4] relative',
          label: 'Desktop UltraWide Display (1440 x 900 px)'
        };
    }
  };

  const current = getDeviceStyles();

  return (
    <div className="w-full flex flex-col items-center justify-center p-4 min-h-[90vh]">
      
      {/* Device Info Bar */}
      <div className="bg-[#282828] text-white font-mono text-xs px-4 py-2 cad-border mb-3 flex items-center justify-between w-full max-w-4xl">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#e15c46] animate-pulse" />
          <span className="font-bold text-[#e15c46]">SIMULATED VIEWPORT:</span>
          <span className="text-white/80">{current.label}</span>
        </div>
        <div className="text-[11px] text-[#5c5c56]">SCROLL INSIDE FRAME TO TEST RESPONSIVENESS</div>
      </div>

      {/* Frame Container */}
      <div className={current.container}>
        <div className={current.screen}>
          {children}
        </div>
      </div>

    </div>
  );
};
