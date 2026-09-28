import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiService } from '../services/api';
import { 
  PlusCircle, 
  X, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  Layers, 
  HardHat, 
  ShieldAlert,
  Zap,
  TrainTrack,
  Radio
} from 'lucide-react';

const DEPARTMENT_CONFIG = {
  DEP001: {
    name: 'Civil Engineering / Permanent Way (P-Way)',
    shortName: 'Track / P-Way',
    icon: TrainTrack,
    color: 'text-amber-400 border-amber-500/30 bg-amber-500/10',
    defaultAsset: 'AST001',
    defaultTask: 'Ultrasonic Flaw Detection (USFD)',
    assets: [
      { id: 'AST001', label: 'AST001 • Point Machine 101A (SEC001 - Turnout Switch)' },
      { id: 'AST002', label: 'AST002 • Track Section KM 12-18 (SEC001 - Mainline Rails)' },
      { id: 'AST008', label: 'AST008 • Track Section KM 45-52 (SEC003 - Ballast Cushion)' },
      { id: 'AST011', label: 'AST011 • Track Section KM 80-88 (SEC004 - Thermite Welds)' },
    ],
    taskSuggestions: [
      'Ultrasonic Flaw Detection (USFD)',
      'Track Tamping (CSM Machine)',
      'Deep Ballast Cleaning (BCM)',
      'Turnout Tongue Rail Renewal'
    ]
  },
  DEP002: {
    name: 'Electrical TRD / Overhead Equipment (OHE)',
    shortName: 'Electrical / OHE',
    icon: Zap,
    color: 'text-cyan-400 border-cyan-500/30 bg-cyan-500/10',
    defaultAsset: 'AST005',
    defaultTask: 'Catenary Contact Wire Inspection',
    assets: [
      { id: 'AST005', label: 'AST005 • OHE Catenary Wire (SEC002 - 25kV Traction Line)' },
      { id: 'AST006', label: 'AST006 • Traction Transformer T-2 (SEC002 - Substation)' },
      { id: 'AST009', label: 'AST009 • OHE Neutral Section (SEC003 - Phase Break)' },
      { id: 'AST012', label: 'AST012 • 25kV Vacuum Circuit Breaker (SEC004 - Feeder)' },
    ],
    taskSuggestions: [
      'Catenary Contact Wire Inspection',
      'Neutral Section Insulator Servicing',
      'Cantilever & Dropper Calibration',
      'Isolator Switch Overhaul'
    ]
  },
  DEP003: {
    name: 'Signaling & Telecommunication (S&T)',
    shortName: 'Signaling / S&T',
    icon: Radio,
    color: 'text-purple-400 border-purple-500/30 bg-purple-500/10',
    defaultAsset: 'AST003',
    defaultTask: 'Audio Frequency Track Circuit Calibration',
    assets: [
      { id: 'AST003', label: 'AST003 • Track Circuit TC-101 (SEC001 - Audio Frequency)' },
      { id: 'AST004', label: 'AST004 • Electronic Interlocking EI-GZB (SEC002 - Cabin)' },
      { id: 'AST007', label: 'AST007 • Relay Interlocking Room (SEC003 - Logic Relays)' },
      { id: 'AST010', label: 'AST010 • Digital Axle Counter DAC-04 (SEC004 - Detection)' },
    ],
    taskSuggestions: [
      'Audio Frequency Track Circuit Calibration',
      'Point Machine Electrical Timing Test',
      'Digital Axle Counter Sensor Tuning',
      'LED Signal Aspect Voltage Measurement'
    ]
  }
};

export default function RequestTaskModal({ isOpen, onClose, onTaskCreated }) {
  const { currentUser, isPWay, isOHE, isController } = useAuth();

  const [departmentId, setDepartmentId] = useState('DEP001');
  const [assetId, setAssetId] = useState('AST001');
  const [taskType, setTaskType] = useState('Ultrasonic Flaw Detection (USFD)');
  const [durationMinutes, setDurationMinutes] = useState(60);
  const [priority, setPriority] = useState(2);
  const [deadlineHours, setDeadlineHours] = useState(48);
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successResult, setSuccessResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  // Synchronize department and asset choices whenever active user or modal open state changes
  useEffect(() => {
    if (!isOpen) return;

    let targetDept = 'DEP001';
    if (isPWay) {
      targetDept = 'DEP001';
    } else if (isOHE) {
      targetDept = 'DEP002';
    } else {
      // Controller or safety: retain current or default to DEP001
      targetDept = departmentId || 'DEP001';
    }

    setDepartmentId(targetDept);
    const config = DEPARTMENT_CONFIG[targetDept];
    if (config) {
      setAssetId(config.defaultAsset);
      setTaskType(config.defaultTask);
    }
    setSuccessResult(null);
    setErrorMsg(null);
  }, [currentUser?.username, currentUser?.role, isPWay, isOHE, isOpen]);

  if (!isOpen) return null;

  const currentConfig = DEPARTMENT_CONFIG[departmentId] || DEPARTMENT_CONFIG.DEP001;

  const handleDepartmentChange = (newDept) => {
    setDepartmentId(newDept);
    const config = DEPARTMENT_CONFIG[newDept];
    if (config) {
      setAssetId(config.defaultAsset);
      setTaskType(config.defaultTask);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const payload = {
        asset_id: assetId,
        task_type: taskType,
        department_id: departmentId,
        duration_minutes: Number(durationMinutes),
        priority: Number(priority),
        deadline_hours: Number(deadlineHours),
        description: description || `Possession memo filed by ${currentUser.full_name}`
      };

      const res = await apiService.createTask(payload);
      if (res && res.task) {
        setSuccessResult(res);
        if (onTaskCreated) onTaskCreated(res.task);
      }
    } catch (err) {
      const detail = err.response?.data?.detail || 'Failed to submit maintenance task.';
      setErrorMsg(detail);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="w-full max-w-lg glass-panel rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl p-6 relative">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
              <PlusCircle className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-heading font-extrabold text-base text-white">
                Submit Maintenance Block Request
              </h3>
              <p className="text-[11px] text-slate-400">
                Divisional Possession Memo & Corridor Requisition
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Success Banner */}
        {successResult ? (
          <div className="space-y-4 py-3">
            <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
              <div className="flex items-center space-x-2 mb-1">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <span className="font-bold text-sm">Request Queued Successfully!</span>
              </div>
              <p className="text-xs text-emerald-200/80">
                Requisition <strong className="font-mono">{successResult.task.task_id}</strong> on{' '}
                <strong className="font-mono">{successResult.task.asset_id}</strong> is now registered in the division backlog.
              </p>
              <div className="mt-2 text-[11px] bg-slate-950/60 p-2.5 rounded-lg border border-emerald-500/20 font-mono space-y-1">
                <div>Activity: {successResult.task.task_type}</div>
                <div>Crew Role: {successResult.task.required_crew_role} • Submitter: {successResult.task.submitted_by}</div>
              </div>
            </div>

            <div className="flex justify-end space-x-2">
              <button
                onClick={() => {
                  setSuccessResult(null);
                  onClose();
                }}
                className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-md transition-all"
              >
                Close & View Backlog
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 text-xs">
            {/* Submitter Credentials Strip */}
            <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-[11px]">
              <div>
                <span className="text-slate-500">Applicant: </span>
                <span className="font-bold text-slate-200">{currentUser.full_name}</span>
              </div>
              <div className="flex items-center space-x-1.5 font-mono">
                <span className="px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 text-[10px]">
                  {currentUser.badge_id}
                </span>
                <span className="text-slate-400 font-sans">({currentUser.department.split('(')[0]})</span>
              </div>
            </div>

            {errorMsg && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-start space-x-2">
                <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <span className="text-xs">{errorMsg}</span>
              </div>
            )}

            {/* Department Selection (Dynamic for Controller, Auto-Assigned for Engineers) */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-[11px] font-bold text-slate-300">
                  Target Department
                </label>
                {!isController && (
                  <span className="text-[10px] text-amber-400 font-medium">
                    Locked to your department credentials (RBAC)
                  </span>
                )}
              </div>

              {isController ? (
                <select
                  value={departmentId}
                  onChange={(e) => handleDepartmentChange(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:border-blue-500 focus:outline-none"
                >
                  <option value="DEP001">DEP001 • Civil Engineering / Permanent Way (P-Way)</option>
                  <option value="DEP002">DEP002 • Electrical TRD / Overhead Equipment (OHE)</option>
                  <option value="DEP003">DEP003 • Signaling & Telecommunication (S&T)</option>
                </select>
              ) : (
                <div className={`p-2.5 rounded-lg border flex items-center justify-between ${currentConfig.color}`}>
                  <span className="font-bold text-xs">{currentConfig.name}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-slate-950/60 font-mono">
                    {departmentId}
                  </span>
                </div>
              )}
            </div>

            {/* Target Asset (Filtered by Department) */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-bold text-slate-300 mb-1">
                  Target Asset ({currentConfig.shortName})
                </label>
                <select
                  value={assetId}
                  onChange={(e) => setAssetId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:border-blue-500 focus:outline-none"
                >
                  {currentConfig.assets.map((asset) => (
                    <option key={asset.id} value={asset.id}>
                      {asset.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-300 mb-1">
                  Requested Possession
                </label>
                <select
                  value={durationMinutes}
                  onChange={(e) => setDurationMinutes(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:border-blue-500 focus:outline-none"
                >
                  <option value="30">30 minutes</option>
                  <option value="45">45 minutes</option>
                  <option value="60">60 minutes (1 hour)</option>
                  <option value="90">90 minutes (1.5 hours)</option>
                  <option value="120">120 minutes (2 hours)</option>
                  <option value="150">150 minutes (2.5 hours)</option>
                </select>
              </div>
            </div>

            {/* Task Type & Quick Suggestions */}
            <div>
              <label className="block text-[11px] font-bold text-slate-300 mb-1">
                Maintenance Activity
              </label>
              <input
                type="text"
                value={taskType}
                onChange={(e) => setTaskType(e.target.value)}
                placeholder="e.g. Ultrasonic Flaw Testing (USFD), Catenary Contact Sag Renewal"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:border-blue-500 focus:outline-none"
                required
              />

              {/* Quick suggestion chips */}
              <div className="flex flex-wrap gap-1.5 mt-2">
                {currentConfig.taskSuggestions.map((sug) => (
                  <button
                    key={sug}
                    type="button"
                    onClick={() => setTaskType(sug)}
                    className={`text-[10px] px-2 py-0.5 rounded-full border transition-all ${
                      taskType === sug
                        ? 'bg-blue-600/30 text-blue-300 border-blue-500/50'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {sug}
                  </button>
                ))}
              </div>
            </div>

            {/* Priority & Deadline */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-bold text-slate-300 mb-1">
                  Urgency / Priority
                </label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:border-blue-500 focus:outline-none"
                >
                  <option value="1">P1 • Critical (Immediate Track Hazard)</option>
                  <option value="2">P2 • High (Routine Safety Margin)</option>
                  <option value="3">P3 • Medium (Scheduled Inspection)</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-300 mb-1">
                  Execution Deadline
                </label>
                <select
                  value={deadlineHours}
                  onChange={(e) => setDeadlineHours(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:border-blue-500 focus:outline-none"
                >
                  <option value="24">Within 24 Hours</option>
                  <option value="48">Within 48 Hours</option>
                  <option value="72">Within 72 Hours (3 Days)</option>
                  <option value="168">Within 7 Days (Weekly Window)</option>
                </select>
              </div>
            </div>

            {/* Submit Buttons */}
            <div className="flex items-center justify-end space-x-2 pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold transition-all"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-2 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold shadow-md shadow-blue-500/25 active:scale-95 transition-all flex items-center space-x-1.5"
              >
                <PlusCircle className="w-4 h-4" />
                <span>{isSubmitting ? 'Submitting Requisition...' : 'Submit Requisition Memo'}</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
