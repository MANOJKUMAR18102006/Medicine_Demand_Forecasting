import React, { useState, useEffect } from 'react';
import { 
  Package, 
  CheckCircle, 
  AlertTriangle, 
  AlertOctagon, 
  Sparkles,
  Info,
  Clock,
  Boxes,
  Plus,
  Save,
  CheckCircle2
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid, 
  Cell 
} from 'recharts';
import { analyzeInventory, updateMedicineStock } from '../services/api';

export default function InventoryTab({ 
  medicines, 
  initialMedicine = 'Paracetamol', 
  onOpenAddMedicine,
  onStockUpdated 
}) {
  const [selectedMedicine, setSelectedMedicine] = useState(initialMedicine);
  const [horizon, setHorizon] = useState(7);
  const [stockInput, setStockInput] = useState('900');
  const [loading, setLoading] = useState(false);
  const [updatingStock, setUpdatingStock] = useState(false);
  const [stockUpdateSuccess, setStockUpdateSuccess] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const fetchInventoryAnalysis = async (med, days) => {
    if (!med) return;
    setLoading(true);
    setError(null);
    const stockVal = stockInput !== '' ? Number(stockInput) : null;
    const res = await analyzeInventory(med, days, stockVal);
    if (res.ok) {
      setResult(res.data);
    } else {
      setError(res.error);
    }
    setLoading(false);
  };

  useEffect(() => {
    if (initialMedicine && medicines.includes(initialMedicine)) {
      setSelectedMedicine(initialMedicine);
      fetchInventoryAnalysis(initialMedicine, horizon);
    } else if (medicines && medicines.length > 0) {
      setSelectedMedicine(medicines[0]);
      fetchInventoryAnalysis(medicines[0], horizon);
    }
  }, [initialMedicine, medicines]);

  const handleSubmit = (e) => {
    e.preventDefault();
    fetchInventoryAnalysis(selectedMedicine, horizon);
  };

  const handleSaveStockToDatabase = async () => {
    if (!selectedMedicine || stockInput === '' || isNaN(stockInput)) return;
    setUpdatingStock(true);
    setStockUpdateSuccess(false);
    setError(null);

    const res = await updateMedicineStock(selectedMedicine, {
      current_stock: Number(stockInput),
    });
    setUpdatingStock(false);

    if (res.ok) {
      setStockUpdateSuccess(true);
      fetchInventoryAnalysis(selectedMedicine, horizon);
      if (onStockUpdated) onStockUpdated();
      setTimeout(() => setStockUpdateSuccess(false), 3000);
    } else {
      setError(res.error);
    }
  };

  // Chart data preparation
  const chartData = result ? [
    { name: 'Current Stock', value: result.current_stock, color: '#0284c7' },
    { name: 'Forecast Demand', value: result.predicted_demand, color: '#0d9488' },
    { name: 'Safety Buffer', value: result.safety_stock, color: '#6366f1' },
    { name: 'Required Stock', value: result.required_stock, color: '#d97706' },
  ] : [];

  let statusBadge = {
    cardBg: 'bg-slate-50 border-slate-200 text-slate-800',
    badgeBg: 'bg-slate-100 text-slate-700 border-slate-200',
    icon: Info,
    iconColor: 'text-slate-600',
  };

  if (result) {
    if (result.inventory_status === 'Critical') {
      statusBadge = {
        cardBg: 'bg-rose-50/80 border-rose-200 text-rose-950',
        badgeBg: 'bg-rose-100 text-rose-800 border-rose-300',
        icon: AlertOctagon,
        iconColor: 'text-rose-600',
      };
    } else if (result.inventory_status === 'Low Stock') {
      statusBadge = {
        cardBg: 'bg-amber-50/80 border-amber-200 text-amber-950',
        badgeBg: 'bg-amber-100 text-amber-800 border-amber-300',
        icon: AlertTriangle,
        iconColor: 'text-amber-600',
      };
    } else if (result.inventory_status === 'Sufficient') {
      statusBadge = {
        cardBg: 'bg-emerald-50/80 border-emerald-200 text-emerald-950',
        badgeBg: 'bg-emerald-100 text-emerald-800 border-emerald-300',
        icon: CheckCircle,
        iconColor: 'text-emerald-600',
      };
    } else if (result.inventory_status === 'Overstocked') {
      statusBadge = {
        cardBg: 'bg-blue-50/80 border-blue-200 text-blue-950',
        badgeBg: 'bg-blue-100 text-blue-800 border-blue-300',
        icon: Boxes,
        iconColor: 'text-blue-600',
      };
    }
  }

  const StatusIcon = statusBadge.icon;

  return (
    <div className="space-y-6">
      
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-2">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">
            Inventory Analysis & Procurement Decision Support
          </h2>
          <p className="text-sm text-slate-500 mt-0.5">
            Compute safety buffer requirements, deficit shortages, and recommended purchase order quantities.
          </p>
        </div>
        {onOpenAddMedicine && (
          <button
            onClick={onOpenAddMedicine}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer self-start sm:self-auto"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Medicine</span>
          </button>
        )}
      </div>

      {/* Input Parameters Form */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs">
        <form onSubmit={handleSubmit} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
          
          {/* Medicine Selector */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
              <Package className="w-3.5 h-3.5 text-teal-600" />
              Medicine
            </label>
            <select
              value={selectedMedicine}
              onChange={(e) => setSelectedMedicine(e.target.value)}
              disabled={medicines.length === 0}
              className="w-full bg-white border border-slate-300 rounded-lg px-3.5 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 transition shadow-2xs disabled:bg-slate-50"
            >
              {medicines.length === 0 ? (
                <option value="">No medicines in shop catalog</option>
              ) : (
                medicines.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))
              )}
            </select>
          </div>

          {/* Forecast Horizon */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-teal-600" />
              Planning Horizon
            </label>
            <select
              value={horizon}
              onChange={(e) => setHorizon(Number(e.target.value))}
              className="w-full bg-white border border-slate-300 rounded-lg px-3.5 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 transition shadow-2xs"
            >
              <option value={7}>7 Days (1 Week)</option>
              <option value={14}>14 Days (Bi-weekly)</option>
              <option value={30}>30 Days (Monthly)</option>
            </select>
          </div>

          {/* Current Stock Input */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                <Boxes className="w-3.5 h-3.5 text-teal-600" />
                Current Stock on Hand
              </label>
              {stockUpdateSuccess && (
                <span className="text-[10px] text-emerald-600 font-semibold flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Saved!
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <input
                type="number"
                min="0"
                value={stockInput}
                onChange={(e) => setStockInput(e.target.value)}
                placeholder="e.g. 900"
                className="w-full bg-white border border-slate-300 rounded-lg px-3.5 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 transition shadow-2xs font-mono"
              />
              <button
                type="button"
                onClick={handleSaveStockToDatabase}
                disabled={updatingStock || !selectedMedicine}
                title="Save this physical stock value to your medical shop inventory in the database"
                className="px-2.5 py-2 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-medium transition cursor-pointer shrink-0 disabled:opacity-50"
              >
                {updatingStock ? '...' : <Save className="w-4 h-4 text-slate-600" />}
              </button>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || medicines.length === 0}
            className="flex items-center justify-center gap-2 bg-teal-600 hover:bg-teal-700 text-white font-medium px-5 py-2 rounded-lg text-sm transition shadow-xs disabled:opacity-50 cursor-pointer h-10"
          >
            {loading ? (
              <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
            ) : (
              <Sparkles className="w-4 h-4" />
            )}
            <span>Analyze Inventory</span>
          </button>

        </form>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-center gap-3">
          <AlertOctagon className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Analysis Results Display */}
      {result && (
        <div className="space-y-6">
          
          {/* Status Alert Banner */}
          <div className={`rounded-xl border p-5 ${statusBadge.cardBg} transition`}>
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div className="flex items-start gap-3.5">
                <div className="p-2 rounded-lg bg-white/80 shadow-2xs shrink-0 mt-0.5 md:mt-0">
                  <StatusIcon className={`w-5 h-5 ${statusBadge.iconColor}`} />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-base font-bold text-slate-900">
                      Inventory Status:
                    </span>
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${statusBadge.badgeBg}`}>
                      {result.inventory_status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-700 font-medium mt-1 leading-relaxed">
                    {result.recommendation}
                  </p>
                </div>
              </div>

              {result.recommended_order_quantity > 0 && (
                <div className="bg-white rounded-lg px-4 py-2.5 border border-slate-200 shadow-2xs text-right shrink-0">
                  <span className="text-[11px] uppercase tracking-wider text-slate-400 font-bold block">
                    Procurement Order
                  </span>
                  <span className="text-lg font-bold text-teal-700 font-mono">
                    +{result.recommended_order_quantity.toLocaleString()} units
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Metric Summary Cards Grid */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block">
                Current Stock On-Hand
              </span>
              <div className="text-xl font-bold text-slate-900 font-mono mt-1">
                {result.current_stock.toLocaleString()}
              </div>
              <span className="text-[11px] text-slate-500 mt-0.5 block">
                Physical shop count
              </span>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block">
                {result.forecast_period}-Day Predicted Demand
              </span>
              <div className="text-xl font-bold text-teal-700 font-mono mt-1">
                {result.predicted_demand.toLocaleString()}
              </div>
              <span className="text-[11px] text-slate-500 mt-0.5 block">
                Avg: {result.average_daily_demand} units/day
              </span>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block">
                Safety Stock Buffer
              </span>
              <div className="text-xl font-bold text-indigo-600 font-mono mt-1">
                {result.safety_stock.toLocaleString()}
              </div>
              <span className="text-[11px] text-slate-500 mt-0.5 block">
                95% availability (Z=1.65)
              </span>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block">
                Required Target Stock
              </span>
              <div className="text-xl font-bold text-amber-600 font-mono mt-1">
                {result.required_stock.toLocaleString()}
              </div>
              <span className="text-[11px] text-slate-500 mt-0.5 block">
                Forecast + Safety Buffer
              </span>
            </div>

          </div>

          {/* Breakdown Chart & Calculation Explainer */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* Inventory Balance Bar Chart */}
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">
                    Stock Comparison & Thresholds
                  </h3>
                  <p className="text-xs text-slate-500">
                    Visual comparison of current inventory vs demand and buffer metrics
                  </p>
                </div>
              </div>

              <div className="h-60 w-full pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                    <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} tickLine={false} />
                    <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#ffffff', 
                        borderColor: '#e2e8f0', 
                        borderRadius: '8px', 
                        fontSize: '12px' 
                      }}
                      formatter={(val) => [`${val.toLocaleString()} units`, 'Quantity']}
                    />
                    <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Formula & Decision Logic Card */}
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
              <h3 className="text-sm font-bold text-slate-900">
                Optimization Engine Logic
              </h3>
              
              <div className="space-y-3 text-xs text-slate-600">
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                  <div className="font-semibold text-slate-800">1. Safety Stock Buffer (SS)</div>
                  <div className="font-mono text-[11px] text-teal-700 mt-0.5">
                    SS = Z × σ_daily × √(Lead_Time) = 1.65 × σ × √2
                  </div>
                  <p className="text-slate-500 text-[11px] mt-1">
                    Protects your medical shop against unpredictable demand surges and supplier delivery delays.
                  </p>
                </div>

                <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                  <div className="font-semibold text-slate-800">2. Required Target Stock</div>
                  <div className="font-mono text-[11px] text-teal-700 mt-0.5">
                    Target = Forecasted_Demand + Safety_Stock
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                  <div className="font-semibold text-slate-800">3. Reorder Quantity (ROQ)</div>
                  <div className="font-mono text-[11px] text-teal-700 mt-0.5">
                    ROQ = max(0, Target - Current_Stock)
                  </div>
                </div>
              </div>
            </div>

          </div>

        </div>
      )}

    </div>
  );
}
