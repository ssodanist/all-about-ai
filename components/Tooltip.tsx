import React from 'react';
import { AICompany } from '../types';
import { ExternalLink } from 'lucide-react';

interface TooltipProps {
  company: AICompany;
  position: { x: number; y: number } | null;
}

const Tooltip: React.FC<TooltipProps> = ({ company, position }) => {
  if (!position) return null;

  return (
    <div
      className="fixed z-50 pointer-events-none transform -translate-x-1/2 -translate-y-full mb-2 w-72"
      style={{ left: position.x, top: position.y - 10 }}
    >
      <div 
        className="bg-slate-900 border border-slate-700 rounded-lg shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200"
      >
        <div 
            className="h-2 w-full"
            style={{ backgroundColor: company.color }}
        />
        <div className="p-4">
          <div className="flex justify-between items-start mb-3">
             <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-white overflow-hidden flex-shrink-0">
                    <img 
                        src={company.logoUrl || `https://logo.clearbit.com/${company.domain}`} 
                        alt={company.name}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                            e.currentTarget.src = `https://www.google.com/s2/favicons?domain=${company.domain}&sz=64`
                        }}
                    />
                </div>
                <div>
                    <h3 className="font-bold font-display text-white text-lg leading-tight">
                    {company.name}
                    </h3>
                    <div className="flex items-center text-xs text-blue-400 mt-0.5">
                        <ExternalLink size={10} className="mr-1" />
                        <span>{company.domain}</span>
                    </div>
                </div>
            </div>
            <span className="text-xs font-mono bg-slate-800 px-2 py-1 rounded text-slate-300 border border-slate-700">
              {Number(company.share).toFixed(1)}%
            </span>
          </div>
          <p className="text-sm text-slate-400 leading-snug mb-3">
            {company.description}
          </p>
        </div>
      </div>
      {/* Arrow */}
      <div className="w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-t-[6px] border-t-slate-900 mx-auto -mt-px"></div>
    </div>
  );
};

export default Tooltip;