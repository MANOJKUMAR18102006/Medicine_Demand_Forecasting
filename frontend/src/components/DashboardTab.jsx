import React, { useState } from 'react';
import { 
  Pill, 
  TrendingUp, 
  AlertTriangle, 
  AlertOctagon, 
  ArrowRight,
  Package,
  Plus,
  Sparkles,
  Building2,
  Boxes
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid 
} from 'recharts';
import { seedStarterMedicines } from '../services/api';

export default function DashboardTab({ 
  summary, 
  loading, 
  error,
  onRetry,
  onSelectMedicineForForecast, 
  onSelectMedicineForInventory,
  currentShop,
  onOpenAddMedicine
}) {
  const [seeding, setSeeding] = useState(false);

  if (loading) {
    return (
      <div className="py-24 text-center space-y-3">
        <div className="w-8 h-8 border-2 border-teal-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
        <p className="text-sm text-slate-500 font-medium">Loading healthcare analytics dashboard...</p>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="py-16 max-w-lg mx-auto text-center space-y-4">
        <div className="w-12 h-12 rounded-full bg-rose-50 text-rose-600 border border-rose-200 flex items-center justify-center mx-auto">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <div className="space-y-1.5">
          <h3 className="text-base font-bold text-slate-900">Dashboard Unavailable</h3>
          <p className="text-xs text-slate-600 max-w-md mx-auto">
            {error || 'Unable to connect to the backend server. Please verify the FastAPI service is running on port 8000.'}
          </p>
        </div>
        {onRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer"
          >
            Retry Connection
          </button>
        )}
      </div>
    );
  }

  const total_medicines = summary?.total_medicines ?? 0;
  const average_demand = summary?.average_demand ?? 0;
  const low_stock_count = summary?.low_stock_count ?? 0;
  const critical_stock_count = summary?.critical_stock_count ?? 0;
  const monthly_demand_summary = summary?.monthly_demand_summary || [];
  const top_medicines = summary?.top_medicines || [];
  const inventory_alerts = summary?.inventory_alerts || [];
  const is_empty = summary?.is_empty || total_medicines === 0;

  const handleQuickSeed = async () => {
    setSeeding(true);
    await seedStarterMedicines();
    setSeeding(false);
    if (onRetry) onRetry();
  };

  return (
    <div className="space-y-6">
      
      {/* Top Welcome / Overview Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-2">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold tracking-tight text-slate-900">
              Supply Chain & Demand Overview
            </h2>
            {currentShop && (
              <span className="hidden sm:inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-teal-50 text-teal-800 border border-teal-200 text-xs font-semibold">
                <Building2 className="w-3 h-3 text-teal-600" />
                {currentShop.shop_name}
              </span>
            )}
          </div>
          <p className="text-sm text-slate-500 mt-0.5">
            Real-time machine learning forecasts and procurement recommendations for {currentShop?.shop_name || 'your medical shop'}.
          </p>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-auto">
          {onOpenAddMedicine && (
            <button
              onClick={onOpenAddMedicine}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Medicine</span>
            </button>
          )}
          <span className="text-xs font-semibold px-2.5 py-1.5 rounded-md bg-teal-50 text-teal-800 border border-teal-200">
            Model: XGBoost Regressor
          </span>
        </div>
      </div>

      {/* Empty State Banner for New Medical Shops */}
      {is_empty && (
        <div className="rounded-xl border border-teal-200 bg-teal-50/60 p-6 sm:p-7 shadow-xs">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="w-8 h-8 rounded-lg bg-teal-600 text-white flex items-center justify-center">
                  <Boxes className="w-4 h-4" />
                </span>
                <h3 className="text-base font-bold text-slate-900">
                  Welcome to MedDemand! No medicines added yet.
                </h3>
              </div>
              <p className="text-xs text-slate-600 max-w-xl pl-10">
                Each medical shop manages its own private inventory. You haven't registered any pharmaceutical drugs for <span className="font-semibold text-slate-800">{currentShop?.shop_name}</span> yet.
              </p>
            </div>
            <div className="flex items-center gap-2.5 pl-10 sm:pl-0">
              {onOpenAddMedicine && (
                <button
                  onClick={onOpenAddMedicine}
                  className="px-3.5 py-2 rounded-lg bg-white border border-teal-300 text-teal-800 hover:bg-teal-50 text-xs font-semibold shadow-2xs transition cursor-pointer"
                >
                  Add Custom Medicine
                </button>
              )}
              <button
                onClick={handleQuickSeed}
                disabled={seeding}
                className="px-4 py-2 rounded-lg bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold shadow-xs transition flex items-center gap-1.5 disabled:opacity-60 cursor-pointer"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>{seeding ? 'Importing Catalog...' : 'Load Standard Hospital Catalog'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* Total Medicines */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-2 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Tracked Drugs</span>
            <span className="w-8 h-8 rounded-lg bg-teal-50 text-teal-700 flex items-center justify-center border border-teal-100">
              <Pill className="w-4 h-4" />
            </span>
          </div>
          <div className="text-2xl font-bold text-slate-900 tracking-tight">{total_medicines}</div>
          <p className="text-xs text-slate-500">Active medicines in shop catalog</p>
        </div>

        {/* Avg Daily Demand */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-2 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Avg Daily Volume</span>
            <span className="w-8 h-8 rounded-lg bg-blue-50 text-blue-700 flex items-center justify-center border border-blue-100">
              <TrendingUp className="w-4 h-4" />
            </span>
          </div>
          <div className="text-2xl font-bold text-slate-900 tracking-tight">
            {average_demand} <span className="text-sm font-normal text-slate-500">units/day</span>
          </div>
          <p className="text-xs text-slate-500">Projected shop consumption rate</p>
        </div>

        {/* Low Stock Medicines */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-2 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Low Stock Warnings</span>
            <span className="w-8 h-8 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center border border-amber-100">
              <AlertTriangle className="w-4 h-4" />
            </span>
          </div>
          <div className="text-2xl font-bold text-amber-600 tracking-tight">{low_stock_count}</div>
          <p className="text-xs text-slate-500">Replenishment recommended soon</p>
        </div>

        {/* Critical Stock Medicines */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-2 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Critical Stockouts</span>
            <span className="w-8 h-8 rounded-lg bg-rose-50 text-rose-700 flex items-center justify-center border border-rose-100">
              <AlertOctagon className="w-4 h-4" />
            </span>
          </div>
          <div className="text-2xl font-bold text-rose-600 tracking-tight">{critical_stock_count}</div>
          <p className="text-xs text-slate-500">Depletion risk within 7 days</p>
        </div>

      </div>

      {/* Demand Trend & Top Medicines Split Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left 2 Cols: Monthly Demand Trend Chart */}
        <div className="lg:col-span-2 rounded-xl border border-slate-200 bg-white p-6 space-y-4 shadow-xs">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-slate-900 text-base">Monthly Demand Seasonality</h3>
              <p className="text-xs text-slate-500">Average units consumed per day across the 12 calendar months</p>
            </div>
            <span className="text-xs font-medium px-2.5 py-1 rounded bg-slate-100 text-slate-700 border border-slate-200">
              Annual Pattern
            </span>
          </div>

          <div className="h-64 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={monthly_demand_summary} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="lightColorDemand" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0d9488" stopOpacity={0.25}/>
                    <stop offset="95%" stopColor="#0d9488" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="month" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#ffffff', 
                    borderColor: '#e2e8f0', 
                    borderRadius: '8px', 
                    fontSize: '12px',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.07)'
                  }}
                  formatter={(value) => [`${value} units/day`, 'Avg Demand']}
                />
                <Area 
                  type="monotone" 
                  dataKey="avg_demand" 
                  stroke="#0d9488" 
                  strokeWidth={2.5} 
                  fillOpacity={1} 
                  fill="url(#lightColorDemand)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right 1 Col: Top 5 Highest Demand Medicines */}
        <div className="rounded-xl border border-slate-200 bg-white p-6 space-y-4 shadow-xs">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-slate-900 text-base">Top Consumed Medicines</h3>
            <span className="text-xs text-slate-500 font-medium">Daily Volume</span>
          </div>

          <div className="space-y-2.5">
            {top_medicines.length === 0 ? (
              <div className="py-12 text-center text-xs text-slate-400">
                No medicine consumption recorded yet.
              </div>
            ) : (
              top_medicines.slice(0, 5).map((med, idx) => (
                <div 
                  key={med.medicine}
                  className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-100 hover:border-slate-200 transition"
                >
                  <div className="flex items-center gap-3">
                    <span className="w-5 text-center text-xs font-bold text-slate-400">#{idx + 1}</span>
                    <div>
                      <div className="text-xs font-semibold text-slate-900">{med.medicine}</div>
                      <div className="text-[11px] text-slate-500">{med.category}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs font-bold text-teal-700">{med.avg_daily_demand}</div>
                    <div className="text-[10px] text-slate-500">units/day</div>
                  </div>
                </div>
              ))
            )}
          </div>

        </div>

      </div>

      {/* Inventory Alerts Table */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 space-y-4 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <h3 className="font-semibold text-slate-900 text-base flex items-center gap-2">
              <Package className="w-4 h-4 text-teal-600" />
              Inventory Status & Reorder Recommendations (7-Day Horizon)
            </h3>
            <p className="text-xs text-slate-500">
              Procurement health computed from ML demand forecasts and safety buffer formula
            </p>
          </div>
          <span className="text-xs text-slate-500 font-mono">
            {inventory_alerts.length} medicines analyzed
          </span>
        </div>

        <div className="overflow-x-auto border border-slate-200 rounded-lg">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-slate-600 uppercase tracking-wider text-[11px] border-b border-slate-200">
              <tr>
                <th className="py-3 px-4 font-semibold">Medicine</th>
                <th className="py-3 px-4 font-semibold">Category</th>
                <th className="py-3 px-4 font-semibold text-right">Current Stock</th>
                <th className="py-3 px-4 font-semibold text-right">7-Day Forecast</th>
                <th className="py-3 px-4 font-semibold text-right">Required Buffer</th>
                <th className="py-3 px-4 font-semibold text-right">Shortage</th>
                <th className="py-3 px-4 font-semibold text-center">Status</th>
                <th className="py-3 px-4 font-semibold text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {inventory_alerts.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-xs text-slate-400">
                    No medicine inventory records found for this medical shop.
                  </td>
                </tr>
              ) : (
                inventory_alerts.map((item) => {
                  let badgeClass = 'bg-slate-100 text-slate-700 border-slate-200';
                  if (item.status === 'Critical') badgeClass = 'bg-rose-50 text-rose-700 border-rose-200';
                  else if (item.status === 'Low Stock') badgeClass = 'bg-amber-50 text-amber-700 border-amber-200';
                  else if (item.status === 'Sufficient') badgeClass = 'bg-emerald-50 text-emerald-700 border-emerald-200';
                  else if (item.status === 'Overstocked') badgeClass = 'bg-blue-50 text-blue-700 border-blue-200';

                  return (
                    <tr key={item.medicine} className="hover:bg-slate-50/70 transition">
                      <td className="py-3 px-4 font-medium text-slate-900">{item.medicine}</td>
                      <td className="py-3 px-4 text-slate-500">{item.category}</td>
                      <td className="py-3 px-4 text-right font-mono">{item.current_stock.toLocaleString()}</td>
                      <td className="py-3 px-4 text-right font-mono font-medium text-teal-700">{item.predicted_demand.toLocaleString()}</td>
                      <td className="py-3 px-4 text-right font-mono">{item.required_stock.toLocaleString()}</td>
                      <td className="py-3 px-4 text-right font-mono font-semibold text-rose-600">
                        {item.expected_shortage > 0 ? item.expected_shortage.toLocaleString() : '-'}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className={`inline-block px-2.5 py-0.5 rounded text-[10px] font-semibold border ${badgeClass}`}>
                          {item.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => onSelectMedicineForInventory(item.medicine)}
                          className="inline-flex items-center gap-1 text-[11px] text-teal-700 hover:text-teal-900 transition font-medium cursor-pointer"
                        >
                          Analyze <ArrowRight className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

      </div>

    </div>
  );
}
