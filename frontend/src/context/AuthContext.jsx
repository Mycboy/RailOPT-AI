import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiService } from '../services/api';

const DEFAULT_DEMO_USERS = [
  {
    username: 'controller',
    full_name: 'Rajesh Sharma',
    designation: 'Chief Section Controller (Sr. DOM)',
    department: 'Traffic Operations (DOM)',
    division: 'Delhi Division / Northern Railway',
    badge_id: 'IR-DOM-0442',
    role: 'CONTROLLER',
    avatar_color: 'from-blue-600 to-indigo-600',
    can_optimize: true,
    can_approve_blocks: true,
    permissions: ['optimize:run', 'schedule:approve', 'schedule:reject', 'scenario:run', 'task:create', 'task:view', 'asset:view', 'conflict:view', 'benchmark:view']
  },
  {
    username: 'pway_engineer',
    full_name: 'Arun Verma',
    designation: 'Sr. Section Engineer / Permanent Way (Civil)',
    department: 'Civil Engineering (P-Way)',
    division: 'Ghaziabad Sub-Division',
    badge_id: 'IR-DEN-1108',
    role: 'PWAY_ENGINEER',
    avatar_color: 'from-amber-600 to-orange-600',
    can_optimize: false,
    can_approve_blocks: false,
    permissions: ['scenario:run', 'task:create', 'task:view', 'asset:view', 'schedule:view', 'benchmark:view']
  },
  {
    username: 'ohe_engineer',
    full_name: 'Priya Nair',
    designation: 'Sr. Section Engineer / Traction & OHE (Electrical)',
    department: 'Electrical TRD (DEE)',
    division: 'Aligarh Sub-Division',
    badge_id: 'IR-DEE-3391',
    role: 'OHE_ENGINEER',
    avatar_color: 'from-cyan-600 to-blue-500',
    can_optimize: false,
    can_approve_blocks: false,
    permissions: ['scenario:run', 'task:create', 'task:view', 'asset:view', 'schedule:view', 'benchmark:view']
  },
  {
    username: 'safety_auditor',
    full_name: 'V. K. Meena',
    designation: 'Divisional Safety Officer (CRS Inspectorate)',
    department: 'Safety & Inspection Directorate',
    division: 'Northern Railway Zone',
    badge_id: 'IR-CRS-0019',
    role: 'SAFETY_AUDITOR',
    avatar_color: 'from-purple-600 to-pink-600',
    can_optimize: false,
    can_approve_blocks: false,
    permissions: ['scenario:run', 'safety:audit', 'conflict:view', 'schedule:view', 'asset:view', 'benchmark:view']
  }
];

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [demoUsers, setDemoUsers] = useState(DEFAULT_DEMO_USERS);
  const [currentUser, setCurrentUser] = useState(() => {
    const savedUsername = localStorage.getItem('optrail_active_username') || 'controller';
    return DEFAULT_DEMO_USERS.find(u => u.username === savedUsername) || DEFAULT_DEMO_USERS[0];
  });
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  // Initialize demo personas from backend and update tokens
  useEffect(() => {
    let isMounted = true;
    const initAuth = async () => {
      try {
        const res = await apiService.getDemoUsers();
        if (isMounted && res && res.demo_users && res.demo_users.length > 0) {
          setDemoUsers(res.demo_users);
          
          const savedUsername = localStorage.getItem('optrail_active_username') || 'controller';
          const matched = res.demo_users.find(u => u.username === savedUsername) || res.demo_users[0];
          
          setCurrentUser(matched);
          if (matched.token) {
            localStorage.setItem('optrail_jwt_token', matched.token);
            localStorage.setItem('optrail_active_username', matched.username);
          }
        }
      } catch (err) {
        console.warn('Backend personas sync pending; using offline local personas', err);
      }
    };

    initAuth();
    return () => { isMounted = false; };
  }, []);

  const switchRole = async (targetUsername) => {
    // 1. Instantly switch locally so UI is immediately responsive and never stuck
    const targetUser = demoUsers.find(u => u.username === targetUsername) || DEFAULT_DEMO_USERS.find(u => u.username === targetUsername);
    if (targetUser) {
      setCurrentUser(targetUser);
      localStorage.setItem('optrail_active_username', targetUsername);
      if (targetUser.token) {
        localStorage.setItem('optrail_jwt_token', targetUser.token);
      }
      
      setNotification({
        type: 'info',
        title: `Role Switched: ${targetUser.designation}`,
        message: targetUser.can_optimize 
          ? 'Full Section Controller privileges active. CP-SAT timetable re-optimization enabled.'
          : `Departmental mode active (${targetUser.department}). Block memo requests enabled.`
      });
      setTimeout(() => setNotification(null), 4500);
    }

    // 2. Sync with backend API to retrieve latest signed JWT token
    try {
      const res = await apiService.switchRole(targetUsername);
      if (res && res.user) {
        setCurrentUser(res.user);
        if (res.access_token) {
          localStorage.setItem('optrail_jwt_token', res.access_token);
        }
        return res.user;
      }
    } catch (err) {
      console.warn('Background switch-role sync deferred (cloud server spinning up)', err);
    }
  };

  const isController = currentUser?.role === 'CONTROLLER';
  const isPWay = currentUser?.role === 'PWAY_ENGINEER';
  const isOHE = currentUser?.role === 'OHE_ENGINEER';
  const isSafety = currentUser?.role === 'SAFETY_AUDITOR';

  return (
    <AuthContext.Provider
      value={{
        currentUser,
        demoUsers,
        loading,
        switchRole,
        notification,
        setNotification,
        isController,
        isPWay,
        isOHE,
        isSafety
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
