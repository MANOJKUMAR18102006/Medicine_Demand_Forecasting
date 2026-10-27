import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  Calendar, 
  Sparkles, 
  Table as TableIcon, 
  AlertCircle,
  Pill,
  Clock,
  Plus,
  History,
  CheckCircle2
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
import { getDemandForecast, getForecastHistory } from '../services/api';

export default function ForecastTab({ 
  medicines, 
  initialMedicine = 'Paracetamol', 
  onOpenAddMedicine 
}) {
  const [selectedMedicine, setSelectedMedicine] = useState(initialMedicine);
  const [horizon, setHorizon] = useState(7);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [historyList, setHistoryList] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const fetchForecast = async (med, days) => {
    if (!med) return;
    setLoading(true);
    setError(null);
    const res = await getDemandForecast(med, days);
    if (res.ok) {
      setForecastData(res.data);
      loadHistory();
    } else {
      setError(res.error);
    }
    setLoading(false);
  };

  const loadHistory = async () => {
    setHistoryLoading(true);
    const res = await getForecastHistory(10);
    if (res.ok && Array.isArray(res.data)) {
      setHistoryList(res.data);
    }
    setHistoryLoading(false);
  };

  useEffect(() => {
    loadHistory();
  }, []);

  useEffect(() => {
    if (initialMedicine && medicines.includes(initialMedicine)) {
      setSelectedMedicine(initialMedicine);
      fetchForecast(initialMedicine, horizon);
    } else if (medicines && medicines.length > 0) {
      setSelectedMedicine(medicines[0]);
      fetchForecast(medicines[0], horizon);
    }
  }, [initialMedicine, medicines]);

  const handleSubmit = (e) => {
    e.preventDefault();
    fetchForecast(selectedMedicine, horizon);
  };

  return (
    <div className="space-y-6">
      
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-2">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">
            Demand Forecasting Engine
          </h2>
          <p className="text-sm text-slate-500 mt-0.5">
            Generate future multi-step recursive demand forecasts powered by the trained XGBoost model.
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

      {/* Control Form Card */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs">
        <form onSubmit={handleSubmit} className="flex flex-col md:flex-row items-stretch md:items-end gap-4">
          
          {/* Medicine Selector */}
          <div className="flex-1 space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
              <Pill className="w-3.5 h-3.5 text-teal-600" />
              Select Pharmaceutical Drug
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

          {/* Forecast Horizon Selector */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-teal-600" />
              Forecast Horizon
            </label>
            <div className="flex items-center gap-1.5 bg-slate-50 p-1 rounded-lg border border-slate-200">
              {[7, 14, 30].map((d) => (
                <button
                  type="button"
                  key={d}
                  onClick={() => setHorizon(d)}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition cursor-pointer ${
                    horizon === d
                      ? 'bg-white text-teal-800 shadow-2xs font-semibold border border-slate-200/80'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {d} Days
                </button>
              ))}
            </div>
          </div>

          {/* Generate Forecast Button */}
          <button
            type="submit"
            disabled={loading || medicines.length === 0}
            className="flex items-center justify-center gap-2 bg-teal-600 hover:bg-teal-700 text-white font-medium px-5 py-2.5 rounded-lg text-sm transition shadow-xs disabled:opacity-50 cursor-pointer h-10"
          >
            {loading ? (
              <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
            ) : (
              <Sparkles className="w-4 h-4" />
            )}
            <span>Generate Forecast</span>
          </button>

        </form>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-center gap-3">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Forecast Output */}
      {forecastData && (
        <div className="space-y-6">
          
          {/* Summary KPI Strip */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            
            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block">
                Total Predicted Demand
              </span>
              <div className="text-2xl font-bold text-teal-700 font-mono mt-1">
                {forecastData.total_predicted_demand.toLocaleString()} <span className="text-xs font-normal text-slate-500">units</span>
              </div>
              <span className="text-[11px] text-slate-500 mt-0.5 block">
                Over next {forecastData.days} days
              </span>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block">
                Average Daily Consumption
              </span>
              <div className="text-2xl font-bold text-slate-900 font-mono mt-1">
                {forecastData.average_daily_demand} <span className="text-xs font-normal text-slate-500">units/day</span>
              </div>
              <span className="text-[11px] text-slate-500 mt-0.5 block">
                Predicted run-rate
              </span>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block">
                Therapeutic Category
              </span>
              <div className="text-base font-bold text-slate-900 mt-1 truncate">
                {forecastData.category}
              </div>
              <span className="text-[11px] text-slate-500 mt-0.5 block font-mono">
                ${forecastData.unit_price.toFixed(2)} / unit
              </span>
            </div>

            <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block">
                Model Engine
              </span>
              <div className="text-base font-bold text-slate-900 mt-1">
                {forecastData.model_used}
              </div>
              <span className="text-[11px] text-emerald-600 font-medium mt-0.5 block">
                Zero Data Leakage • Test R²=0.85
              </span>
            </div>

          </div>

          {/* Forecast Chart */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
              <div>
                <h3 className="text-base font-bold text-slate-900">
                  Recursive Daily Demand Projection
                </h3>
                <p className="text-xs text-slate-500">
                  Timeline from {forecastData.forecast_start} to {forecastData.forecast_end}
                </p>
              </div>
              <span className="text-xs font-semibold px-2.5 py-1 rounded bg-teal-50 text-teal-800 border border-teal-200 self-start sm:self-auto">
                {forecastData.medicine} • {forecastData.days} Days
              </span>
            </div>

            <div className="h-72 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={forecastData.forecast} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
                  <defs>
                    <linearGradient id="forecastFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0d9488" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#0d9488" stopOpacity={0.0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                  <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} tickLine={false} />
                  <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#ffffff', 
                      borderColor: '#e2e8f0', 
                      borderRadius: '8px', 
                      fontSize: '12px',
                      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.07)'
                    }}
                    formatter={(val) => [`${val} units`, 'Demand']}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="predicted_demand" 
                    stroke="#0d9488" 
                    strokeWidth={2.5} 
                    fill="url(#forecastFill)" 
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Daily Forecast Breakdown Table */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <TableIcon className="w-4 h-4 text-teal-600" />
                Daily Schedule Breakdown
              </h3>
              <span className="text-xs text-slate-500 font-mono">
                {forecastData.forecast.length} days forecasted
              </span>
            </div>

            <div className="overflow-x-auto border border-slate-200 rounded-lg">
              <table className="w-full text-left text-xs text-slate-700">
                <thead className="bg-slate-50 text-slate-600 uppercase tracking-wider text-[11px] border-b border-slate-200">
                  <tr>
                    <th className="py-2.5 px-4 font-semibold">Forecast Date</th>
                    <th className="py-2.5 px-4 font-semibold">Medicine</th>
                    <th className="py-2.5 px-4 font-semibold text-right">Predicted Demand</th>
                    <th className="py-2.5 px-4 font-semibold text-right">Est. Daily Sales ($)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {forecastData.forecast.map((row) => (
                    <tr key={row.date} className="hover:bg-slate-50/70 transition">
                      <td className="py-2.5 px-4 font-mono text-slate-600">{row.date}</td>
                      <td className="py-2.5 px-4 font-medium text-slate-900">{forecastData.medicine}</td>
                      <td className="py-2.5 px-4 text-right font-mono font-bold text-teal-700">
                        {row.predicted_demand.toLocaleString()} units
                      </td>
                      <td className="py-2.5 px-4 text-right font-mono text-slate-600">
                        ${(row.predicted_demand * forecastData.unit_price).toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

          </div>

        </div>
      )}

      {/* Shop Forecast Audit History */}
      {historyList.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <History className="w-4 h-4 text-teal-600" />
              Recent Forecast History (Isolated Shop Log)
            </h3>
            <span className="text-[11px] text-slate-500 font-mono">
              Last {historyList.length} runs
            </span>
          </div>

          <div className="overflow-x-auto border border-slate-200 rounded-lg">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-slate-600 uppercase tracking-wider text-[11px] border-b border-slate-200">
                <tr>
                  <th className="py-2 px-3.5 font-semibold">Medicine</th>
                  <th className="py-2 px-3.5 font-semibold">Horizon</th>
                  <th className="py-2 px-3.5 font-semibold text-right">Predicted Volume</th>
                  <th className="py-2 px-3.5 font-semibold">Algorithm</th>
                  <th className="py-2 px-3.5 font-semibold text-right">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {historyList.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/70 transition">
                    <td className="py-2 px-3.5 font-medium text-slate-900">{item.medicine_name}</td>
                    <td className="py-2 px-3.5 text-slate-600">{item.forecast_horizon} Days</td>
                    <td className="py-2 px-3.5 text-right font-mono font-bold text-teal-700">
                      {item.predicted_demand?.toLocaleString()} units
                    </td>
                    <td className="py-2 px-3.5 text-slate-500 text-[11px]">{item.model_identifier}</td>
                    <td className="py-2 px-3.5 text-right text-slate-400 font-mono text-[10px]">
                      {item.forecast_generation_date}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

    </div>
  );
}
