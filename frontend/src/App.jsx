import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import KPICards from './components/KPICards';
import MaintenancePlanView from './components/MaintenancePlanView';
import NetworkMapView from './components/NetworkMapView';
import AssetView from './components/AssetView';
import ConflictView from './components/ConflictView';
import ScenarioSandbox from './components/ScenarioSandbox';
import AnalyticsView from './components/AnalyticsView';
import BenchmarkView from './components/BenchmarkView';
import { AuthProvider, useAuth } from './context/AuthContext';
import { apiService } from './services/api';
import { 
  Sparkles, 
  RefreshCw, 
  BarChart2, 
  Calendar, 
  Layers, 
  AlertTriangle, 
  TrainTrack,
  Award,
  KeyRound,
  ShieldCheck,
  UserCheck
} from 'lucide-react';

function DashboardContent() {
  const { currentUser, notification, isController, isPWay, isOHE, isSafety } = useAuth();
  const [horizon, setHorizon] = useState('weekly');
  const [activeTab, setActiveTab] = useState('benchmark');
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [systemStatus, setSystemStatus] = useState(null);

  // Core Data
  const [kpis, setKpis] = useState(null);
  const [scheduleData, setScheduleData] = useState(null);
  const [assets, setAssets] = useState([]);
  const [conflicts, setConflicts] = useState(null);
  const [blocks, setBlocks] = useState([]);

  // Fetch initial data
  const fetchData = async (currentHorizon = horizon) => {
    try {
      // 1. Fetch system status
      const statusRes = await apiService.getStatus();
      setSystemStatus(statusRes);

      // 2. Fetch KPIs
      const kpiRes = await apiService.getKPI();
      if (kpiRes && kpiRes.kpis) {
        setKpis(kpiRes.kpis);
      }

      // 3. Fetch schedule
      const schedRes = await apiService.getSchedule();
      if (schedRes && schedRes.schedule) {
        setScheduleData(schedRes.schedule);
        if (schedRes.summary) setKpis(schedRes.summary);
      }

      // 4. Fetch assets
      const assetsRes = await apiService.getAssets();
      if (assetsRes && assetsRes.assets) {
        setAssets(assetsRes.assets);
      }

      // 5. Fetch conflicts
      const conflictsRes = await apiService.getConflicts();
      if (conflictsRes) {
        setConflicts(conflictsRes);
      }

      // 6. Fetch blocks
      const blocksRes = await apiService.getBlocks();
      if (blocksRes && blocksRes.blocks) {
        setBlocks(blocksRes.blocks);
      }
    } catch (err) {
      console.warn('Backend loading warning:', err);
    }
  };

  useEffect(() => {
    fetchData(horizon);
  }, [horizon]);

  // Handle Horizon Change
  const handleHorizonChange = async (newHorizon) => {
    setHorizon(newHorizon);
    setIsOptimizing(true);
    try {
      const res = await apiService.optimizeSchedule(newHorizon);
      if (res && res.schedule) {
        setScheduleData(res.schedule);
        setKpis(res.summary);
      }
      await fetchData(newHorizon);
    } catch (err) {
      console.error('Failed to optimize for horizon', err);
    } finally {
      setIsOptimizing(false);
    }
  };

  // Handle Live Re-Optimize
  const handleOptimize = async () => {
    setIsOptimizing(true);
    try {
      const res = await apiService.optimizeSchedule(horizon);
      if (res && res.schedule) {
        setScheduleData(res.schedule);
        setKpis(res.summary);
      }
      await fetchData(horizon);
    } catch (err) {
      console.error('Optimization failed', err);
    } finally {
      setIsOptimizing(false);
    }
  };

  // Handle Failure Simulation from Asset Card
  const handleSimulateFailure = (assetId) => {
    setActiveTab('scenarios');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navigation with RBAC */}
      <Navbar
        horizon={horizon}
        onHorizonChange={handleHorizonChange}
        onOptimize={handleOptimize}
        isOptimizing={isOptimizing}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        status={systemStatus}
        onTaskCreated={() => fetchData(horizon)}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Role Context Bar if not Controller */}
        {!isController && currentUser && (
          <div className="mb-4 p-2.5 rounded-xl border border-amber-500/30 bg-amber-500/10 text-amber-300 flex items-center justify-between text-xs animate-in fade-in duration-200">
            <div className="flex items-center space-x-2">
              <UserCheck className="w-4 h-4 text-amber-400 shrink-0" />
              <span>
                Active Session: <strong>{currentUser.full_name}</strong> ({currentUser.designation}). You can file departmental block requests; global timetable re-optimization is restricted to the Section Controller.
              </span>
            </div>
            <span className="font-mono text-[10px] bg-amber-500/20 px-2 py-0.5 rounded border border-amber-500/30 font-bold uppercase">
              {currentUser.role.replace('_ENGINEER', '').replace('_AUDITOR', '')} MODE
            </span>
          </div>
        )}

        {/* KPI Overview Strip */}
        <KPICards
          kpis={kpis}
          assets={assets}
          conflicts={conflicts}
        />

        {/* View Switcher Bar & Analytics Tab Link */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-6">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Active View:</span>
            <span className="font-heading font-extrabold text-base text-white capitalize">
              {activeTab === 'benchmark' && 'Controlled Synthetic Benchmark: Before vs After Optimization'}
              {activeTab === 'plan' && 'Maintenance Master Timetable'}
              {activeTab === 'map' && 'GIS Corridor & Asset Topology Map'}
              {activeTab === 'assets' && 'Asset Health & Condition Registry'}
              {activeTab === 'conflicts' && 'Train Traffic Conflicts & Delay Analysis'}
              {activeTab === 'scenarios' && 'Real-Time What-If Scenario Sandbox'}
              {activeTab === 'analytics' && 'Operational Analytics & Charts'}
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setActiveTab('benchmark')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border ${
                activeTab === 'benchmark'
                  ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              <Award className="w-3.5 h-3.5" />
              <span>Before vs After</span>
            </button>
            <button
              onClick={() => setActiveTab('analytics')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border ${
                activeTab === 'analytics'
                  ? 'bg-blue-600/20 text-blue-400 border-blue-500/40'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              <BarChart2 className="w-3.5 h-3.5" />
              <span>Analytics Charts</span>
            </button>
          </div>
        </div>

        {/* Dynamic Tab Views */}
        <div>
          {activeTab === 'benchmark' && (
            <BenchmarkView horizon={horizon} />
          )}

          {activeTab === 'plan' && (
            <MaintenancePlanView schedule={scheduleData} />
          )}

          {activeTab === 'map' && (
            <NetworkMapView
              assets={assets}
              blocks={blocks}
              schedule={scheduleData}
            />
          )}

          {activeTab === 'assets' && (
            <AssetView
              assets={assets}
              schedule={scheduleData}
              onSimulateFailure={handleSimulateFailure}
            />
          )}

          {activeTab === 'conflicts' && (
            <ConflictView conflicts={conflicts} />
          )}

          {activeTab === 'scenarios' && (
            <ScenarioSandbox horizon={horizon} />
          )}

          {activeTab === 'analytics' && (
            <AnalyticsView
              kpis={kpis}
              assets={assets}
              schedule={scheduleData}
            />
          )}
        </div>
      </main>

      {/* Floating Role Switch Notification Toast */}
      {notification && (
        <div className="fixed bottom-6 right-6 z-50 glass-panel border border-blue-500/40 bg-slate-950/95 p-4 rounded-xl shadow-2xl flex items-start space-x-3 max-w-md animate-in slide-in-from-bottom duration-200">
          <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400 shrink-0">
            <KeyRound className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-white">{notification.title}</h4>
            <p className="text-[11px] text-slate-300 mt-0.5 leading-snug">{notification.message}</p>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/80 py-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-wrap items-center justify-between gap-2">
          <span>OptRail-AI • Smart India Hackathon (SIH) Prototype • Google OR-Tools CP-SAT</span>
          <span>Northern Railway Mainline Corridor SEC001–SEC004 (105 km)</span>
        </div>
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <DashboardContent />
    </AuthProvider>
  );
}
