import React from 'react';

interface CadCrosshairProps {
  position: 'tl' | 'tr' | 'bl' | 'br';
  className?: string;
}

export const CadCrosshair: React.FC<CadCrosshairProps> = ({ position, className = '' }) => {
  const getPosClass = () => {
    switch (position) {
      case 'tl': return 'cad-crosshair-tl';
      case 'tr': return 'cad-crosshair-tr';
      case 'bl': return 'cad-crosshair-bl';
      case 'br': return 'cad-crosshair-br';
    }
  };

  return (
    <div className={`${getPosClass()} ${className} flex items-center justify-center text-[#282828] select-none z-10`}>
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M5.995 0V12" stroke="currentColor" strokeWidth="1" />
        <path d="M0 5.995H12" stroke="currentColor" strokeWidth="1" />
      </svg>
    </div>
  );
};
