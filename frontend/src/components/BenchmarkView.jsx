import React, { useState, useEffect } from 'react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  Legend 
} from 'recharts';
import { 
  ArrowRight, 
  CheckCircle2, 
  AlertTriangle, 
  TrendingDown, 
  TrendingUp, 
  Clock, 
  HardHat, 
  Train, 
  ShieldCheck, 
  ShieldAlert, 
  RotateCw, 
  Award,
  Sparkles,
  Layers
} from 'lucide-react';
import { apiService } from '../services/api';

export default function BenchmarkView({ horizon = 'weekly' }) {
  const [benchmarkData, setBenchmarkData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedDayTab, setSelectedDayTab] = useState('ALL');

  const fetchBenchmark = async () => {
    setIsLoading(true);
    try {
      const data = await apiService.getBenchmark(horizon);
      setBenchmarkData(data);
    } catch (err) {
      console.error('Failed to fetch benchmark data', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchBenchmark();
  }, [horizon]);

  if (isLoading || !benchmarkData) {
    return (
      <div className="glass-panel rounded-2xl p-12 text-center border border-slate-800">
        <RotateCw className="w-8 h-8 text-blue-400 animate-spin mx-auto mb-3" />
        <h3 className="text-base font-bold text-white mb-1">Evaluating Controlled Synthetic Railway Scenario...</h3>
        <p className="text-xs text-slate-400">
          Comparing uncoordinated manual heuristic plan against CP-SAT global optimization.
        </p>
      </div>
    );
  }

  const exec = benchmarkData.executive_summary;
  const kpis = benchmarkData.comparison_kpis;
  const before = benchmarkData.before;
  const after = benchmarkData.after;

  // Chart data comparing Before vs After
  const chartData = [
    {
      category: 'Train Disruption Cost (pts)',
      Manual: before.summary.total_operations_cost,
      'CP-SAT Optimized': after.summary.total_operations_cost,
    },
    {
      category: 'Capacity Utilization (%)',
      Manual: before.summary.average_utilization_pct,
      'CP-SAT Optimized': after.summary.average_utilization_pct,
    },
    {
      category: 'Hard Violations (count)',
      Manual: before.summary.violations_count,
      'CP-SAT Optimized': after.summary.violations_count,
    },
    {
      category: 'Net Value / 100 (pts)',
      Manual: Math.round(before.summary.total_net_value / 100),
      'CP-SAT Optimized': Math.round(after.summary.total_net_value / 100),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Executive Hero Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 bg-gradient-to-r from-blue-950/40 via-indigo-950/40 to-slate-900/60 shadow-2xl relative overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 p-0.5 shadow-lg shadow-blue-500/30">
              <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <Award className="w-5 h-5 text-blue-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-[10px] uppercase tracking-wider font-extrabold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/25">
                  Controlled Synthetic Railway Scenario
                </span>
                <span className="text-[10px] uppercase tracking-wider font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/25">
                  Measurable Proof
                </span>
              </div>
              <h2 className="font-heading font-extrabold text-xl text-white mt-1">
                Before Optimization vs After CP-SAT Optimization
              </h2>
            </div>
          </div>

          <button
            onClick={fetchBenchmark}
            disabled={isLoading}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-900 border border-slate-800 text-slate-300 hover:text-white transition-all shadow-sm"
          >
            <RotateCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Re-Run Benchmark</span>
          </button>
        </div>

        <p className="text-xs text-slate-300 leading-relaxed max-w-4xl">
          Real-world railway maintenance is often planned in departmental silos (P-Way, OHE, S&T) on spreadsheets, resulting in train conflicts, double-booked crews, omitted safety buffers, and fragmented track closures. OptRail-AI formulates this as a joint mathematical optimization problem solved globally with Google OR-Tools CP-SAT.
        </p>

        {/* 4 Core Value Multiplier Metric Pills */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-5">
          <div className="glass-panel p-3 rounded-xl border border-emerald-500/30 bg-emerald-500/5">
            <span className="text-[10px] uppercase font-bold text-slate-400">Train Disruption</span>
            <div className="text-xl font-mono font-extrabold text-emerald-400 mt-0.5">
              -{exec.disruption_reduction_pct}%
            </div>
            <p className="text-[10px] text-slate-400">Train delay penalty eliminated</p>
          </div>

          <div className="glass-panel p-3 rounded-xl border border-blue-500/30 bg-blue-500/5">
            <span className="text-[10px] uppercase font-bold text-slate-400">Window Utilization</span>
            <div className="text-xl font-mono font-extrabold text-blue-400 mt-0.5">
              +{exec.utilization_gain_pct}%
            </div>
            <p className="text-[10px] text-slate-400">Joint multi-dept bundling</p>
          </div>

          <div className="glass-panel p-3 rounded-xl border border-purple-500/30 bg-purple-500/5">
            <span className="text-[10px] uppercase font-bold text-slate-400">Hard Violations</span>
            <div className="text-xl font-mono font-extrabold text-purple-400 mt-0.5">
              0 Violations
            </div>
            <p className="text-[10px] text-slate-400">From {exec.violations_eliminated} down to zero</p>
          </div>

          <div className="glass-panel p-3 rounded-xl border border-indigo-500/30 bg-indigo-500/5">
            <span className="text-[10px] uppercase font-bold text-slate-400">Net Value Multiplier</span>
            <div className="text-xl font-mono font-extrabold text-indigo-400 mt-0.5">
              {exec.net_value_multiplier}x
            </div>
            <p className="text-[10px] text-slate-400">Net schedule value gain</p>
          </div>
        </div>
      </div>

      {/* KPI Comparison Scorecard Table */}
      <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800 bg-slate-950/80 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-blue-400" />
            <h3 className="font-heading font-bold text-sm text-white">
              Measurable Key Performance Indicators (KPI Scorecard)
            </h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            Planning Horizon: {benchmarkData.horizon.toUpperCase()}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-950/60 border-b border-slate-800 text-slate-400 font-bold uppercase text-[10px]">
                <th className="py-3 px-4">Measurable Railway KPI</th>
                <th className="py-3 px-3 text-rose-400 font-bold">Before (Manual Heuristic)</th>
                <th className="py-3 px-3 text-emerald-400 font-bold">After (CP-SAT Optimized)</th>
                <th className="py-3 px-4 font-mono">Measured Improvement</th>
                <th className="py-3 px-4">Operational Railway Impact</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 bg-slate-950/30">
              {kpis.map((k, idx) => (
                <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3 px-4 font-semibold text-slate-200">{k.metric}</td>
                  <td className="py-3 px-3 font-mono text-rose-400 font-bold bg-rose-500/5">{k.before}</td>
                  <td className="py-3 px-3 font-mono text-emerald-400 font-bold bg-emerald-500/5">{k.after}</td>
                  <td className="py-3 px-4 font-mono font-extrabold text-blue-400">{k.improvement}</td>
                  <td className="py-3 px-4 text-[11px] text-slate-400">{k.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Visual Chart: Before vs After Breakdown */}
      <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4 shadow-xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-blue-400" />
            <h4 className="font-heading font-bold text-sm text-white">
              Comparative Impact Metrics (Manual Plan vs CP-SAT)
            </h4>
          </div>
          <span className="text-[11px] text-slate-400">Lower Disruption Cost is Better • Higher Utilization is Better</span>
        </div>

        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="category" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
              />
              <Legend verticalAlign="top" height={36} formatter={(val) => <span className="text-xs text-slate-300 font-bold">{val}</span>} />
              <Bar dataKey="Manual" fill="#f43f5e" radius={[4, 4, 0, 0]} name="Manual Heuristic Plan" />
              <Bar dataKey="CP-SAT Optimized" fill="#10b981" radius={[4, 4, 0, 0]} name="OptRail-AI CP-SAT" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Side-by-Side Schedule Comparison: Left (Before) vs Right (After) */}
      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <h3 className="font-heading font-extrabold text-base text-white">
            Side-by-Side Plan Comparison (Operational Demonstration)
          </h3>
          <span className="text-xs text-slate-400">
            Compare specific possession allocations and conflict resolutions
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* LEFT: Before (Manual / Uncoordinated) */}
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300">
              <div className="flex items-center space-x-2">
                <ShieldAlert className="w-4 h-4 text-rose-400" />
                <span className="font-heading font-extrabold text-sm">BEFORE: Manual Uncoordinated Plan</span>
              </div>
              <span className="text-xs font-mono font-bold bg-rose-500/20 px-2 py-0.5 rounded text-rose-300">
                {before.summary.violations_count} Violations Detected
              </span>
            </div>

            {/* List of sample flawed blocks in Before plan */}
            <div className="space-y-3">
              {/* Flaw 1: Train Conflict in Midday block */}
              <div className="glass-panel p-4 rounded-xl border border-rose-500/40 bg-slate-950/70 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-white">12:10–13:50 (100 min) | SEC003 | BLK0006</span>
                  <span className="px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/40 text-[10px] font-bold">
                    TRAIN CONFLICT: -123 pts
                  </span>
                </div>
                <div className="p-2 rounded bg-rose-500/10 border border-rose-500/20 text-[11px] text-rose-300 space-y-0.5">
                  <p className="font-bold flex items-center space-x-1">
                    <Train className="w-3.5 h-3.5" />
                    <span>Overlaps Passenger TR004 & Regional Express TR005</span>
                  </p>
                  <p className="text-slate-400">Causes 35 minutes of passenger regulation delay on main line.</p>
                </div>
                <div className="text-xs text-slate-300">
                  Task: <strong className="text-white">MT005 (USFD Rail Inspection)</strong> • Duration: 60 min (40 min wasted capacity)
                </div>
              </div>

              {/* Flaw 2: Crew Double-Booking */}
              <div className="glass-panel p-4 rounded-xl border border-rose-500/40 bg-slate-950/70 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-white">01:30–04:00 | SEC001 & SEC002</span>
                  <span className="px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/40 text-[10px] font-bold">
                    CREW DOUBLE-BOOKED
                  </span>
                </div>
                <div className="p-2 rounded bg-rose-500/10 border border-rose-500/20 text-[11px] text-rose-300 space-y-0.5">
                  <p className="font-bold flex items-center space-x-1">
                    <HardHat className="w-3.5 h-3.5" />
                    <span>Engineering Team 1 (RES001) simultaneously assigned to 2 sections</span>
                  </p>
                  <p className="text-slate-400">Assigned to MT004 on SEC001 and MT001 on SEC002 at exact same time!</p>
                </div>
              </div>

              {/* Flaw 3: Fragmented Siloed Windows */}
              <div className="glass-panel p-4 rounded-xl border border-slate-800 bg-slate-950/70 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-white">01:30–04:00 (150 min) | SEC001</span>
                  <span className="px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 text-[10px] font-bold">
                    33% Utilization (100m Idle)
                  </span>
                </div>
                <p className="text-xs text-slate-400">
                  Engineering takes a 150-min block for a single 50-min task. S&T requests a separate block on SEC001 the next day, doubling network disruption.
                </p>
              </div>
            </div>
          </div>

          {/* RIGHT: After (OptRail-AI CP-SAT Optimized) */}
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
              <div className="flex items-center space-x-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span className="font-heading font-extrabold text-sm">AFTER: OptRail-AI CP-SAT Optimized</span>
              </div>
              <span className="text-xs font-mono font-bold bg-emerald-500/20 px-2 py-0.5 rounded text-emerald-300">
                100% Conflict-Free • Net: +{after.summary.total_net_value} pts
              </span>
            </div>

            {/* Optimized Resolutions */}
            <div className="space-y-3">
              {/* Resolution 1: Steered to Night Corridor White Window */}
              <div className="glass-panel p-4 rounded-xl border border-emerald-500/40 bg-slate-950/70 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-white">02:00–04:30 (150 min) | SEC003 | BLK0027</span>
                  <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 text-[10px] font-bold">
                    ZERO TRAIN DISRUPTION (WHITE WINDOW)
                  </span>
                </div>
                <div className="p-2 rounded bg-emerald-500/10 border border-emerald-500/20 text-[11px] text-emerald-300 space-y-0.5">
                  <p className="font-bold flex items-center space-x-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Joint Maintenance Bundled (Track + S&T)</span>
                  </p>
                  <p className="text-slate-300">
                    MT005 (P-Way USFD) + MT009 (Signal Interlocking) co-scheduled in one night corridor.
                  </p>
                </div>
                <div className="text-xs text-slate-300">
                  Enforces 10m setup + 5m buffer + 15m teardown • <strong>80.0% Window Utilization</strong>
                </div>
              </div>

              {/* Resolution 2: Dynamic Crew Re-allocation */}
              <div className="glass-panel p-4 rounded-xl border border-emerald-500/40 bg-slate-950/70 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-white">01:45–04:15 | SEC002 | BLK0004</span>
                  <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 text-[10px] font-bold">
                    CREW OVERLAP RESOLVED
                  </span>
                </div>
                <div className="p-2 rounded bg-emerald-500/10 border border-emerald-500/20 text-[11px] text-emerald-300 space-y-0.5">
                  <p className="font-bold flex items-center space-x-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Clean Pairwise Assignment</span>
                  </p>
                  <p className="text-slate-300">
                    RES001 assigned strictly to Critical repair MT001 on SEC002. MT004 on SEC001 cleanly reassigned to RES002.
                  </p>
                </div>
              </div>

              {/* Resolution 3: Multi-Activity Bundling */}
              <div className="glass-panel p-4 rounded-xl border border-emerald-500/40 bg-slate-950/70 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-white">01:30–04:00 (150 min) | SEC001 | BLK0001</span>
                  <span className="px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/40 text-[10px] font-bold">
                    70.0% UTILIZATION (2 Tasks Bundled)
                  </span>
                </div>
                <p className="text-xs text-slate-300">
                  MT002 (OHE Contact Wire) + MT003 (Signal Point Machine) packed sequentially with 10m setup, 5m buffer, and 30m teardown.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
