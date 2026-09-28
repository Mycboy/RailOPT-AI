import React, { useState } from 'react';
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
  ShieldAlert 
} from 'lucide-react';

export default function RequestTaskModal({ isOpen, onClose, onTaskCreated }) {
  const { currentUser, isPWay, isOHE, isController } = useAuth();

  const defaultDept = isPWay ? 'DEP001' : (isOHE ? 'DEP002' : 'DEP001');

  const [assetId, setAssetId] = useState('AST001');
  const [departmentId, setDepartmentId] = useState(defaultDept);
  const [taskType, setTaskType] = useState(
    isPWay ? 'Ultrasonic Flaw Detection (USFD)' : (isOHE ? 'Catenary Contact Wire Inspection' : 'Routine Maintenance')
  );
  const [durationMinutes, setDurationMinutes] = useState(60);
  const [priority, setPriority] = useState(2);
  const [deadlineHours, setDeadlineHours] = useState(48);
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successResult, setSuccessResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  if (!isOpen) return null;

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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
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
                Task <strong className="font-mono">{successResult.task.task_id}</strong> on{' '}
                <strong className="font-mono">{successResult.task.asset_id}</strong> is now registered in the division backlog.
              </p>
              <div className="mt-2 text-[11px] bg-slate-950/60 p-2 rounded border border-emerald-500/20 font-mono">
                Assigned Role: {successResult.task.required_crew_role} • Submitter: {successResult.task.submitted_by}
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
            <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/70 border border-slate-800 text-[11px]">
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

            {/* Department Selection (Locked based on RBAC) */}
            <div>
              <label className="block text-[11px] font-bold text-slate-300 mb-1">
                Department Division
              </label>
              <select
                value={departmentId}
                onChange={(e) => setDepartmentId(e.target.value)}
                disabled={!isController}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 disabled:opacity-60 disabled:cursor-not-allowed focus:border-blue-500 focus:outline-none"
              >
                <option value="DEP001">DEP001 • Civil Engineering / Permanent Way (P-Way)</option>
                <option value="DEP002">DEP002 • Electrical TRD / Overhead Equipment (OHE)</option>
                <option value="DEP003">DEP003 • Signaling & Telecommunication (S&T)</option>
              </select>
              {!isController && (
                <p className="text-[10px] text-slate-500 mt-1">
                  Locked by RBAC to your assigned department credentials.
                </p>
              )}
            </div>

            {/* Target Asset */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-bold text-slate-300 mb-1">
                  Target Asset ID
                </label>
                <select
                  value={assetId}
                  onChange={(e) => setAssetId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 focus:border-blue-500 focus:outline-none"
                >
                  <option value="AST001">AST001 • Point Machine 101A (SEC001)</option>
                  <option value="AST002">AST002 • Track Section KM 12-18 (SEC001)</option>
                  <option value="AST003">AST003 • Track Circuit TC-101 (SEC001)</option>
                  <option value="AST005">AST005 • OHE Catenary Wire (SEC002)</option>
                  <option value="AST006">AST006 • Traction Transformer T-2 (SEC002)</option>
                  <option value="AST008">AST008 • Track Section KM 45-52 (SEC003)</option>
                  <option value="AST009">AST009 • OHE Neutral Section (SEC003)</option>
                  <option value="AST011">AST011 • Track Section KM 80-88 (SEC004)</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-slate-300 mb-1">
                  Requested Duration
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

            {/* Task Type */}
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
