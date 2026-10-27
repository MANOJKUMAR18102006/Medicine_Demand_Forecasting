import React from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  Calendar, 
  Activity, 
  Database,
  Layers,
  AlertTriangle
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

export default function AnalyticsTab({ summary, loading, error, onRetry }) {
  if (loading) {
    return (
      <div className="py-24 text-center space-y-3">
        <div className="w-8 h-8 border-2 border-teal-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
        <p className="text-sm text-slate-500 font-medium">Loading supply chain and data science analytics...</p>
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
          <h3 className="text-base font-bold text-slate-900">Analytics Unavailable</h3>
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

  const monthly_demand_summary = summary?.monthly_demand_summary || [];
  const medicine_wise_demand_summary = summary?.medicine_wise_demand_summary || [];
  const total_historical_records = summary?.total_historical_records ?? 0;
  const average_demand = summary?.average_demand ?? 0;

  // Day of week aggregated data
  const dowData = [
    { day: 'Mon', avg: 76.3 },
    { day: 'Tue', avg: 76.3 },
    { day: 'Wed', avg: 77.6 },
    { day: 'Thu', avg: 76.6 },
    { day: 'Fri', avg: 77.9 },
    { day: 'Sat', avg: 80.5, weekend: true },
    { day: 'Sun', avg: 82.2, weekend: true },
  ];

  // Seasonal aggregate data
  const seasonalData = [
    { season: 'Winter', avg: 80.5, desc: 'Flu & Cold surge' },
    { season: 'Spring', avg: 71.9, desc: 'Allergy peak' },
    { season: 'Summer', avg: 68.6, desc: 'ORS surge' },
    { season: 'Monsoon', avg: 88.5, desc: 'Infection surge' },
    { season: 'Autumn', avg: 75.3, desc: 'Steady baseline' },
  ];

  return (
    <div className="space-y-6">
      
      {/* Title */}
      <div className="pb-2">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">
          Consumption Analytics & Data Science Insights
        </h2>
        <p className="text-sm text-slate-500 mt-0.5">
          Exploratory analysis of 3-year historical demand patterns across temporal cycles, weather factors, and drug categories.
        </p>
      </div>

      {/* Analytics Header Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-1 shadow-xs">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Historical Dataset Records</span>
          <div className="text-2xl font-bold text-slate-900 font-mono">{total_historical_records.toLocaleString()}</div>
          <p className="text-xs text-slate-500">3 full calendar years (2022-2024)</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-1 shadow-xs">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Mean Demand (3-Year)</span>
          <div className="text-2xl font-bold text-teal-700 font-mono">
            {average_demand} <span className="text-sm font-normal text-slate-500 font-sans">units/day</span>
          </div>
          <p className="text-xs text-slate-500">Computed across 18 catalog drugs</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-1 shadow-xs">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Therapeutic Categories</span>
          <div className="text-2xl font-bold text-indigo-700 font-mono">12</div>
          <p className="text-xs text-slate-500">Analgesic, Antibiotic, Chronic, Antacid, etc.</p>
        </div>
      </div>

      {/* Grid 1: Medicine-wise Demand Comparison */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 space-y-4 shadow-xs">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-slate-900 text-base">Cumulative Demand by Pharmaceutical Drug</h3>
            <p className="text-xs text-slate-500">Total historical consumption units over 1,096 tracking days</p>
          </div>
          <span className="text-xs font-mono text-slate-600 px-2.5 py-1 rounded bg-slate-50 border border-slate-200">
            Total Units Sold
          </span>
        </div>

        <div className="h-80 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart 
              data={medicine_wise_demand_summary} 
              margin={{ top: 10, right: 10, left: -10, bottom: 40 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis 
                dataKey="medicine" 
                stroke="#64748b" 
                fontSize={10} 
                angle={-35} 
                textAnchor="end" 
                interval={0}
              />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#ffffff', 
                  borderColor: '#e2e8f0', 
                  borderRadius: '8px', 
                  fontSize: '12px',
                  boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.07)'
                }}
                formatter={(val) => [`${val.toLocaleString()} units`, 'Total Demand']}
              />
              <Bar dataKey="total_demand" fill="#0d9488" radius={[4, 4, 0, 0]}>
                {medicine_wise_demand_summary.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={index === 0 ? '#0f766e' : index < 3 ? '#0d9488' : index < 8 ? '#14b8a6' : '#94a3b8'} 
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Grid 2: Day of Week & Seasonal Dynamics Split */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Day of Week Pattern */}
        <div className="rounded-xl border border-slate-200 bg-white p-6 space-y-4 shadow-xs">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-slate-900 text-base">Day-of-Week Consumption Pattern</h3>
              <p className="text-xs text-slate-500">Weekday baseline vs elevated weekend OTC demand (+7.2%)</p>
            </div>
            <span className="text-xs font-medium px-2 py-0.5 rounded bg-teal-50 text-teal-800 border border-teal-200">
              Weekly Signal
            </span>
          </div>

          <div className="h-60 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dowData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="day" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} domain={[70, 85]} tickLine={false} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#ffffff', 
                    borderColor: '#e2e8f0', 
                    borderRadius: '8px', 
                    fontSize: '12px',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.07)'
                  }}
                  formatter={(val) => [`${val} units/day`, 'Avg Demand']}
                />
                <Bar dataKey="avg" radius={[4, 4, 0, 0]}>
                  {dowData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.weekend ? '#0284c7' : '#64748b'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Seasonal Patterns */}
        <div className="rounded-xl border border-slate-200 bg-white p-6 space-y-4 shadow-xs">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-slate-900 text-base">Seasonal Demand Dynamics</h3>
              <p className="text-xs text-slate-500">Peak infection periods: Monsoon (waterborne) and Winter (viral flu)</p>
            </div>
            <span className="text-xs font-medium px-2 py-0.5 rounded bg-indigo-50 text-indigo-800 border border-indigo-200">
              Seasonality
            </span>
          </div>

          <div className="h-60 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={seasonalData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="season" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} domain={[60, 95]} tickLine={false} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#ffffff', 
                    borderColor: '#e2e8f0', 
                    borderRadius: '8px', 
                    fontSize: '12px',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.07)'
                  }}
                  formatter={(val, name, item) => [`${val} units/day (${item.payload.desc})`, 'Avg Demand']}
                />
                <Bar dataKey="avg" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>

    </div>
  );
}
