import React, { memo } from 'react';
import { AICompany } from '../types';

interface BlockProps {
  company: AICompany;
  isHovered: boolean;
  onMouseEnter: (id: string) => void;
  onMouseLeave: () => void;
  onClick: (url?: string) => void;
}

const Block: React.FC<BlockProps> = ({ company, isHovered, onMouseEnter, onMouseLeave, onClick }) => {
  const logoUrl = company.logoUrl || `https://logo.clearbit.com/${company.domain}`;

  return (
    <div
      className={`
        w-full h-full cursor-pointer transition-all duration-100
        ${isHovered ? 'z-20 scale-150 shadow-2xl rounded-sm border-2 border-white relative' : 'hover:opacity-100'}
      `}
      style={{ 
        backgroundColor: company.color,
      }}
      onMouseEnter={() => onMouseEnter(company.id)}
      onMouseLeave={onMouseLeave}
      onClick={() => onClick(company.url)}
      title={`${company.name} (${Number(company.share).toFixed(2)}%)`}
      role="button"
      aria-label={`View details for ${company.name}`}
    >
      <div 
        className="w-full h-full bg-center bg-no-repeat bg-cover opacity-90 hover:opacity-100"
        style={{ 
          backgroundImage: `url(${logoUrl})`,
        }} 
      >
        <img 
            src={logoUrl} 
            onError={(e) => {
                // If logo fails, we just keep the background color
                e.currentTarget.style.display = 'none';
            }}
            className="hidden" // Hidden image just to trigger preloading
            alt=""
        />
      </div>
    </div>
  );
};

export default memo(Block);