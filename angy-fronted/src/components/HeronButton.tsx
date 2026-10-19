import React from 'react';
import { ArrowRight } from 'lucide-react';

interface HeronButtonProps {
  children: React.ReactNode;
  variant?: 'outline' | 'brand' | 'dark' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  icon?: boolean;
  onClick?: () => void;
  className?: string;
  type?: 'button' | 'submit' | 'reset';
}

export const HeronButton: React.FC<HeronButtonProps> = ({
  children,
  variant = 'outline',
  size = 'md',
  icon = true,
  onClick,
  className = '',
  type = 'button',
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'brand':
        return 'bg-[#e15c46] text-white border-[#e15c46] hover:bg-[#282828] hover:border-[#282828]';
      case 'dark':
        return 'bg-[#282828] text-white border-[#282828] hover:bg-[#e15c46] hover:border-[#e15c46]';
      case 'ghost':
        return 'bg-transparent text-[#282828] border-transparent hover:bg-[#282828]/10';
      case 'outline':
      default:
        return 'bg-transparent text-[#282828] border-[#282828] hover:bg-[#282828] hover:text-white';
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case 'sm':
        return 'text-[11px] py-1.5 px-3 gap-2';
      case 'lg':
        return 'text-[15px] py-3.5 px-6 gap-3';
      case 'md':
      default:
        return 'text-[13px] py-2.5 px-4 gap-2.5';
    }
  };

  return (
    <button
      type={type}
      onClick={onClick}
      className={`group relative inline-flex items-center justify-between border font-mono font-bold uppercase tracking-wider transition-colors duration-300 select-none overflow-hidden ${getVariantStyles()} ${getSizeStyles()} ${className}`}
    >
      {/* Sliding Text Container */}
      <div className="relative overflow-hidden h-[1.3em] flex flex-col justify-center">
        <span className="block transform transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:-translate-y-full">
          {children}
        </span>
        <span className="absolute top-0 left-0 block transform translate-y-full transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:translate-y-0 text-current">
          {children}
        </span>
      </div>

      {/* Sliding Arrow Icon */}
      {icon && (
        <div className="relative overflow-hidden w-4 h-4 flex items-center justify-center flex-shrink-0">
          <ArrowRight className="w-3.5 h-3.5 transform transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:translate-x-4" />
          <ArrowRight className="w-3.5 h-3.5 absolute transform -translate-x-4 transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:translate-x-0" />
        </div>
      )}
    </button>
  );
};
