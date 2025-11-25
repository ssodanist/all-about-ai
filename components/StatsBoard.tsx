import React from 'react';
import { AICompany } from '../types';
import { TrendingUp, Globe, Search } from 'lucide-react';

interface StatsBoardProps {
  companies: AICompany[];
  highlightedId: string | null;
  onHover: (id: string | null) => void;
}

const StatsBoard: React.FC<StatsBoardProps> = ({ companies, highlightedId, onHover }) => {
  return (
    <div className="bg-slate-800/50 backdrop-blur-md border border-slate-700 rounded-xl p-6 h-full flex flex-col">
      <div className="flex items-center gap-2 mb-4 text-emerald-400">
        <TrendingUp size={20} />
        <h2 className="text-xl font-bold font-display tracking-wide text-white">Live Mindshare</h2>
      </div>

      <div className="flex-1 overflow-y-auto pr-2 space-y-2 custom-scrollbar">
        {companies.map((company) => (
          <a
            key={company.id}
            href={company.url}
            target="_blank"
            rel="noopener noreferrer"
            className={`
              block p-2 rounded-lg border transition-all duration-200 group
              ${highlightedId === company.id 
                ? 'bg-slate-700 border-slate-500 translate-x-1' 
                : 'bg-slate-900/40 border-slate-800 hover:bg-slate-800 hover:border-slate-600'}
            `}
            onMouseEnter={() => onHover(company.id)}
            onMouseLeave={() => onHover(null)}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3 overflow-hidden">
                <div 
                  className="w-5 h-5 rounded shadow-sm overflow-hidden bg-white flex-shrink-0 flex items-center justify-center" 
                  style={{ backgroundColor: company.color }}
                >
                    <img 
                        src={company.logoUrl || `https://logo.clearbit.com/${company.domain}`}
                        alt={company.name}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                            e.currentTarget.src = `https://www.google.com/s2/favicons?domain=${company.domain}&sz=64`
                        }}
                    />
                </div>
                <span className="font-semibold text-sm text-slate-100 group-hover:text-white truncate">
                  {company.name}
                </span>
              </div>
              <span className="text-xs font-mono text-slate-400 flex-shrink-0 ml-2">
                {Number(company.share).toFixed(1)}%
              </span>
            </div>
          </a>
        ))}
      </div>
      
      <div className="mt-4 pt-3 border-t border-slate-700 text-[10px] text-slate-500 flex flex-col gap-1.5 uppercase tracking-wider font-semibold">
        <div className="flex items-center gap-2">
            <Globe size={12} />
            <span>Data sourced via Gemini Google Search</span>
        </div>
        <div className="flex items-center gap-2">
            <Search size={12} />
            <span>Reflects real-time query volume</span>
        </div>
      </div>
    </div>
  );
};

export default StatsBoard;