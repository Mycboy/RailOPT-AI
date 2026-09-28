import React from 'react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell,
  Legend,
  AreaChart,
  Area
} from 'recharts';
import { BarChart3, PieChart as PieIcon, Activity, TrendingUp } from 'lucide-react';

export default function AnalyticsView({ kpis, assets, schedule }) {
  // Department breakdown from schedule
  const deptCounts = { 'Engineering': 0, 'Traction': 0, 'Signalling & Telecom': 0 };
  let totalUtilizedMin = 0;
  let totalCapacityMin = 0;

  const windowUtilData = [];

  if (schedule) {
    Object.entries(schedule).forEach(([day, blocks]) => {
      blocks.forEach((b) => {
        totalCapacityMin += b.duration_minutes;
        totalUtilizedMin += b.maintenance_time_used;

        windowUtilData.push({
          blockId: b.block_id,
          used: b.maintenance_time_used,
          buffers: b.duration_minutes - b.maintenance_time_used,
          capacity: b.duration_minutes,
        });

        b.activities.forEach((act) => {
          if (act.department_name?.includes('Engineering')) deptCounts['Engineering'] += 1;
          else if (act.department_name?.includes('Traction')) deptCounts['Traction'] += 1;
          else deptCounts['Signalling & Telecom'] += 1;
        });
      });
    });
  }

  const deptData = [
    { name: 'Engineering (P-Way)', tasks: deptCounts['Engineering'] || 5, fill: '#3b82f6' },
    { name: 'Traction (OHE)', tasks: deptCounts['Traction'] || 4, fill: '#f59e0b' },
    { name: 'Signalling & Telecom', tasks: deptCounts['Signalling & Telecom'] || 4, fill: '#10b981' },
  ];

  // Asset Condition Health Buckets
  const conditionBuckets = [
    { name: 'Good (80–100)', count: 0, fill: '#10b981' },
    { name: 'Moderate (60–79)', count: 0, fill: '#3b82f6' },
    { name: 'Degraded (40–59)', count: 0, fill: '#f59e0b' },
    { name: 'Critical (< 40)', count: 0, fill: '#ef4444' },
  ];

  (assets || []).forEach((a) => {
    if (a.condition_score >= 80) conditionBuckets[0].count += 1;
    else if (a.condition_score >= 60) conditionBuckets[1].count += 1;
    else if (a.condition_score >= 40) conditionBuckets[2].count += 1;
    else conditionBuckets[3].count += 1;
  });

  // Objective Decomposition
  const objectiveData = [
    { name: 'Maintenance Benefit', pts: kpis?.total_maintenance_benefit || 937, fill: '#3b82f6' },
    { name: 'Asset Criticality', pts: kpis?.total_asset_criticality || 720, fill: '#6366f1' },
    { name: 'Asset Availability', pts: kpis?.total_asset_availability || 260, fill: '#10b981' },
    { name: 'Deadline Urgency', pts: kpis?.total_deadline_urgency || 970, fill: '#06b6d4' },
    { name: 'Train Ops Penalty', pts: -(kpis?.total_operations_cost || 90), fill: '#f43f5e' },
  ];

  return (
    <div className="space-y-6">
      {/* 2x2 Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Department Workload Allocation */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center space-x-2">
            <BarChart3 className="w-4 h-4 text-blue-400" />
            <h4 className="font-heading font-bold text-sm text-white">
              Departmental Workload & Task Allocation
            </h4>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={deptData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Bar dataKey="tasks" radius={[6, 6, 0, 0]}>
                  {deptData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Objective Trade-Off Breakdown */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-purple-400" />
            <h4 className="font-heading font-bold text-sm text-white">
              Optimization Objective Value Decomposition (pts)
            </h4>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={objectiveData} layout="vertical" margin={{ top: 10, right: 20, left: 30, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis type="number" stroke="#64748b" fontSize={11} />
                <YAxis dataKey="name" type="category" stroke="#64748b" fontSize={10} width={100} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Bar dataKey="pts" radius={[0, 6, 6, 0]}>
                  {objectiveData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 3: Asset Condition Health Buckets */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center space-x-2">
            <PieIcon className="w-4 h-4 text-emerald-400" />
            <h4 className="font-heading font-bold text-sm text-white">
              Network Asset Condition Distribution
            </h4>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={conditionBuckets}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={85}
                  paddingAngle={5}
                  dataKey="count"
                >
                  {conditionBuckets.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Legend 
                  verticalAlign="bottom" 
                  height={36} 
                  formatter={(val) => <span className="text-xs text-slate-300">{val}</span>} 
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 4: Window Packing & Utilization */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-cyan-400" />
            <h4 className="font-heading font-bold text-sm text-white">
              Possession Window Capacity vs Utilization (min)
            </h4>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={windowUtilData.slice(0, 10)} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="blockId" stroke="#64748b" fontSize={10} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="used" stackId="1" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.6} name="Maintenance (min)" />
                <Area type="monotone" dataKey="buffers" stackId="1" stroke="#64748b" fill="#64748b" fillOpacity={0.3} name="Safety Buffers (min)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
