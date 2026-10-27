import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import DashboardTab from './components/DashboardTab';
import ForecastTab from './components/ForecastTab';
import InventoryTab from './components/InventoryTab';
import AnalyticsTab from './components/AnalyticsTab';
import ModelPerformanceTab from './components/ModelPerformanceTab';
import AuthPage from './components/AuthPage';
import ShopProfileModal from './components/ShopProfileModal';
import AddMedicineModal from './components/AddMedicineModal';
import { 
  checkBackendHealth, 
  getMedicines, 
  getAnalyticsSummary,
  getCurrentShopProfile,
  logoutShop
} from './services/api';

export default function App() {
  // Authentication & Shop State
  const [currentShop, setCurrentShop] = useState(() => {
    const cached = localStorage.getItem('meddemand_shop') || sessionStorage.getItem('meddemand_shop');
    return cached ? JSON.parse(cached) : null;
  });
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return Boolean(localStorage.getItem('meddemand_token') || sessionStorage.getItem('meddemand_token'));
  });
  const [isAuthChecking, setIsAuthChecking] = useState(true);

  // Modals state
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isAddMedicineOpen, setIsAddMedicineOpen] = useState(false);

  // Active navigation tab
  const [activeTab, setActiveTab] = useState('dashboard');

  // Backend Health state
  const [healthStatus, setHealthStatus] = useState({
    loading: true,
    connected: false,
    details: null,
  });

  // Shop-specific data states
  const [medicines, setMedicines] = useState([]);
  const [selectedMedicine, setSelectedMedicine] = useState('');
  const [analyticsSummary, setAnalyticsSummary] = useState(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(true);
  const [analyticsError, setAnalyticsError] = useState(null);

  // Verify and refresh current shop session on startup
  useEffect(() => {
    const verifySession = async () => {
      const token = localStorage.getItem('meddemand_token') || sessionStorage.getItem('meddemand_token');
      if (token) {
        const res = await getCurrentShopProfile();
        if (res.ok) {
          setCurrentShop(res.data);
          setIsAuthenticated(true);
        } else {
          // Token invalid or expired
          setIsAuthenticated(false);
          setCurrentShop(null);
          localStorage.removeItem('meddemand_token');
          sessionStorage.removeItem('meddemand_token');
        }
      } else {
        setIsAuthenticated(false);
        setCurrentShop(null);
      }
      setIsAuthChecking(false);
    };

    verifySession();

    // Listen for 401 unauthenticated events from Axios interceptor
    const handleForcedLogout = () => {
      setIsAuthenticated(false);
      setCurrentShop(null);
    };
    window.addEventListener('meddemand_logout', handleForcedLogout);
    return () => window.removeEventListener('meddemand_logout', handleForcedLogout);
  }, []);

  const loadInitialData = async () => {
    if (!isAuthenticated) return;
    setAnalyticsLoading(true);
    setAnalyticsError(null);

    // Parallel fetch for optimal load speed and zero sequential blocking
    const [healthRes, medsRes, summaryRes] = await Promise.all([
      checkBackendHealth(),
      getMedicines(),
      getAnalyticsSummary(),
    ]);

    // Health state
    if (healthRes.ok) {
      setHealthStatus({
        loading: false,
        connected: true,
        details: healthRes.data,
      });
    } else {
      setHealthStatus({
        loading: false,
        connected: false,
        details: null,
      });
    }

    // Medicines catalog state
    if (medsRes.ok && Array.isArray(medsRes.data)) {
      setMedicines(medsRes.data);
      if (medsRes.data.length > 0) {
        if (!selectedMedicine || !medsRes.data.includes(selectedMedicine)) {
          setSelectedMedicine(medsRes.data[0]);
        }
      } else {
        setSelectedMedicine('');
      }
    }

    // Analytics summary state
    if (summaryRes.ok && summaryRes.data) {
      setAnalyticsSummary(summaryRes.data);
      setAnalyticsError(null);
    } else {
      setAnalyticsError(
        summaryRes.error || 'Failed to load dashboard analytics from backend.'
      );
    }

    setAnalyticsLoading(false);
  };

  useEffect(() => {
    if (isAuthenticated) {
      loadInitialData();
    }
  }, [isAuthenticated]);

  const handleLoginSuccess = (shopData) => {
    setCurrentShop(shopData);
    setIsAuthenticated(true);
    setActiveTab('dashboard');
  };

  const handleLogout = async () => {
    await logoutShop();
    setIsAuthenticated(false);
    setCurrentShop(null);
    setMedicines([]);
    setAnalyticsSummary(null);
    setSelectedMedicine('');
  };

  const handleMedicineAdded = (newMedName) => {
    loadInitialData();
    if (newMedName) {
      setSelectedMedicine(newMedName);
    }
  };

  const handleSelectForForecast = (med) => {
    setSelectedMedicine(med);
    setActiveTab('forecast');
  };

  const handleSelectForInventory = (med) => {
    setSelectedMedicine(med);
    setActiveTab('inventory');
  };

  // Initial loading splash
  if (isAuthChecking) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center font-sans">
        <div className="w-9 h-9 border-3 border-teal-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-xs text-slate-500 font-medium mt-3">Initializing MedDemand Platform...</p>
      </div>
    );
  }

  // If not authenticated, render Login & Registration page
  if (!isAuthenticated) {
    return <AuthPage onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans selection:bg-teal-500 selection:text-white">
      
      {/* Light Clean Navbar with Shop Profile Dropdown */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        healthStatus={healthStatus}
        onRefreshHealth={loadInitialData}
        currentShop={currentShop}
        onOpenProfile={() => setIsProfileOpen(true)}
        onOpenAddMedicine={() => setIsAddMedicineOpen(true)}
        onLogout={handleLogout}
      />

      {/* Main Centered Content Container */}
      <main className="flex-1 max-w-[1460px] w-full mx-auto px-4 sm:px-8 py-8">
        {activeTab === 'dashboard' && (
          <DashboardTab
            summary={analyticsSummary}
            loading={analyticsLoading}
            error={analyticsError}
            onRetry={loadInitialData}
            onSelectMedicineForForecast={handleSelectForForecast}
            onSelectMedicineForInventory={handleSelectForInventory}
            currentShop={currentShop}
            onOpenAddMedicine={() => setIsAddMedicineOpen(true)}
          />
        )}

        {activeTab === 'forecast' && (
          <ForecastTab
            medicines={medicines}
            initialMedicine={selectedMedicine}
            onOpenAddMedicine={() => setIsAddMedicineOpen(true)}
          />
        )}

        {activeTab === 'inventory' && (
          <InventoryTab
            medicines={medicines}
            initialMedicine={selectedMedicine}
            onOpenAddMedicine={() => setIsAddMedicineOpen(true)}
            onStockUpdated={loadInitialData}
          />
        )}

        {activeTab === 'analytics' && (
          <AnalyticsTab
            summary={analyticsSummary}
            loading={analyticsLoading}
            error={analyticsError}
            onRetry={loadInitialData}
          />
        )}

        {activeTab === 'models' && (
          <ModelPerformanceTab />
        )}
      </main>

      {/* Shop Profile Modal */}
      {isProfileOpen && (
        <ShopProfileModal
          shop={currentShop}
          onClose={() => setIsProfileOpen(false)}
          onProfileUpdated={(updatedShop) => setCurrentShop(updatedShop)}
        />
      )}

      {/* Add Medicine Modal */}
      {isAddMedicineOpen && (
        <AddMedicineModal
          onClose={() => setIsAddMedicineOpen(false)}
          onMedicineAdded={handleMedicineAdded}
        />
      )}

      {/* Clean Light Footer */}
      <footer className="border-t border-slate-200 bg-white py-4.5 text-center text-xs text-slate-500">
        <div className="max-w-[1460px] mx-auto px-4 sm:px-8 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>
            MedDemand AI Platform • Multi-Shop Medicine Demand Forecasting & Inventory Optimization
          </span>
          <span className="font-mono text-[11px] text-slate-400">
            {currentShop ? `Authenticated: ${currentShop.shop_name}` : 'FastAPI + XGBoost Engine'}
          </span>
        </div>
      </footer>
    </div>
  );
}
