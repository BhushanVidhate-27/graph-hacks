import React from 'react';

interface HelioLogoProps {
  className?: string;
  showText?: boolean;
}

export const HelioLogo: React.FC<HelioLogoProps> = ({ className = '', showText = true }) => {
  return (
    <div className={`flex items-center gap-3 select-none ${className}`}>
      {/* Helio Graph Nexus / Node Geometric Mark */}
      <div className="relative w-7 h-8 flex-shrink-0 flex items-center justify-center">
        <svg width="28" height="32" viewBox="0 0 34 39" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path
            d="M17 2L32 10.5V28.5L17 37L2 28.5V10.5L17 2Z"
            stroke="#282828"
            strokeWidth="2"
            fill="none"
          />
          <path
            d="M17 2V19.5M32 28.5L17 19.5M2 28.5L17 19.5"
            stroke="#282828"
            strokeWidth="1.5"
          />
          {/* Inner core pulse node */}
          <circle cx="17" cy="19.5" r="3.5" fill="#e15c46" />
          <circle cx="17" cy="2" r="2" fill="#282828" />
          <circle cx="32" cy="10.5" r="2" fill="#282828" />
          <circle cx="32" cy="28.5" r="2" fill="#282828" />
          <circle cx="17" cy="37" r="2" fill="#282828" />
          <circle cx="2" cy="28.5" r="2" fill="#282828" />
          <circle cx="2" cy="10.5" r="2" fill="#282828" />
        </svg>
      </div>

      {/* Helio Logotype */}
      {showText && (
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5 font-mono font-bold tracking-tight text-xl leading-none text-[#282828]">
            <span>HELIO</span>
            <span className="w-1.5 h-1.5 bg-[#e15c46] rounded-full inline-block" />
          </div>
          <span className="font-mono text-[9px] text-[#5c5c56] tracking-widest uppercase font-semibold mt-0.5">
            A Company Brain // Graph
          </span>
        </div>
      )}
    </div>
  );
};
