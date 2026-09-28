import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiService } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [demoUsers, setDemoUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [notification, setNotification] = useState(null);

  // Initialize demo personas and restore or set default persona (Chief Section Controller)
  useEffect(() => {
    const initAuth = async () => {
      try {
        const res = await apiService.getDemoUsers();
        if (res && res.demo_users) {
          setDemoUsers(res.demo_users);
          
          // Check if user already had a saved persona
          const savedUsername = localStorage.getItem('optrail_active_username') || 'controller';
          const matched = res.demo_users.find(u => u.username === savedUsername) || res.demo_users[0];
          
          setCurrentUser(matched);
          if (matched.token) {
            localStorage.setItem('optrail_jwt_token', matched.token);
            localStorage.setItem('optrail_active_username', matched.username);
          }
        }
      } catch (err) {
        console.warn('Failed to load demo users, falling back to local default', err);
        // Fallback default
        setCurrentUser({
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
          permissions: ['optimize:run', 'schedule:approve', 'schedule:reject', 'scenario:run', 'task:create']
        });
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  const switchRole = async (targetUsername) => {
    try {
      const res = await apiService.switchRole(targetUsername);
      if (res && res.user) {
        setCurrentUser(res.user);
        localStorage.setItem('optrail_active_username', targetUsername);
        
        // Show role change notification toast
        setNotification({
          type: 'info',
          title: `Role Switched: ${res.user.designation}`,
          message: res.user.can_optimize 
            ? 'Full Section Controller privileges active. CP-SAT timetable re-optimization enabled.'
            : 'Engineering departmental mode active. Block request submission enabled; global optimization restricted to Controller.'
        });
        
        setTimeout(() => setNotification(null), 4500);
        return res.user;
      }
    } catch (err) {
      console.error('Failed to switch role', err);
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
