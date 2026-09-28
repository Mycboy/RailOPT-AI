import React, { useState } from 'react';
import { 
  Layers, 
  Search, 
  Filter, 
  ShieldAlert, 
  CheckCircle2, 
  Clock, 
  Wrench,
  AlertTriangle,
  ArrowUpRight
} from 'lucide-react';

export default function AssetView({ assets, schedule, onSimulateFailure }) {
  const [search, setSearch] = useState('');
  const [criticalityFilter, setCriticalityFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Build upcoming maintenance lookup from schedule
  const upcomingMaintenanceMap = {};
  if (schedule) {
    Object.values(schedule).forEach((blocks) => {
      blocks.forEach((b) => {
        b.activities.forEach((act) => {
          if (!upcomingMaintenanceMap[act.asset_id]) {
            upcomingMaintenanceMap[act.asset_id] = [];
          }
          upcomingMaintenanceMap[act.asset_id].push({
            taskId: act.task_id,
            taskType: act.task_type,
            time: `${act.scheduled_start}–${act.scheduled_end}`,
            window: b.block_id,
            section: b.section_id,
            crew: act.crew_name,
            priority: act.priority,
          });
        });
      });
    });
  }

  const filteredAssets = (assets || []).filter((a) => {
    const matchesSearch = 
      a.asset_id.toLowerCase().includes(search.toLowerCase()) ||
      a.asset_code.toLowerCase().includes(search.toLowerCase()) ||
      a.section_id.toLowerCase().includes(search.toLowerCase());

    const matchesCriticality = 
      criticalityFilter === 'ALL' || a.criticality.toLowerCase() === criticalityFilter.toLowerCase();

    const matchesStatus = 
      statusFilter === 'ALL' || a.status.toLowerCase() === statusFilter.toLowerCase();

    return matchesSearch && matchesCriticality && matchesStatus;
  });

  const getConditionColor = (score) => {
    if (score >= 80) return 'text-emerald-400 bg-emerald-500';
    if (score >= 60) return 'text-amber-400 bg-amber-500';
    return 'text-rose-400 bg-rose-500';
  };

  return (
    <div className="space-y-6">
      {/* Top Filter Bar */}
      <div className="glass-panel p-4 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-3">
        {/* Search Input */}
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by Asset ID, Code, Section..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Filter Dropdowns */}
        <div className="flex items-center space-x-2">
          <select
            value={criticalityFilter}
            onChange={(e) => setCriticalityFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg text-xs font-medium text-slate-300 px-3 py-1.5 focus:outline-none focus:border-blue-500"
          >
            <option value="ALL">All Criticalities</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg text-xs font-medium text-slate-300 px-3 py-1.5 focus:outline-none focus:border-blue-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="Operational">Operational</option>
            <option value="Degraded">Degraded</option>
            <option value="Failed">Failed / Out of Service</option>
          </select>
        </div>
      </div>

      {/* Asset Grid / Table */}
      <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                <th className="py-3 px-4">Asset ID & Code</th>
                <th className="py-3 px-3">Type & Department</th>
                <th className="py-3 px-3">Section & Location</th>
                <th className="py-3 px-3">Criticality</th>
                <th className="py-3 px-4">Condition Score</th>
                <th className="py-3 px-3">Current Status</th>
                <th className="py-3 px-4">Upcoming Maintenance</th>
                <th className="py-3 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 bg-slate-900/40">
              {filteredAssets.map((asset) => {
                const upcoming = upcomingMaintenanceMap[asset.asset_id] || [];
                const condColor = getConditionColor(asset.condition_score);

                return (
                  <tr key={asset.asset_id} className="hover:bg-slate-800/40 transition-colors">
                    {/* ID & Code */}
                    <td className="py-3 px-4">
                      <div className="font-mono font-bold text-white text-xs">
                        {asset.asset_id}
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono">
                        {asset.asset_code}
                      </div>
                    </td>

                    {/* Type & Dept */}
                    <td className="py-3 px-3">
                      <span className="font-semibold text-slate-200">{asset.asset_type}</span>
                      <div className="text-[10px] text-slate-400">{asset.department_id}</div>
                    </td>

                    {/* Section & Location */}
                    <td className="py-3 px-3 font-mono text-slate-300">
                      <div>{asset.section_id}</div>
                      <div className="text-[10px] text-slate-500">km {asset.location_km}</div>
                    </td>

                    {/* Criticality */}
                    <td className="py-3 px-3">
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                          asset.criticality === 'Critical'
                            ? 'bg-rose-500/20 text-rose-400 border-rose-500/30'
                            : asset.criticality === 'High'
                            ? 'bg-orange-500/20 text-orange-400 border-orange-500/30'
                            : 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                        }`}
                      >
                        {asset.criticality}
                      </span>
                    </td>

                    {/* Condition Score Gauge */}
                    <td className="py-3 px-4">
                      <div className="flex items-center space-x-2">
                        <div className="w-20 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${condColor.split(' ')[1]}`}
                            style={{ width: `${asset.condition_score}%` }}
                          ></div>
                        </div>
                        <span className={`font-mono font-bold text-xs ${condColor.split(' ')[0]}`}>
                          {asset.condition_score}/100
                        </span>
                      </div>
                    </td>

                    {/* Status */}
                    <td className="py-3 px-3">
                      <span
                        className={`inline-flex items-center space-x-1 text-[11px] font-semibold ${
                          asset.status === 'Operational'
                            ? 'text-emerald-400'
                            : asset.status === 'Degraded'
                            ? 'text-amber-400'
                            : 'text-rose-400'
                        }`}
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${
                          asset.status === 'Operational' ? 'bg-emerald-400' : 'bg-rose-400'
                        }`}></span>
                        <span>{asset.status}</span>
                      </span>
                    </td>

                    {/* Upcoming Maintenance */}
                    <td className="py-3 px-4">
                      {upcoming.length > 0 ? (
                        <div className="space-y-1">
                          {upcoming.slice(0, 1).map((m, idx) => (
                            <div key={idx} className="bg-slate-950/60 p-1.5 rounded border border-slate-800 text-[11px]">
                              <div className="font-semibold text-blue-400 flex items-center justify-between">
                                <span>{m.taskId}: {m.taskType}</span>
                                <span className="text-[10px] text-slate-400">{m.time}</span>
                              </div>
                              <div className="text-[10px] text-slate-400 truncate">
                                Window: {m.window} • Crew: {m.crew}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <span className="text-slate-500 text-[11px] italic">No scheduled maintenance</span>
                      )}
                    </td>

                    {/* Action */}
                    <td className="py-3 px-3 text-right">
                      {onSimulateFailure && (
                        <button
                          onClick={() => onSimulateFailure(asset.asset_id)}
                          className="px-2 py-1 rounded bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/25 text-[10px] font-bold transition-all"
                          title="Simulate Critical Failure on this asset"
                        >
                          Simulate Failure
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
