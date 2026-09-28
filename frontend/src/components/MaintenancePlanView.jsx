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
  Info
} from 'lucide-react';

export default function MaintenancePlanView({ schedule, onFilterChange }) {
  const [selectedDay, setSelectedDay] = useState('ALL');
  const [selectedSection, setSelectedSection] = useState('ALL');
  const [selectedDepartment, setSelectedDepartment] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

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

  const daysList = Object.keys(schedule);

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
            <option value="ALL">All Sections (SEC01–SEC04)</option>
            <option value="SEC001">SEC001 (0–25 km)</option>
            <option value="SEC002">SEC002 (25–52 km)</option>
            <option value="SEC003">SEC003 (52–78 km)</option>
            <option value="SEC004">SEC004 (78–105 km)</option>
          </select>

          {/* Department Filter */}
          <select
            value={selectedDepartment}
            onChange={(e) => setSelectedDepartment(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg text-xs font-medium text-slate-300 px-2.5 py-1.5 focus:outline-none focus:border-blue-500"
          >
            <option value="ALL">All Departments</option>
            <option value="DEP001">Engineering (P-Way)</option>
            <option value="DEP002">Traction (OHE)</option>
            <option value="DEP003">Signalling & Telecom (S&T)</option>
          </select>
        </div>
      </div>

      {/* Days & Block Windows Layout */}
      {daysList
        .filter((day) => selectedDay === 'ALL' || selectedDay === day)
        .map((dayKey) => {
          const blocks = schedule[dayKey] || [];
          const filteredBlocks = blocks.filter((b) => {
            if (selectedSection !== 'ALL' && b.section_id !== selectedSection) return false;
            if (selectedDepartment !== 'ALL') {
              return b.activities.some((a) => a.department_id === selectedDepartment);
            }
            return true;
          });

          if (filteredBlocks.length === 0) return null;

          return (
            <div key={dayKey} className="space-y-4">
              {/* Day Header */}
              <div className="flex items-center space-x-2 border-b border-slate-800/80 pb-2">
                <Calendar className="w-4 h-4 text-blue-400" />
                <h3 className="font-heading font-extrabold text-base tracking-wide text-white uppercase">
                  {dayKey}
                </h3>
                <span className="text-xs text-slate-400 font-medium">
                  ({filteredBlocks.length} Possession Windows)
                </span>
              </div>

              {/* Block Cards Grid */}
              <div className="space-y-4">
                {filteredBlocks.map((block) => {
                  const isWhiteWindow = !block.affected_trains || block.affected_trains.length === 0;

                  return (
                    <div
                      key={block.block_id}
                      className="glass-panel rounded-2xl border border-slate-800 overflow-hidden transition-all hover:border-slate-700 bg-slate-900/60 shadow-lg"
                    >
                      {/* Block Window Header */}
                      <div className="bg-slate-950/80 px-4 py-3 border-b border-slate-800/80 flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center space-x-3">
                          <span className="px-2.5 py-1 rounded-md bg-blue-500/15 border border-blue-500/30 text-blue-400 font-mono font-bold text-xs">
                            {block.window_display}
                          </span>
                          <span className="font-mono text-xs font-semibold text-slate-300">
                            {block.block_id}
                          </span>
                          <span className="text-xs text-slate-400 flex items-center space-x-1">
                            <MapPin className="w-3.5 h-3.5 text-slate-500" />
                            <span>Section <strong className="text-slate-200">{block.section_id}</strong></span>
                          </span>
                          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700 font-medium">
                            {block.window_type}
                          </span>
                        </div>

                        {/* Traffic Impact Status */}
                        <div className="flex items-center space-x-2">
                          <span
                            className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${
                              isWhiteWindow
                                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                                : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                            }`}
                          >
                            {isWhiteWindow
                              ? 'Zero Train Disruption (White Window)'
                              : `Disrupts ${block.affected_trains.length} Trains (Ops Cost: ${block.operations_cost} pts)`}
                          </span>
                          <span className="text-xs text-slate-400 font-mono">
                            {block.maintenance_time_used}/{block.duration_minutes}m ({block.utilization_pct}%)
                          </span>
                        </div>
                      </div>

                      {/* Intra-Window Timeline Layout */}
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

                        {/* 2. Tasks Inside Block Window */}
                        <div className="space-y-2.5 pl-2 border-l-2 border-blue-500/30">
                          {block.activities.map((act, actIdx) => {
                            const deptBadge = getDeptBadge(act.department_id, act.department_name);
                            const priBadge = getPriorityBadge(act.priority);
                            const m = act.metrics;

                            return (
                              <React.Fragment key={act.task_id}>
                                <div className="glass-panel p-3.5 rounded-xl border border-slate-800 bg-slate-950/70 hover:border-slate-700 transition-all">
                                  <div className="flex flex-wrap items-start justify-between gap-2 mb-2">
                                    {/* Task Time & ID */}
                                    <div className="flex items-center space-x-2.5">
                                      <span className="font-mono font-bold text-xs text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/25">
                                        {act.scheduled_start}–{act.scheduled_end}
                                      </span>
                                      <span className="font-mono font-bold text-xs text-white">
                                        {act.task_id}
                                      </span>
                                      <span className="text-xs font-semibold text-slate-200">
                                        {act.task_type}
                                      </span>
                                    </div>

                                    {/* Badges */}
                                    <div className="flex items-center space-x-1.5">
                                      <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full border ${priBadge}`}>
                                        {act.priority}
                                      </span>
                                      <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full border ${deptBadge.bg} ${deptBadge.text} ${deptBadge.border}`}>
                                        {act.department_name}
                                      </span>
                                    </div>
                                  </div>

                                  {/* Asset & Crew Details */}
                                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 text-xs text-slate-300 mb-3 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/80">
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
