import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  ShieldCheck, 
  ChevronDown, 
  Check, 
  User, 
  TrainTrack, 
  Zap, 
  Radio, 
  Lock, 
  KeyRound,
  BadgeAlert
} from 'lucide-react';

export default function RoleSwitcher() {
  const { currentUser, demoUsers, switchRole, isController } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (!currentUser) return null;

  const getRoleIcon = (role) => {
    switch (role) {
      case 'CONTROLLER':
        return <TrainTrack className="w-3.5 h-3.5 text-blue-400" />;
      case 'PWAY_ENGINEER':
        return <Radio className="w-3.5 h-3.5 text-amber-400" />;
      case 'OHE_ENGINEER':
        return <Zap className="w-3.5 h-3.5 text-cyan-400" />;
      case 'SAFETY_AUDITOR':
        return <ShieldCheck className="w-3.5 h-3.5 text-purple-400" />;
      default:
        return <User className="w-3.5 h-3.5 text-slate-400" />;
    }
  };

  const getRoleBadge = (role) => {
    switch (role) {
      case 'CONTROLLER':
        return { label: 'DOM / Traffic Controller', color: 'bg-blue-500/10 text-blue-400 border-blue-500/25' };
      case 'PWAY_ENGINEER':
        return { label: 'DEN / Track P-Way', color: 'bg-amber-500/10 text-amber-400 border-amber-500/25' };
      case 'OHE_ENGINEER':
        return { label: 'DEE / Electrical TRD', color: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/25' };
      case 'SAFETY_AUDITOR':
        return { label: 'CRS / Safety Auditor', color: 'bg-purple-500/10 text-purple-400 border-purple-500/25' };
      default:
        return { label: 'Railway Staff', color: 'bg-slate-500/10 text-slate-400 border-slate-500/25' };
    }
  };

  const badgeInfo = getRoleBadge(currentUser.role);

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Active Persona Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2.5 p-1.5 pr-2.5 rounded-xl border border-slate-800 bg-slate-900/90 hover:bg-slate-800/80 transition-all text-left group"
        title="Switch Indian Railways Persona / RBAC Role"
      >
        {/* Avatar with Initials */}
        <div className={`w-8 h-8 rounded-lg bg-gradient-to-tr ${currentUser.avatar_color || 'from-blue-600 to-indigo-600'} p-0.5 shadow-md`}>
          <div className="w-full h-full bg-slate-950 rounded-[6px] flex items-center justify-center font-bold text-xs text-white">
            {currentUser.full_name
              .split(' ')
              .filter(n => !n.includes('(') && !n.includes('/') && !n.includes('.'))
              .slice(0, 2)
              .map(n => n[0])
              .join('') || 'IR'}
          </div>
        </div>

        {/* User Info & Role Tag */}
        <div className="hidden sm:block text-left">
          <div className="flex items-center space-x-1.5">
            <span className="text-xs font-bold text-white group-hover:text-blue-300 transition-colors">
              {currentUser.full_name.split(',')[0]}
            </span>
            <span className={`text-[9px] uppercase font-mono font-bold px-1.5 py-0.2 rounded border ${badgeInfo.color}`}>
              {currentUser.role === 'CONTROLLER' ? 'CTRL' : currentUser.role.replace('_ENGINEER', '').replace('_AUDITOR', '')}
            </span>
          </div>
          <p className="text-[10px] text-slate-400 truncate max-w-[130px]">
            {currentUser.designation.split('(')[0]}
          </p>
        </div>

        <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform ${isOpen ? 'rotate-180 text-white' : ''}`} />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 glass-panel rounded-2xl border border-slate-800 bg-slate-950/95 shadow-2xl p-2 z-50 animate-in fade-in zoom-in-95 duration-100">
          <div className="px-3 py-2 border-b border-slate-800/80 mb-1">
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
                Indian Railways RBAC
              </span>
              <span className="text-[10px] font-mono text-emerald-400 flex items-center space-x-1">
                <KeyRound className="w-3 h-3 inline mr-1" />
                JWT Active
              </span>
            </div>
            <p className="text-xs text-slate-300 font-medium mt-0.5">
              Select persona to test divisional authority:
            </p>
          </div>

          <div className="space-y-1">
            {demoUsers.map((persona) => {
              const isSelected = currentUser.username === persona.username;
              const pBadge = getRoleBadge(persona.role);
              const Icon = getRoleIcon(persona.role);

              return (
                <button
                  key={persona.username}
                  onClick={() => {
                    switchRole(persona.username);
                    setIsOpen(false);
                  }}
                  className={`w-full flex items-start space-x-3 p-2.5 rounded-xl text-left transition-all border ${
                    isSelected
                      ? 'bg-blue-600/15 border-blue-500/40 shadow-sm'
                      : 'border-transparent hover:bg-slate-900 hover:border-slate-800'
                  }`}
                >
                  <div className={`w-8 h-8 rounded-lg bg-gradient-to-tr ${persona.avatar_color} p-0.5 shrink-0 mt-0.5`}>
                    <div className="w-full h-full bg-slate-950 rounded-[6px] flex items-center justify-center font-bold text-xs text-white">
                      {persona.full_name
                        .split(' ')
                        .filter(n => !n.includes('(') && !n.includes('/') && !n.includes('.'))
                        .slice(0, 2)
                        .map(n => n[0])
                        .join('')}
                    </div>
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white truncate">
                        {persona.full_name}
                      </span>
                      {isSelected && <Check className="w-3.5 h-3.5 text-blue-400 shrink-0 ml-1" />}
                    </div>

                    <div className="flex items-center space-x-1.5 mt-0.5">
                      <span className={`text-[9px] font-bold px-1.5 py-0.2 rounded border ${pBadge.color}`}>
                        {pBadge.label}
                      </span>
                      <span className="text-[10px] text-slate-500 font-mono">
                        {persona.badge_id}
                      </span>
                    </div>

                    <p className="text-[10px] text-slate-400 mt-1 leading-tight">
                      {persona.can_optimize 
                        ? 'Full Controller Authority: Re-Optimize, Approve/Reject Memos, What-If Sandbox'
                        : `Departmental Mode: Submit ${persona.department.split('(')[0]} requests; Global solve locked.`}
                    </p>
                  </div>
                </button>
              );
            })}
          </div>

          <div className="mt-2 pt-2 border-t border-slate-800/80 px-2 py-1 flex items-center justify-between text-[10px] text-slate-500">
            <span>Auth: PyJWT + bcrypt</span>
            <span>Division: Delhi / NR</span>
          </div>
        </div>
      )}
    </div>
  );
}
