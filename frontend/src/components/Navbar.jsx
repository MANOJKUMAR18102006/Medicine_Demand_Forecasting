import React, { useState, useRef, useEffect } from 'react';
import { 
  Activity, 
  TrendingUp, 
  Package, 
  BarChart3, 
  Cpu, 
  RefreshCw, 
  LayoutDashboard,
  Menu,
  X,
  Building2,
  ChevronDown,
  User,
  LogOut,
  Settings,
  Plus
} from 'lucide-react';

export default function Navbar({ 
  activeTab, 
  setActiveTab, 
  healthStatus, 
  onRefreshHealth,
  currentShop,
  onOpenProfile,
  onOpenAddMedicine,
  onLogout 
}) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'forecast', label: 'Demand Forecast', icon: TrendingUp },
    { id: 'inventory', label: 'Inventory Analysis', icon: Package },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'models', label: 'Model Performance', icon: Cpu },
  ];

  // Close profile dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setProfileDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="sticky top-0 z-50 w-full bg-white border-b border-slate-200 shadow-xs">
      <div className="max-w-[1460px] mx-auto px-4 sm:px-8 h-17 flex items-center justify-between gap-4 sm:gap-6">
        
        {/* Left Branding */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="w-9 h-9 rounded-lg bg-teal-600 text-white flex items-center justify-center shadow-xs">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-base tracking-tight text-slate-900 leading-none">
                MedDemand
              </span>
              <span className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-teal-50 text-teal-700 border border-teal-200 leading-none">
                AI Forecasting
              </span>
            </div>
            <p className="text-[11px] text-slate-500 font-medium leading-tight mt-0.5 hidden xl:block">
              Medicine Demand Forecasting & Inventory Optimization
            </p>
          </div>
        </div>

        {/* Center Desktop Navigation Items */}
        <nav className="hidden lg:flex items-center gap-1.5 flex-1 justify-center max-w-2xl">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition cursor-pointer ${
                  isActive
                    ? 'bg-teal-50 text-teal-800 border border-teal-200 font-semibold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-teal-600' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Right Actions & Profile Dropdown */}
        <div className="flex items-center gap-2 sm:gap-3 shrink-0">
          
          {/* Quick Add Medicine Button */}
          {onOpenAddMedicine && (
            <button
              onClick={onOpenAddMedicine}
              className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-teal-50 hover:bg-teal-100/80 text-teal-700 border border-teal-200 text-xs font-semibold shadow-2xs transition cursor-pointer"
              title="Add medicine to your inventory"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Medicine</span>
            </button>
          )}

          {/* API Health Pill */}
          <div
            className={`hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
              healthStatus.connected
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : 'bg-rose-50 text-rose-700 border-rose-200'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full shrink-0 ${
                healthStatus.connected ? 'bg-emerald-500' : 'bg-rose-500'
              }`}
            />
            <span className="text-[11px] font-medium tracking-tight whitespace-nowrap">
              {healthStatus.loading
                ? 'Connecting...'
                : healthStatus.connected
                ? 'API Online'
                : 'API Offline'}
            </span>
          </div>

          {/* Refresh Health Button */}
          <button
            onClick={onRefreshHealth}
            disabled={healthStatus.loading}
            className="w-8 h-8 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 hover:text-slate-900 flex items-center justify-center transition shadow-xs disabled:opacity-50 cursor-pointer"
            title="Refresh API Connection"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${healthStatus.loading ? 'animate-spin text-teal-600' : ''}`} />
          </button>

          {/* Authenticated Shop Profile Dropdown */}
          {currentShop && (
            <div className="relative" ref={dropdownRef}>
              <button
                type="button"
                onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
                className="flex items-center gap-2 p-1.5 sm:px-2.5 sm:py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-800 transition shadow-2xs cursor-pointer"
              >
                <div className="w-6 h-6 rounded-md bg-teal-600 text-white flex items-center justify-center text-xs font-bold shrink-0">
                  {currentShop.shop_name?.charAt(0).toUpperCase() || 'S'}
                </div>
                <div className="text-left hidden md:block max-w-[130px] truncate">
                  <div className="text-xs font-semibold text-slate-900 truncate leading-tight">
                    {currentShop.shop_name}
                  </div>
                  <div className="text-[10px] text-slate-500 truncate leading-tight">
                    {currentShop.owner_name}
                  </div>
                </div>
                <ChevronDown className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              </button>

              {/* Profile Dropdown Menu */}
              {profileDropdownOpen && (
                <div className="absolute right-0 mt-2 w-64 bg-white rounded-xl border border-slate-200 shadow-lg py-2 z-50 text-xs font-sans">
                  <div className="px-3.5 py-2 border-b border-slate-100">
                    <p className="font-semibold text-slate-900 truncate">
                      {currentShop.shop_name}
                    </p>
                    <p className="text-[11px] text-slate-500 truncate mt-0.5">
                      {currentShop.email}
                    </p>
                    <div className="inline-block mt-1 px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 text-[10px] font-medium border border-emerald-200">
                      Medical Shop Active
                    </div>
                  </div>

                  <div className="py-1">
                    <button
                      type="button"
                      onClick={() => {
                        setProfileDropdownOpen(false);
                        if (onOpenProfile) onOpenProfile();
                      }}
                      className="w-full flex items-center gap-2.5 px-3.5 py-2 text-slate-700 hover:bg-slate-50 transition cursor-pointer"
                    >
                      <Settings className="w-4 h-4 text-slate-400" />
                      <span>Shop Settings & Profile</span>
                    </button>

                    {onOpenAddMedicine && (
                      <button
                        type="button"
                        onClick={() => {
                          setProfileDropdownOpen(false);
                          onOpenAddMedicine();
                        }}
                        className="w-full flex items-center gap-2.5 px-3.5 py-2 text-slate-700 hover:bg-slate-50 transition cursor-pointer"
                      >
                        <Plus className="w-4 h-4 text-teal-600" />
                        <span>Add New Medicine</span>
                      </button>
                    )}
                  </div>

                  <div className="border-t border-slate-100 pt-1">
                    <button
                      type="button"
                      onClick={() => {
                        setProfileDropdownOpen(false);
                        onLogout();
                      }}
                      className="w-full flex items-center gap-2.5 px-3.5 py-2 text-rose-600 hover:bg-rose-50 transition cursor-pointer font-medium"
                    >
                      <LogOut className="w-4 h-4 text-rose-500" />
                      <span>Sign Out</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Mobile Hamburger Toggle */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden w-8 h-8 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 flex items-center justify-center transition cursor-pointer"
            aria-label="Toggle Navigation"
          >
            {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>

        </div>

      </div>

      {/* Mobile Responsive Navigation Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-slate-200 bg-white px-6 py-3 space-y-1 shadow-sm">
          {currentShop && (
            <div className="pb-2 mb-2 border-b border-slate-100 flex items-center justify-between">
              <div>
                <p className="text-xs font-bold text-slate-900">{currentShop.shop_name}</p>
                <p className="text-[11px] text-slate-500">{currentShop.email}</p>
              </div>
              <button
                onClick={() => {
                  setMobileMenuOpen(false);
                  if (onOpenProfile) onOpenProfile();
                }}
                className="text-xs text-teal-600 font-semibold cursor-pointer"
              >
                Settings
              </button>
            </div>
          )}

          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  setActiveTab(item.id);
                  setMobileMenuOpen(false);
                }}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition cursor-pointer ${
                  isActive
                    ? 'bg-teal-50 text-teal-800 border border-teal-200 font-semibold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-teal-600' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}

          {currentShop && (
            <div className="pt-2 border-t border-slate-100">
              <button
                onClick={() => {
                  setMobileMenuOpen(false);
                  onLogout();
                }}
                className="w-full flex items-center gap-2 px-3 py-2 text-xs font-semibold text-rose-600 hover:bg-rose-50 rounded-lg cursor-pointer"
              >
                <LogOut className="w-4 h-4" />
                <span>Sign Out of {currentShop.shop_name}</span>
              </button>
            </div>
          )}
        </div>
      )}

    </header>
  );
}
