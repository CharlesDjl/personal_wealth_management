import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { LayoutDashboard, Wallet, PieChart, ArrowLeftRight, LogOut, User } from 'lucide-react';
import { cn } from '../../lib/utils';

export const MainLayout = () => {
  const { signOut, user } = useAuth();
  const location = useLocation();

  const navigation = [
    { name: '总览', href: '/', icon: LayoutDashboard },
    { name: '资产管理', href: '/assets', icon: Wallet },
    { name: '资产报告', href: '/reports', icon: PieChart },
    { name: '调仓建议', href: '/rebalancing', icon: ArrowLeftRight },
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <div className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 bg-slate-900 text-white">
        <div className="flex-1 flex flex-col min-h-0">
          <div className="flex items-center h-16 flex-shrink-0 px-4 bg-slate-900 border-b border-slate-800">
            <h1 className="text-xl font-bold text-yellow-500">Wealth Manager</h1>
          </div>
          <div className="flex-1 flex flex-col overflow-y-auto">
            <nav className="flex-1 px-2 py-4 space-y-1">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={cn(
                      isActive
                        ? 'bg-slate-800 text-white'
                        : 'text-slate-300 hover:bg-slate-800 hover:text-white',
                      'group flex items-center px-2 py-2 text-sm font-medium rounded-md'
                    )}
                  >
                    <item.icon
                      className={cn(
                        isActive ? 'text-yellow-500' : 'text-slate-400 group-hover:text-yellow-500',
                        'mr-3 flex-shrink-0 h-6 w-6'
                      )}
                      aria-hidden="true"
                    />
                    {item.name}
                  </Link>
                );
              })}
            </nav>
          </div>
          <div className="flex-shrink-0 flex bg-slate-800 p-4">
            <div className="flex items-center w-full">
              <div className="flex-shrink-0">
                <User className="h-8 w-8 rounded-full bg-slate-600 p-1 text-slate-300" />
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-white truncate max-w-[120px]">
                  {user?.email}
                </p>
                <button
                  onClick={signOut}
                  className="text-xs font-medium text-slate-300 hover:text-white flex items-center mt-1"
                >
                  <LogOut className="h-3 w-3 mr-1" />
                  退出登录
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="md:pl-64 flex flex-col flex-1">
        <main className="flex-1">
          <div className="py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
              <Outlet />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};
