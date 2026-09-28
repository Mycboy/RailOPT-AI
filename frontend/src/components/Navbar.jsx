import React, { useState } from 'react';
import { 
  TrainTrack, 
  RotateCw, 
  Calendar, 
  Layers, 
  Radio, 
  Sparkles, 
  CheckCircle2, 
  AlertTriangle, 
  Award, 
  Lock, 
  PlusCircle 
} from 'lucide-react';
import RoleSwitcher from './RoleSwitcher';
import RequestTaskModal from './RequestTaskModal';
import { useAuth } from '../context/AuthContext';

export default function Navbar({
  horizon,
  onHorizonChange,
  onOptimize,
  isOptimizing,
  activeTab,
  onTabChange,
  status,
  onTaskCreated
}) {
  const { currentUser } = useAuth();
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);

  const canOptimize = currentUser?.can_optimize ?? true;

  return (
    <>
      <header className="sticky top-0 z-50 glass-panel border-b border-slate-800 bg-slate-950/90 backdrop-blur-md">
        <div className="w-full max-w-[1700px] mx-auto px-3 sm:px-5 lg:px-6">
          <div className="flex items-center justify-between h-16 gap-2">
            {/* Brand Logo & Name */}
            <div className="flex items-center space-x-2.5 shrink-0">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-cyan-400 p-0.5 shadow-md shadow-blue-500/20 shrink-0">
                <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                  <TrainTrack className="w-5 h-5 text-blue-400" />
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <span className="font-heading font-extrabold text-lg sm:text-xl tracking-tight text-white">
                  OptRail<span className="text-blue-500">-AI</span>
                </span>
                <span className="text-[9px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/25 shrink-0">
                  CP-SAT
                </span>
              </div>
            </div>

            {/* Navigation Tabs (Concise labels for perfect fit) */}
            <nav className="hidden lg:flex items-center space-x-0.5 bg-slate-900/90 p-1 rounded-xl border border-slate-800 shrink-0">
              {[
                { id: 'benchmark', label: 'Benchmark', icon: Award },
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
                    className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      isActive
                        ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5 shrink-0" />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </nav>

            {/* Right Action Bar */}
            <div className="flex items-center space-x-2 shrink-0">
              {/* Request Block Button */}
              <button
                onClick={() => setIsTaskModalOpen(true)}
                className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg text-xs font-bold bg-slate-900 hover:bg-slate-800 text-blue-400 border border-blue-500/30 hover:border-blue-500/50 shadow-sm transition-all shrink-0"
                title="File a departmental maintenance possession memo"
              >
                <PlusCircle className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                <span className="hidden sm:inline">Request Block</span>
              </button>

              {/* Horizon Selector */}
              <div className="hidden sm:flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5 shrink-0">
                {[
                  { id: 'daily', label: '24h' },
                  { id: 'weekly', label: '7d' },
                  { id: 'monthly', label: '30d' },
                ].map((h) => (
                  <button
                    key={h.id}
                    onClick={() => onHorizonChange(h.id)}
                    className={`px-2 py-1 text-[11px] font-semibold rounded-md transition-all ${
                      horizon === h.id
                        ? 'bg-slate-800 text-blue-400 shadow-sm'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {h.label}
                  </button>
                ))}
              </div>

              {/* Live Re-Optimize Button (Guarded by RBAC) */}
              {canOptimize ? (
                <button
                  onClick={onOptimize}
                  disabled={isOptimizing}
                  className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-bold text-white transition-all shadow-md shrink-0 ${
                    isOptimizing
                      ? 'bg-slate-800 text-slate-400 cursor-not-allowed'
                      : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 shadow-blue-600/25 active:scale-95'
                  }`}
                  title="Section Controller Global CP-SAT Optimization"
                >
                  <RotateCw className={`w-3.5 h-3.5 ${isOptimizing ? 'animate-spin text-blue-400' : ''} shrink-0`} />
                  <span>{isOptimizing ? 'Solving...' : 'Re-Optimize'}</span>
                </button>
              ) : (
                <div
                  className="flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-900 border border-slate-800 text-slate-500 cursor-not-allowed shrink-0"
                  title="Restricted: Only Chief Section Controllers (DOM) can execute global timetable re-optimization."
                >
                  <Lock className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                  <span className="hidden sm:inline">Ctrl Only</span>
                </div>
              )}

              {/* Indian Railways Persona / RBAC Role Switcher */}
              <RoleSwitcher />
            </div>
          </div>
        </div>

        {/* Mobile Tab Bar */}
        <div className="lg:hidden flex items-center justify-around border-t border-slate-800/80 bg-slate-950/95 py-2 px-2">
          {[
            { id: 'benchmark', label: 'Benchmark', icon: Award },
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

      {/* Modal Requisition Dialog */}
      <RequestTaskModal
        isOpen={isTaskModalOpen}
        onClose={() => setIsTaskModalOpen(false)}
        onTaskCreated={(task) => {
          if (onTaskCreated) onTaskCreated(task);
        }}
      />
    </>
  );
}
