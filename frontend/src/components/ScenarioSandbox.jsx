import React, { useState } from 'react';
import { 
  Sparkles, 
  RotateCw, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  ShieldAlert, 
  Calendar, 
  ArrowRight,
  Clock,
  Layers,
  CheckCircle2,
  Zap
} from 'lucide-react';
import { apiService } from '../services/api';

const SCENARIOS = [
  {
    id: 'A',
    title: 'Scenario A: Normal Operations',
    tag: 'Baseline',
    color: 'blue',
    icon: CheckCircle2,
    desc: 'Standard train timetable, all scheduled crews available, routine and cyclic backlog.',
    accent: 'border-blue-500/30 bg-blue-500/5',
  },
  {
    id: 'B',
    title: 'Scenario B: +20% Train Traffic',
    tag: 'Traffic Surge',
    color: 'amber',
    icon: TrendingUp,
    desc: '20% more train movements injected (extra express and freight paths), raising daytime disruption costs.',
    accent: 'border-amber-500/30 bg-amber-500/5',
  },
  {
    id: 'C',
    title: 'Scenario C: Crew Unavailable',
    tag: 'Resource Outage',
    color: 'rose',
    icon: AlertTriangle,
    desc: 'Primary P-Way crew (RES001) is taken off-duty. Tests CP-SAT dynamic crew re-allocation to RES002.',
    accent: 'border-rose-500/30 bg-rose-500/5',
  },
  {
    id: 'D',
    title: 'Scenario D: Critical Asset Failure',
    tag: 'Emergency Breakdown',
    color: 'purple',
    icon: Zap,
    desc: 'Sudden rail fracture on AST005 (km 31.5) with 6h deadline. Tests emergency priority preemption.',
    accent: 'border-purple-500/30 bg-purple-500/5',
  },
  {
    id: 'E',
    title: 'Scenario E: Extra Block Windows',
    tag: 'Capacity Expansion',
    color: 'emerald',
    icon: Layers,
    desc: 'Operating control grants extended 240m night blocks and additional afternoon shadow windows.',
    accent: 'border-emerald-500/30 bg-emerald-500/5',
  },
];

import { useAuth } from '../context/AuthContext';
import { Lock } from 'lucide-react';

export default function ScenarioSandbox({ horizon = 'weekly', initialScenario = 'D' }) {
  const { currentUser, isController } = useAuth();
  const [selectedScenario, setSelectedScenario] = useState(initialScenario);
  const [isRunning, setIsRunning] = useState(false);
  const [comparison, setComparison] = useState(null);
  const [error, setError] = useState(null);

  const handleRunScenario = async (scenId) => {
    setIsRunning(true);
    setSelectedScenario(scenId);
    setError(null);

    try {
      const data = await apiService.runScenario(scenId, horizon);
      setComparison(data);
    } catch (err) {
      console.error('Failed to run scenario', err);
      if (err.response?.status === 403) {
        setError('Action Restricted: Only Chief Section Controllers (DOM) can execute What-If simulations. Switch to Rajesh Sharma in the top right.');
      } else {
        setError('Could not run scenario on server. Check backend status.');
      }
    } finally {
      setIsRunning(false);
    }
  };

  React.useEffect(() => {
    if (initialScenario) {
      setSelectedScenario(initialScenario);
      handleRunScenario(initialScenario);
    }
  }, [initialScenario, horizon]);

  return (
    <div className="space-y-6">
      {/* Introduction Card */}
      <div className="glass-panel p-5 rounded-2xl border border-slate-800 bg-gradient-to-r from-blue-900/20 via-indigo-900/20 to-purple-900/20 shadow-xl">
        <div className="flex items-center space-x-3 mb-2">
          <div className="p-2 rounded-xl bg-purple-500/20 border border-purple-500/30 text-purple-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-heading font-extrabold text-lg text-white">
              What-If & Real-Time Operational Scenario Sandbox
            </h2>
            <p className="text-xs text-slate-300">
              Demonstrates that OptRail-AI dynamically recalculates optimal possession windows and crew rosters when unexpected disruptions occur.
            </p>
          </div>
        </div>
      </div>

      {/* RBAC Notice if not Controller */}
      {!isController && currentUser && (
        <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-center justify-between animate-in fade-in duration-150">
          <div className="flex items-center space-x-2">
            <Lock className="w-4 h-4 text-amber-400 shrink-0" />
            <span>
              Simulation Dispatch is restricted to <strong>Chief Section Controllers (DOM)</strong>. Switch to Rajesh Sharma in the top right to execute live What-If solver runs.
            </span>
          </div>
          <span className="font-mono text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500/20 border border-amber-500/30 shrink-0">
            READ-ONLY AUDIT
          </span>
        </div>
      )}

      {/* Scenario Selection Grid */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
        {SCENARIOS.map((scen) => {
          const Icon = scen.icon;
          const isSelected = selectedScenario === scen.id;

          return (
            <div
              key={scen.id}
              onClick={() => handleRunScenario(scen.id)}
              className={`glass-panel p-3.5 rounded-xl border cursor-pointer transition-all hover:scale-[1.02] flex flex-col justify-between ${
                isSelected
                  ? 'border-blue-500 bg-slate-900 shadow-lg shadow-blue-500/20 ring-1 ring-blue-500'
                  : 'border-slate-800 bg-slate-950/70 hover:border-slate-700'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono font-bold text-xs text-blue-400">
                    [{scen.id}]
                  </span>
                  <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full border ${scen.accent}`}>
                    {scen.tag}
                  </span>
                </div>
                <h4 className="font-bold text-xs text-white mb-1.5 leading-snug">
                  {scen.title}
                </h4>
                <p className="text-[11px] text-slate-400 leading-relaxed mb-3">
                  {scen.desc}
                </p>
              </div>

              <button
                disabled={isRunning}
                className={`w-full py-1.5 rounded-lg text-[11px] font-bold transition-all flex items-center justify-center space-x-1.5 ${
                  isSelected
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                {isRunning && isSelected ? (
                  <RotateCw className="w-3.5 h-3.5 animate-spin text-blue-300" />
                ) : (
                  <Sparkles className="w-3.5 h-3.5" />
                )}
                <span>{isRunning && isSelected ? 'Simulating...' : 'Simulate'}</span>
              </button>
            </div>
          );
        })}
      </div>

      {/* Comparison & Impact Analysis Results */}
      {comparison && (
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-6 bg-slate-900/50 shadow-2xl">
          {/* Header */}
          <div className="flex flex-wrap items-center justify-between border-b border-slate-800 pb-4 gap-2">
            <div>
              <span className="text-[10px] uppercase tracking-wider font-extrabold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/25">
                Scenario {comparison.scenario_id} Impact Differential
              </span>
              <h3 className="font-heading font-extrabold text-xl text-white mt-1">
                {comparison.scenario_name}
              </h3>
              <p className="text-xs text-slate-400">{comparison.scenario_description}</p>
            </div>

            <div className="flex items-center space-x-3 bg-slate-950 px-4 py-2 rounded-xl border border-slate-800">
              <span className="text-xs text-slate-400">Net Value Impact:</span>
              <span className={`text-xl font-mono font-extrabold ${
                comparison.delta.net_value >= 0 ? 'text-emerald-400' : 'text-rose-400'
              }`}>
                {comparison.delta.net_value >= 0 ? `+${comparison.delta.net_value}` : comparison.delta.net_value} pts
              </span>
            </div>
          </div>

          {/* Metric Comparison Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-bold uppercase text-[10px]">
                  <th className="py-2.5 px-4">Metric</th>
                  <th className="py-2.5 px-3">Baseline (Scenario A)</th>
                  <th className="py-2.5 px-3">Scenario ({comparison.scenario_id})</th>
                  <th className="py-2.5 px-4 font-mono">Delta / Perturbation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 bg-slate-950/30">
                <tr>
                  <td className="py-2.5 px-4 font-semibold text-slate-300">Tasks Scheduled</td>
                  <td className="py-2.5 px-3 text-slate-400">{comparison.baseline_summary.tasks_scheduled} / {comparison.baseline_summary.tasks_total}</td>
                  <td className="py-2.5 px-3 text-white font-bold">{comparison.scenario_summary.tasks_scheduled} / {comparison.scenario_summary.tasks_total}</td>
                  <td className={`py-2.5 px-4 font-mono font-bold ${
                    comparison.delta.tasks_scheduled >= 0 ? 'text-emerald-400' : 'text-rose-400'
                  }`}>
                    {comparison.delta.tasks_scheduled >= 0 ? `+${comparison.delta.tasks_scheduled}` : comparison.delta.tasks_scheduled}
                  </td>
                </tr>
                <tr>
                  <td className="py-2.5 px-4 font-semibold text-slate-300">Blocks Possessed / Activated</td>
                  <td className="py-2.5 px-3 text-slate-400">{comparison.baseline_summary.blocks_activated} / {comparison.baseline_summary.blocks_total}</td>
                  <td className="py-2.5 px-3 text-white font-bold">{comparison.scenario_summary.blocks_activated} / {comparison.scenario_summary.blocks_total}</td>
                  <td className="py-2.5 px-4 font-mono font-bold text-slate-300">
                    {comparison.delta.blocks_activated >= 0 ? `+${comparison.delta.blocks_activated}` : comparison.delta.blocks_activated}
                  </td>
                </tr>
                <tr>
                  <td className="py-2.5 px-4 font-semibold text-slate-300">Gross Maintenance Value</td>
                  <td className="py-2.5 px-3 text-slate-400">{comparison.baseline_summary.total_gross_value} pts</td>
                  <td className="py-2.5 px-3 text-white font-bold">{comparison.scenario_summary.total_gross_value} pts</td>
                  <td className="py-2.5 px-4 font-mono font-bold text-blue-400">
                    +{comparison.scenario_summary.total_gross_value - comparison.baseline_summary.total_gross_value} pts
                  </td>
                </tr>
                <tr>
                  <td className="py-2.5 px-4 font-semibold text-slate-300">Railway Operations Disruption Cost</td>
                  <td className="py-2.5 px-3 text-slate-400">-{comparison.baseline_summary.total_operations_cost} pts</td>
                  <td className="py-2.5 px-3 text-rose-400 font-bold">-{comparison.scenario_summary.total_operations_cost} pts</td>
                  <td className={`py-2.5 px-4 font-mono font-bold ${
                    comparison.delta.operations_cost <= 0 ? 'text-emerald-400' : 'text-rose-400'
                  }`}>
                    {comparison.delta.operations_cost >= 0 ? `+${comparison.delta.operations_cost}` : comparison.delta.operations_cost} pts
                  </td>
                </tr>
                <tr className="bg-slate-900/60 font-bold">
                  <td className="py-3 px-4 text-white">FINAL NET SCHEDULE VALUE</td>
                  <td className="py-3 px-3 text-slate-300">+{comparison.baseline_summary.total_net_value} pts</td>
                  <td className="py-3 px-3 text-purple-400 text-sm">+{comparison.scenario_summary.total_net_value} pts</td>
                  <td className={`py-3 px-4 font-mono text-sm ${
                    comparison.delta.net_value >= 0 ? 'text-emerald-400' : 'text-rose-400'
                  }`}>
                    {comparison.delta.net_value >= 0 ? `+${comparison.delta.net_value}` : comparison.delta.net_value} pts
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Operational Insights Bullets */}
          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
            <h4 className="font-heading font-bold text-xs uppercase tracking-wider text-slate-400 flex items-center space-x-2">
              <Sparkles className="w-3.5 h-3.5 text-blue-400" />
              <span>CP-SAT Autonomous Decision Insights</span>
            </h4>
            <ul className="space-y-1 text-xs text-slate-300">
              {comparison.insights.map((ins, idx) => (
                <li key={idx} className="flex items-start space-x-2">
                  <span className="text-blue-400 font-bold">•</span>
                  <span>{ins}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Schedule Perturbations / Rescheduled Tasks */}
          {comparison.schedule_changes && comparison.schedule_changes.length > 0 ? (
            <div>
              <h4 className="font-heading font-bold text-xs uppercase tracking-wider text-slate-400 mb-2">
                Rescheduled & Perturbed Maintenance Tasks ({comparison.schedule_changes.length})
              </h4>
              <div className="space-y-2">
                {comparison.schedule_changes.map((chg, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex flex-wrap items-center justify-between text-xs gap-2"
                  >
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        chg.change_type.includes('NEW')
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          : chg.change_type.includes('DEFERRED')
                          ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                          : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      }`}>
                        {chg.change_type}
                      </span>
                      <strong className="text-white font-mono">{chg.task_id}</strong>
                    </div>
                    <span className="text-slate-300 text-[11px] font-mono">{chg.details}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic">No task rescheduling required for this scenario.</p>
          )}
        </div>
      )}
    </div>
  );
}
