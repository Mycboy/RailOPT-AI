import React, { useState } from 'react';
import { 
  Calendar, 
  Clock, 
  MapPin, 
  HardHat, 
  Wrench, 
  ShieldAlert, 
  CheckCircle2, 
  ArrowRight, 
  Filter, 
  Sparkles, 
  Info,
  RotateCw
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function MaintenancePlanView({ 
  schedule, 
  pendingTasks = [], 
  onApproveAndSchedule, 
  isOptimizing = false 
}) {
  const { isController, currentUser } = useAuth();
  const [selectedDay, setSelectedDay] = useState('ALL');
  const [selectedSection, setSelectedSection] = useState('ALL');
  const [selectedDepartment, setSelectedDepartment] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  const daysList = schedule ? Object.keys(schedule) : [];

  // Automatically reset selectedDay to ALL if switching between horizons (e.g. daily/weekly/monthly)
  React.useEffect(() => {
    if (selectedDay !== 'ALL' && !daysList.includes(selectedDay)) {
      setSelectedDay('ALL');
    }
  }, [schedule, daysList, selectedDay]);

  if (!schedule || Object.keys(schedule).length === 0) {
    return (
      <div className="glass-panel rounded-2xl p-12 text-center border border-slate-800">
        <Calendar className="w-12 h-12 text-slate-500 mx-auto mb-3" />
        <h3 className="text-lg font-bold text-white mb-1">No Maintenance Schedule Generated</h3>
        <p className="text-xs text-slate-400">
          Click the "Re-Optimize" button above to run Google OR-Tools CP-SAT and generate the timetable.
        </p>
      </div>
    );
  }

  // Department colors
  const getDeptBadge = (deptId, deptName) => {
    if (deptId === 'DEP001' || deptName?.includes('Engineering')) {
      return { bg: 'bg-blue-500/15', text: 'text-blue-400', border: 'border-blue-500/30' };
    }
    if (deptId === 'DEP002' || deptName?.includes('Traction')) {
      return { bg: 'bg-amber-500/15', text: 'text-amber-400', border: 'border-amber-500/30' };
    }
    return { bg: 'bg-emerald-500/15', text: 'text-emerald-400', border: 'border-emerald-500/30' };
  };

  // Priority badges
  const getPriorityBadge = (priority) => {
    switch (priority?.toLowerCase()) {
      case 'critical':
        return 'bg-rose-500/20 text-rose-400 border-rose-500/40';
      case 'high':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/40';
      default:
        return 'bg-sky-500/20 text-sky-400 border-sky-500/40';
    }
  };

  return (
    <div className="space-y-6">
      {/* Pending Requisitions Queue Awaiting Allocation */}
      {pendingTasks && pendingTasks.length > 0 && (
        <div className="glass-panel p-4 rounded-2xl border border-amber-500/40 bg-amber-500/5 shadow-xl space-y-3 animate-in fade-in duration-200">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-amber-500/20 pb-3">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-lg bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400">
                <Clock className="w-4 h-4" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h4 className="font-heading font-extrabold text-sm text-white">
                    Queued Maintenance Requisitions ({pendingTasks.length})
                  </h4>
                  <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 font-mono">
                    Pending CP-SAT Allocation
                  </span>
                </div>
                <p className="text-[11px] text-slate-300">
                  Possession memos filed by department engineers awaiting Chief Section Controller corridor slotting.
                </p>
              </div>
            </div>

            {isController ? (
              <button
                onClick={onApproveAndSchedule}
                disabled={isOptimizing}
                className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-md shadow-blue-500/25 active:scale-95 transition-all"
              >
                <RotateCw className={`w-3.5 h-3.5 ${isOptimizing ? 'animate-spin text-blue-300' : ''}`} />
                <span>{isOptimizing ? 'Solving CP-SAT...' : 'Approve & Bundle into Timetable'}</span>
              </button>
            ) : (
              <div className="text-[11px] text-slate-400 italic">
                Logged in as {currentUser?.designation?.split('(')[0]} • Awaiting Controller Approval
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5">
            {pendingTasks.map((task) => (
              <div key={task.task_id} className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1.5 text-xs shadow-sm">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-white text-xs">{task.task_id}</span>
                  <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${
                    task.priority === 1 ? 'bg-rose-500/20 text-rose-400 border-rose-500/30' : 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                  }`}>
                    {task.priority === 1 ? 'P1 Critical' : (task.priority === 2 ? 'P2 High' : 'P3 Medium')}
                  </span>
                </div>
                <p className="font-semibold text-slate-200 truncate">{task.task_type}</p>
                <div className="text-[11px] text-slate-400 flex items-center justify-between">
                  <span>Target Asset: <strong className="text-slate-200 font-mono">{task.asset_id}</strong></span>
                  <span>Duration: <strong className="text-slate-200">{task.duration_minutes}m</strong></span>
                </div>
                {task.submitted_by && (
                  <div className="text-[10px] text-slate-500 truncate pt-1 border-t border-slate-900">
                    Requisition By: {task.submitted_by}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filter Toolbar */}
      <div className="glass-panel rounded-xl p-3 border border-slate-800 flex flex-wrap items-center justify-between gap-3">
        {/* Day Pills */}
        <div className="flex items-center space-x-1 overflow-x-auto pb-1 sm:pb-0 max-w-full">
          <button
            onClick={() => setSelectedDay('ALL')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
              selectedDay === 'ALL'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            All Days ({daysList.length})
          </button>
          {daysList.map((day) => {
            const shortName = day.split(',')[0].trim();
            const isSelected = selectedDay === day;
            return (
              <button
                key={day}
                onClick={() => setSelectedDay(day)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
                  isSelected
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                {shortName}
              </button>
            );
          })}
        </div>

        {/* Dropdown Filters */}
        <div className="flex items-center space-x-2">
          {/* Section Filter */}
          <select
            value={selectedSection}
            onChange={(e) => setSelectedSection(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg text-xs font-medium text-slate-300 px-2.5 py-1.5 focus:outline-none focus:border-blue-500"
          >
            <option value="ALL">All Sections</option>
            <option value="SEC001">SEC001 (km 0–25)</option>
            <option value="SEC002">SEC002 (km 25–52)</option>
            <option value="SEC003">SEC003 (km 52–78)</option>
            <option value="SEC004">SEC004 (km 78–105)</option>
          </select>

          {/* Department Filter */}
          <select
            value={selectedDepartment}
            onChange={(e) => setSelectedDepartment(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg text-xs font-medium text-slate-300 px-2.5 py-1.5 focus:outline-none focus:border-blue-500"
          >
            <option value="ALL">All Departments</option>
            <option value="DEP001">DEP001 • Engineering (P-Way)</option>
            <option value="DEP002">DEP002 • Traction (OHE)</option>
            <option value="DEP003">DEP003 • Signaling & Telecom (S&T)</option>
          </select>

          {/* Text Search */}
          <input
            type="text"
            placeholder="Search task, asset, crew..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-300 px-2.5 py-1.5 placeholder-slate-500 focus:outline-none focus:border-blue-500 w-44"
          />
        </div>
      </div>

      {/* Timetable Accordions */}
      {daysList
        .filter((day) => selectedDay === 'ALL' || selectedDay === day)
        .map((day) => {
          let blocks = schedule[day] || [];

          // Filter by section
          if (selectedSection !== 'ALL') {
            blocks = blocks.filter((b) => b.section_id === selectedSection);
          }

          // Filter by department
          if (selectedDepartment !== 'ALL') {
            blocks = blocks.filter((b) =>
              b.activities.some((act) => act.department_id === selectedDepartment)
            );
          }

          // Filter by search query
          if (searchQuery.trim() !== '') {
            const q = searchQuery.toLowerCase();
            blocks = blocks.filter((b) =>
              b.block_id.toLowerCase().includes(q) ||
              b.section_id.toLowerCase().includes(q) ||
              b.activities.some((act) =>
                act.task_id.toLowerCase().includes(q) ||
                act.asset_id.toLowerCase().includes(q) ||
                act.task_type.toLowerCase().includes(q) ||
                act.crew_name?.toLowerCase().includes(q)
              )
            );
          }

          if (blocks.length === 0) return null;

          return (
            <div key={day} className="space-y-4">
              {/* Day Section Header */}
              <div className="flex items-center space-x-3 pb-2 border-b border-slate-800">
                <Calendar className="w-4 h-4 text-blue-400" />
                <h3 className="font-heading font-extrabold text-base text-white">{day}</h3>
                <span className="text-xs text-slate-400 font-medium">
                  ({blocks.length} possession window{blocks.length > 1 ? 's' : ''})
                </span>
              </div>

              {/* Day Blocks Grid */}
              <div className="space-y-4">
                {blocks.map((block) => {
                  const isMultiDept = block.activities.length > 1;

                  return (
                    <div
                      key={block.block_id}
                      className="glass-panel rounded-2xl border border-slate-800/90 overflow-hidden hover:border-slate-700/80 transition-all shadow-md"
                    >
                      {/* Window Header Strip */}
                      <div className="bg-slate-900/90 px-4 py-3 border-b border-slate-800 flex flex-wrap items-center justify-between gap-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-mono font-bold text-sm text-blue-400">
                            {block.window_display}
                          </span>
                          <span className="text-slate-500">•</span>
                          <span className="font-mono text-xs font-semibold text-slate-300">
                            {block.section_id}
                          </span>
                          <span className="text-slate-500">•</span>
                          <span className="text-xs font-medium text-slate-400">
                            Window: {block.block_id} ({block.duration_minutes} min)
                          </span>

                          {/* Window Type Pill */}
                          <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                            {block.window_type}
                          </span>

                          {/* Joint Multi-Department Bundling Badge */}
                          {isMultiDept && (
                            <span className="flex items-center space-x-1 text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                              <Sparkles className="w-3 h-3 text-emerald-400" />
                              <span>Multi-Dept Joint Block (+15 pts)</span>
                            </span>
                          )}
                        </div>

                        {/* Utilization Metric */}
                        <div className="flex items-center space-x-2 text-xs font-mono">
                          <span className="text-slate-400">Window Capacity:</span>
                          <div className="flex items-center space-x-1 font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                            <span>{block.maintenance_time_used}m used</span>
                            <span className="text-slate-500">/</span>
                            <span>{block.utilization_pct}%</span>
                          </div>
                        </div>
                      </div>

                      {/* Window Timeline Structure: Setup -> Activities -> Teardown */}
                      <div className="p-4 space-y-3">
                        {/* 1. Setup Phase */}
                        <div className="flex items-center space-x-3 px-3 py-1.5 rounded-lg bg-amber-500/5 border border-dashed border-amber-500/25 text-xs text-amber-300/80">
                          <span className="font-mono font-bold text-amber-400">
                            {block.setup_phase.start}–{block.setup_phase.end}
                          </span>
                          <span className="text-[11px] font-semibold tracking-wider uppercase px-1.5 py-0.5 rounded bg-amber-500/10 border border-amber-500/20">
                            Setup Buffer ({block.setup_phase.duration_minutes} min)
                          </span>
                          <span className="text-slate-400 truncate">
                            {block.setup_phase.description}
                          </span>
                        </div>

                        {/* 2. Scheduled Maintenance Activities */}
                        <div className="space-y-2.5">
                          {block.activities.map((act, actIdx) => {
                            const deptBadge = getDeptBadge(act.department_id, act.department_name);
                            const prioBadge = getPriorityBadge(act.priority);
                            const m = act.score_metrics || {};

                            return (
                              <React.Fragment key={act.task_id}>
                                <div className="p-3 rounded-xl bg-slate-900/50 border border-slate-800 space-y-2">
                                  {/* Task Title Row */}
                                  <div className="flex flex-wrap items-center justify-between gap-2">
                                    <div className="flex items-center space-x-2">
                                      <span className="font-mono font-bold text-xs text-white">
                                        {act.task_id}
                                      </span>
                                      <span className="text-slate-600">•</span>
                                      <span className="font-semibold text-xs text-slate-200">
                                        {act.task_type}
                                      </span>
                                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${deptBadge.bg} ${deptBadge.text} ${deptBadge.border}`}>
                                        {act.department_name}
                                      </span>
                                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${prioBadge}`}>
                                        Priority {act.priority}
                                      </span>
                                    </div>

                                    {/* Task Time Slot */}
                                    <div className="font-mono text-xs font-bold text-blue-400 flex items-center space-x-1">
                                      <Clock className="w-3.5 h-3.5" />
                                      <span>{act.scheduled_start}–{act.scheduled_end}</span>
                                    </div>
                                  </div>

                                  {/* Task Resource & Asset Row */}
                                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs pt-1">
                                    <div className="flex items-center space-x-1.5">
                                      <Wrench className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                                      <span className="text-slate-400">Asset:</span>
                                      <strong className="text-slate-200 font-mono">{act.asset_id}</strong>
                                      <span className="text-slate-400 truncate">({act.asset_code} @ km {act.asset_location_km})</span>
                                    </div>
                                    <div className="flex items-center space-x-1.5">
                                      <HardHat className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                                      <span className="text-slate-400">Crew:</span>
                                      <strong className="text-slate-200 font-mono">{act.crew_id}</strong>
                                      <span className="text-slate-300 truncate">({act.crew_name})</span>
                                    </div>
                                    <div className="flex items-center space-x-1.5">
                                      <Clock className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                                      <span className="text-slate-400">Duration:</span>
                                      <strong className="text-slate-200">{act.duration_minutes} min</strong>
                                      <span className="text-slate-400">({act.status})</span>
                                    </div>
                                  </div>

                                  {/* Objective Net Value Breakdown Pill */}
                                  <div className="flex flex-wrap items-center justify-between text-[11px] pt-1 border-t border-slate-800/80 text-slate-400">
                                    <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                                      <span>Benefit: <strong className="text-blue-400">+{m.maintenance_benefit}</strong></span>
                                      <span>•</span>
                                      <span>Criticality: <strong className="text-indigo-400">+{m.asset_criticality}</strong></span>
                                      <span>•</span>
                                      <span>Availability: <strong className="text-emerald-400">+{m.asset_availability}</strong></span>
                                      <span>•</span>
                                      <span>Urgency: <strong className="text-cyan-400">+{m.deadline_urgency}</strong></span>
                                      <span>•</span>
                                      <span>Ops Share: <strong className="text-rose-400">-{m.allocated_ops_cost}</strong></span>
                                    </div>
                                    <div className="flex items-center space-x-1 font-bold text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/25">
                                      <span>Net Value:</span>
                                      <span>+{m.net_value} pts</span>
                                    </div>
                                  </div>
                                </div>

                                {/* Inter-task buffer between consecutive activities */}
                                {actIdx < block.activities.length - 1 && (
                                  <div className="flex items-center space-x-2 px-3 py-1 rounded bg-slate-900/60 border border-dashed border-slate-700/60 text-[11px] text-slate-400">
                                    <span className="font-mono text-slate-400 font-semibold">
                                      {act.scheduled_end}–{block.activities[actIdx + 1].scheduled_start}
                                    </span>
                                    <span className="uppercase text-[9px] font-bold px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">
                                      Inter-Task Safety Buffer (5 min)
                                    </span>
                                    <span className="text-slate-500">Crew / Equipment Handover & Track Clearance</span>
                                  </div>
                                )}
                              </React.Fragment>
                            );
                          })}
                        </div>

                        {/* 3. Teardown Phase */}
                        <div className="flex items-center space-x-3 px-3 py-1.5 rounded-lg bg-emerald-500/5 border border-dashed border-emerald-500/25 text-xs text-emerald-300/80">
                          <span className="font-mono font-bold text-emerald-400">
                            {block.teardown_phase.start}–{block.teardown_phase.end}
                          </span>
                          <span className="text-[11px] font-semibold tracking-wider uppercase px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
                            Teardown Buffer ({block.teardown_phase.duration_minutes} min)
                          </span>
                          <span className="text-slate-400 truncate">
                            {block.teardown_phase.description}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
    </div>
  );
}
