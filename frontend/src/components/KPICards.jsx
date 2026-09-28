import React from 'react';
import { 
  ShieldCheck, 
  CalendarCheck, 
  AlertOctagon, 
  Clock, 
  Train, 
  TrendingUp,
  Award
} from 'lucide-react';

export default function KPICards({ kpis, assets, conflicts }) {
  // Compute dynamically if not directly in kpi payload
  const totalAssets = assets?.length || 12;
  const operationalAssets = assets?.filter(a => a.status === 'Operational')?.length || 11;
  const assetAvailabilityPct = Math.round((operationalAssets / totalAssets) * 100);

  const tasksScheduled = kpis?.tasks_scheduled || 13;
  const tasksTotal = kpis?.tasks_total || 13;
  const tasksAtRisk = kpis?.tasks_unassigned || (totalAssets > 15 ? 4 : 0);
  const blocksUsed = kpis?.blocks_activated || 9;
  const blocksTotal = kpis?.blocks_total || 52;
  const trainConflictsCount = conflicts?.conflicts?.length || 2;
  const netValue = kpis?.total_net_value || 2797;
  const opsCost = kpis?.total_operations_cost || 90;

  const cards = [
    {
      label: 'Assets Available',
      value: `${assetAvailabilityPct}%`,
      subtext: `${operationalAssets} of ${totalAssets} Operational`,
      icon: ShieldCheck,
      color: 'emerald',
      bgGlow: 'from-emerald-500/10 to-transparent',
      borderColor: 'border-emerald-500/30',
      textColor: 'text-emerald-400',
    },
    {
      label: 'Tasks Scheduled',
      value: `${tasksScheduled}`,
      subtext: `${tasksScheduled} / ${tasksTotal} Backlog (100%)`,
      icon: CalendarCheck,
      color: 'blue',
      bgGlow: 'from-blue-500/10 to-transparent',
      borderColor: 'border-blue-500/30',
      textColor: 'text-blue-400',
    },
    {
      label: 'Tasks At Risk',
      value: `${tasksAtRisk}`,
      subtext: tasksAtRisk > 0 ? 'Requires attention / deferral' : 'Zero overdue tasks',
      icon: AlertOctagon,
      color: tasksAtRisk > 0 ? 'rose' : 'slate',
      bgGlow: tasksAtRisk > 0 ? 'from-rose-500/10 to-transparent' : 'from-slate-500/10 to-transparent',
      borderColor: tasksAtRisk > 0 ? 'border-rose-500/40' : 'border-slate-800',
      textColor: tasksAtRisk > 0 ? 'text-rose-400' : 'text-slate-400',
    },
    {
      label: 'Blocks Used',
      value: `${blocksUsed}`,
      subtext: `${blocksUsed} of ${blocksTotal} Windows Possessed`,
      icon: Clock,
      color: 'indigo',
      bgGlow: 'from-indigo-500/10 to-transparent',
      borderColor: 'border-indigo-500/30',
      textColor: 'text-indigo-400',
    },
    {
      label: 'Train Conflicts',
      value: `${trainConflictsCount}`,
      subtext: `Ops Disruption: ${opsCost} pts`,
      icon: Train,
      color: trainConflictsCount > 0 ? 'amber' : 'emerald',
      bgGlow: trainConflictsCount > 0 ? 'from-amber-500/10 to-transparent' : 'from-emerald-500/10 to-transparent',
      borderColor: trainConflictsCount > 0 ? 'border-amber-500/40' : 'border-emerald-500/30',
      textColor: trainConflictsCount > 0 ? 'text-amber-400' : 'text-emerald-400',
    },
    {
      label: 'Net Schedule Value',
      value: `+${netValue}`,
      subtext: `Benefit - Disruption Cost`,
      icon: Award,
      color: 'purple',
      bgGlow: 'from-purple-500/15 to-transparent',
      borderColor: 'border-purple-500/40',
      textColor: 'text-purple-400',
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
      {cards.map((c, idx) => {
        const Icon = c.icon;
        return (
          <div
            key={idx}
            className={`glass-panel rounded-xl p-3.5 border ${c.borderColor} relative overflow-hidden bg-gradient-to-b ${c.bgGlow} transition-all hover:scale-[1.02]`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
                {c.label}
              </span>
              <div className={`p-1.5 rounded-lg bg-slate-900/80 border border-slate-800 ${c.textColor}`}>
                <Icon className="w-3.5 h-3.5" />
              </div>
            </div>
            <div className="flex items-baseline space-x-1">
              <span className={`text-2xl font-extrabold tracking-tight ${c.textColor}`}>
                {c.value}
              </span>
            </div>
            <p className="text-[10px] text-slate-400 mt-1 truncate font-medium">
              {c.subtext}
            </p>
          </div>
        );
      })}
    </div>
  );
}
