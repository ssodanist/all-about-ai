import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { DEFAULT_COMPANIES, GRID_COLUMNS, GRID_ROWS, TOTAL_BLOCKS } from './constants';
import { AICompany } from './types';
import { fetchLiveTrends } from './services/geminiService';
import Block from './components/Block';
import StatsBoard from './components/StatsBoard';
import Tooltip from './components/Tooltip';
import { RefreshCcw, Cpu, Share2 } from 'lucide-react';

const App: React.FC = () => {
  const [companies, setCompanies] = useState<AICompany[]>(DEFAULT_COMPANIES);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  
  // Interaction State
  const [hoveredCompanyId, setHoveredCompanyId] = useState<string | null>(null);
  const [mousePos, setMousePos] = useState<{ x: number; y: number } | null>(null);

  // Generate grid mapping based on company shares
  const gridMapping = useMemo(() => {
    const map: string[] = [];
    let currentBlock = 0;

    // Sort companies by share size (largest first looks better in linear fill)
    const sortedCompanies = [...companies].sort((a, b) => b.share - a.share);

    sortedCompanies.forEach(company => {
      // Calculate how many blocks this company gets
      // We floor it initially, then might have remainder
      const blockCount = Math.floor((company.share / 100) * TOTAL_BLOCKS);
      
      for (let i = 0; i < blockCount; i++) {
        map.push(company.id);
      }
    });

    // Fill remaining blocks due to rounding with the top company or "Unknown"
    while (map.length < TOTAL_BLOCKS) {
      map.push(sortedCompanies[0]?.id || 'unknown');
    }
    
    // If we exceeded (rare due to math), trim
    return map.slice(0, TOTAL_BLOCKS);
  }, [companies]);

  const handleFetchTrends = async () => {
    setLoading(true);
    setError(null);
    try {
      const newTrends = await fetchLiveTrends();
      setCompanies(newTrends);
      setLastUpdated(new Date());
    } catch (err) {
      setError("Failed to fetch live trends. Using cached data.");
      // Optionally keep old data
    } finally {
      setLoading(false);
    }
  };

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    setMousePos({ x: e.clientX, y: e.clientY });
  }, []);

  const handleCompanyClick = useCallback((url?: string) => {
    if (url) window.open(url, '_blank');
  }, []);

  const hoveredCompany = useMemo(() => 
    companies.find(c => c.id === hoveredCompanyId),
  [companies, hoveredCompanyId]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 flex flex-col" onMouseMove={handleMouseMove}>
      
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Cpu className="text-white" size={24} />
            </div>
            <div>
                <h1 className="font-display font-bold text-xl text-white tracking-tight">AI Mindshare Grid</h1>
                <p className="text-xs text-slate-400">The "Million Dollar Homepage" of Artificial Intelligence</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
             <div className="hidden md:block text-right">
                <p className="text-xs text-slate-500 uppercase tracking-wider font-bold">Last Updated</p>
                <p className="text-xs text-emerald-400 font-mono">{lastUpdated.toLocaleTimeString()}</p>
             </div>
            <button
              onClick={handleFetchTrends}
              disabled={loading}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-all
                ${loading 
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed' 
                  : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/25 active:scale-95'}
              `}
            >
              <RefreshCcw size={16} className={loading ? 'animate-spin' : ''} />
              {loading ? 'Analyzing Web...' : 'Refresh Trends'}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 py-8 grid lg:grid-cols-12 gap-8">
        
        {/* Left: The Grid */}
        <div className="lg:col-span-8 flex flex-col gap-4">
            <div className="bg-slate-900 border border-slate-800 p-1 rounded-xl shadow-2xl relative overflow-hidden group">
                
                {/* Loading Overlay */}
                {loading && (
                    <div className="absolute inset-0 bg-slate-900/80 backdrop-blur-sm z-30 flex items-center justify-center flex-col">
                        <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4"></div>
                        <p className="text-indigo-400 font-mono animate-pulse">Scanning Global Search Data...</p>
                    </div>
                )}

                {/* The actual grid container */}
                <div 
                    className="grid w-full aspect-[16/10] bg-black"
                    style={{
                        gridTemplateColumns: `repeat(${GRID_COLUMNS}, 1fr)`,
                        gridTemplateRows: `repeat(${GRID_ROWS}, 1fr)`,
                    }}
                >
                    {gridMapping.map((companyId, index) => {
                        const company = companies.find(c => c.id === companyId);
                        if (!company) return <div key={index} className="bg-slate-900" />;

                        return (
                            <Block
                                key={`${index}-${company.id}`}
                                company={company}
                                isHovered={hoveredCompanyId === company.id}
                                onMouseEnter={setHoveredCompanyId}
                                onMouseLeave={() => setHoveredCompanyId(null)}
                                onClick={handleCompanyClick}
                            />
                        );
                    })}
                </div>
            </div>
            
            <div className="flex justify-between items-center text-sm text-slate-500 px-2">
                <p>1 Block = 0.1% Global Interest</p>
                <p>Total: 1,000 Blocks</p>
            </div>
            {error && (
                <div className="p-4 bg-red-900/20 border border-red-900/50 text-red-400 rounded-lg text-sm">
                    {error}
                </div>
            )}
        </div>

        {/* Right: Stats & List */}
        <div className="lg:col-span-4 h-[600px] lg:h-auto lg:max-h-[800px] sticky top-24">
            <StatsBoard 
                companies={companies} 
                highlightedId={hoveredCompanyId}
                onHover={setHoveredCompanyId}
            />
        </div>

      </main>

      <Tooltip company={hoveredCompany || DEFAULT_COMPANIES[0]} position={hoveredCompany ? mousePos : null} />
    </div>
  );
};

export default App;