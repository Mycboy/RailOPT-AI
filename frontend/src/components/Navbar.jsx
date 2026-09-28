import React from 'react';
import { 
  TrainTrack, 
  RotateCw, 
  Calendar, 
  Layers, 
  Radio, 
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  Award
} from 'lucide-react';

export default function Navbar({
  horizon,
  onHorizonChange,
  onOptimize,
  isOptimizing,
  activeTab,
  onTabChange,
  status
}) {
  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800 bg-slate-950/85">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo & Name */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-400 p-0.5 shadow-lg shadow-blue-500/20">
              <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <TrainTrack className="w-5 h-5 text-blue-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-heading font-extrabold text-xl tracking-tight text-white">
                  OptRail<span className="text-blue-500">-AI</span>
                </span>
                <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/25">
                  CP-SAT 2.0
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium hidden sm:block">
                Indian Railways Maintenance Window & Traffic Optimizer
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="hidden md:flex items-center space-x-1 bg-slate-900/80 p-1 rounded-xl border border-slate-800">
            {[
              { id: 'benchmark', label: 'Before vs After', icon: Award },
              { id: 'plan', label: 'Maintenance Plan', icon: Calendar },
              { id: 'map', label: 'Network GIS Map', icon: TrainTrack },
              { id: 'assets', label: 'Asset View', icon: Layers },
              { id: 'conflicts', label: 'Train Conflicts', icon: AlertTriangle },
              { id: 'scenarios', label: 'What-If Engine', icon: Sparkles },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => onTabChange(tab.id)}
                  className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Right Action Bar: Horizon Toggle + Optimize Button */}
          <div className="flex items-center space-x-3">
            {/* Horizon Selector */}
            <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5">
              {[
                { id: 'daily', label: 'Daily (24h)' },
                { id: 'weekly', label: 'Weekly (7d)' },
                { id: 'monthly', label: 'Monthly (30d)' },
              ].map((h) => (
                <button
                  key={h.id}
                  onClick={() => onHorizonChange(h.id)}
                  className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-all ${
                    horizon === h.id
                      ? 'bg-slate-800 text-blue-400 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {h.label}
                </button>
              ))}
            </div>

            {/* Live Re-Optimize Button */}
            <button
              onClick={onOptimize}
              disabled={isOptimizing}
              className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-bold text-white transition-all shadow-md ${
                isOptimizing
                  ? 'bg-slate-800 text-slate-400 cursor-not-allowed'
                  : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 shadow-blue-600/25 active:scale-95'
              }`}
            >
              <RotateCw className={`w-3.5 h-3.5 ${isOptimizing ? 'animate-spin text-blue-400' : ''}`} />
              <span>{isOptimizing ? 'Solving CP-SAT...' : 'Re-Optimize'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Tab Bar */}
      <div className="md:hidden flex items-center justify-around border-t border-slate-800/80 bg-slate-950/95 py-2 px-2">
        {[
          { id: 'benchmark', label: 'Before/After', icon: Award },
          { id: 'plan', label: 'Plan', icon: Calendar },
          { id: 'map', label: 'GIS Map', icon: TrainTrack },
          { id: 'assets', label: 'Assets', icon: Layers },
          { id: 'conflicts', label: 'Conflicts', icon: AlertTriangle },
          { id: 'scenarios', label: 'What-If', icon: Sparkles },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`flex flex-col items-center space-y-0.5 text-[10px] font-medium ${
                isActive ? 'text-blue-400' : 'text-slate-400'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>
    </header>
  );
}
