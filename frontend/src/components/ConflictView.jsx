import React, { useState } from 'react';
import { 
  AlertTriangle, 
  Train, 
  Clock, 
  MapPin, 
  ShieldAlert, 
  TrendingDown, 
  CheckCircle,
  HelpCircle
} from 'lucide-react';

export default function ConflictView({ conflicts }) {
  const [filterSeverity, setFilterSeverity] = useState('ALL');

  const conflictList = conflicts?.conflicts || [];
  const totalCost = conflicts?.total_disruption_cost || 0;

  // Flatten conflicts to individual train-block events
  const events = [];
  conflictList.forEach((c) => {
    c.affected_trains.forEach((t) => {
      // Determine severity
      let severity = 'Medium';
      let sevColor = 'text-amber-400 bg-amber-500/15 border-amber-500/30';
      if (t.priority === 'high' || t.train_type === 'superfast' || t.total_cost >= 60) {
        severity = 'Critical';
        sevColor = 'text-rose-400 bg-rose-500/15 border-rose-500/30';
      } else if (t.priority === 'medium' || t.total_cost >= 30) {
        severity = 'High';
        sevColor = 'text-orange-400 bg-orange-500/15 border-orange-500/30';
      } else {
        severity = 'Low';
        sevColor = 'text-blue-400 bg-blue-500/15 border-blue-500/30';
      }

      events.push({
        blockId: c.block_id,
        sectionId: c.section_id,
        blockStart: c.start_time,
        blockEnd: c.end_time,
        blockDuration: c.duration_minutes,
        trainId: t.train_id,
        trainType: t.train_type,
        trainPriority: t.priority,
        overlapMinutes: t.overlap_minutes,
        totalCost: t.total_cost,
        severity,
        sevColor,
      });
    });
  });

  const filteredEvents = events.filter((e) => {
    if (filterSeverity === 'ALL') return true;
    return e.severity.toLowerCase() === filterSeverity.toLowerCase();
  });

  return (
    <div className="space-y-6">
      {/* Overview Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="glass-panel p-4 rounded-xl border border-slate-800 bg-slate-900/60">
          <div className="flex items-center space-x-2 text-slate-400 text-xs font-semibold mb-1">
            <Train className="w-4 h-4 text-blue-400" />
            <span>Conflicting Train Events</span>
          </div>
          <div className="text-2xl font-extrabold text-white">{events.length}</div>
          <p className="text-[11px] text-slate-400 mt-1">Across {conflictList.length} block windows</p>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-slate-800 bg-slate-900/60">
          <div className="flex items-center space-x-2 text-slate-400 text-xs font-semibold mb-1">
            <TrendingDown className="w-4 h-4 text-rose-400" />
            <span>Total Operational Disruption Penalty</span>
          </div>
          <div className="text-2xl font-extrabold text-rose-400">-{totalCost} pts</div>
          <p className="text-[11px] text-slate-400 mt-1">Potential regulation delay cost</p>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-slate-800 bg-slate-900/60">
          <div className="flex items-center space-x-2 text-slate-400 text-xs font-semibold mb-1">
            <ShieldAlert className="w-4 h-4 text-amber-400" />
            <span>High Severity Conflicts</span>
          </div>
          <div className="text-2xl font-extrabold text-amber-400">
            {events.filter((e) => e.severity === 'Critical' || e.severity === 'High').length}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Express / Superfast trains affected</p>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="glass-panel p-3 rounded-xl border border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-2 text-xs text-slate-300 font-semibold">
          <AlertTriangle className="w-4 h-4 text-amber-400" />
          <span>Train Conflict & Operational Impact Registry</span>
        </div>

        <div className="flex items-center space-x-1">
          {['ALL', 'Critical', 'High', 'Medium', 'Low'].map((sev) => (
            <button
              key={sev}
              onClick={() => setFilterSeverity(sev)}
              className={`px-2.5 py-1 rounded-md text-xs font-semibold transition-all ${
                filterSeverity === sev
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-400 hover:text-slate-200 bg-slate-900'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {/* Conflicts Table */}
      <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                <th className="py-3 px-4">Train ID & Type</th>
                <th className="py-3 px-3">Train Priority</th>
                <th className="py-3 px-3">Section</th>
                <th className="py-3 px-3">Block Window</th>
                <th className="py-3 px-3">Conflict Type</th>
                <th className="py-3 px-3">Overlap Duration</th>
                <th className="py-3 px-3">Severity</th>
                <th className="py-3 px-4">Disruption Cost</th>
                <th className="py-3 px-4">CP-SAT Optimizer Strategy</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 bg-slate-900/40">
              {filteredEvents.map((evt, idx) => (
                <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                  {/* Train */}
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2">
                      <Train className="w-3.5 h-3.5 text-blue-400" />
                      <div>
                        <strong className="text-white font-mono">{evt.trainId}</strong>
                        <div className="text-[10px] text-slate-400 capitalize">{evt.trainType}</div>
                      </div>
                    </div>
                  </td>

                  {/* Priority */}
                  <td className="py-3 px-3 font-semibold uppercase text-[10px]">
                    <span className={`px-2 py-0.5 rounded-full border ${
                      evt.trainPriority === 'high' ? 'bg-rose-500/10 text-rose-400 border-rose-500/25' : 'bg-slate-800 text-slate-300 border-slate-700'
                    }`}>
                      {evt.trainPriority}
                    </span>
                  </td>

                  {/* Section */}
                  <td className="py-3 px-3 font-mono font-bold text-slate-300">
                    {evt.sectionId}
                  </td>

                  {/* Block */}
                  <td className="py-3 px-3 font-mono text-slate-400">
                    {evt.blockId}
                  </td>

                  {/* Conflict Type */}
                  <td className="py-3 px-3 text-slate-300">
                    Direct Slot Overlap
                  </td>

                  {/* Overlap Minutes */}
                  <td className="py-3 px-3 font-mono font-bold text-amber-400">
                    {evt.overlapMinutes} min
                  </td>

                  {/* Severity */}
                  <td className="py-3 px-3">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${evt.sevColor}`}>
                      {evt.severity}
                    </span>
                  </td>

                  {/* Cost */}
                  <td className="py-3 px-4 font-mono font-bold text-rose-400">
                    -{evt.totalCost} pts
                  </td>

                  {/* CP-SAT Strategy */}
                  <td className="py-3 px-4 text-[11px] text-slate-300">
                    {evt.severity === 'Critical' ? (
                      <span className="text-rose-300">
                        High disruption penalty: CP-SAT steers routine maintenance into White Windows unless task is Critical emergency.
                      </span>
                    ) : (
                      <span className="text-slate-400">
                        Minor traffic regulation: Acceptable for urgent track repair when Net Value exceeds delay penalty.
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
