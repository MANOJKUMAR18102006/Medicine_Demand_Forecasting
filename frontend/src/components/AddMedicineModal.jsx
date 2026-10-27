import React, { useState } from 'react';
import { 
  Pill, 
  Plus, 
  X, 
  Layers, 
  DollarSign, 
  Boxes, 
  ShieldAlert, 
  Sparkles,
  AlertCircle,
  CheckCircle2
} from 'lucide-react';
import { createMedicine, seedStarterMedicines } from '../services/api';

const POPULAR_CATEGORIES = [
  'Analgesic / Antipyretic',
  'Antibiotic',
  'NSAID',
  'Antidiabetic',
  'Cardiovascular / Statin',
  'Cardiovascular / Antihypertensive',
  'Gastrointestinal',
  'Antihistamine',
  'Respiratory / Inhaler',
  'Corticosteroid',
  'Neuropathic',
  'General',
];

export default function AddMedicineModal({ onClose, onMedicineAdded }) {
  const [formData, setFormData] = useState({
    medicine_name: '',
    category: 'Analgesic / Antipyretic',
    unit_of_measurement: 'tablets',
    unit_price: 10.0,
    initial_stock: 500,
    safety_stock: 50,
    reorder_threshold: 150,
  });

  const [loading, setLoading] = useState(false);
  const [seedLoading, setSeedLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!formData.medicine_name.trim()) {
      setError('Please provide a medicine name.');
      return;
    }

    setLoading(true);
    const res = await createMedicine({
      medicine_name: formData.medicine_name.trim(),
      category: formData.category,
      unit_of_measurement: formData.unit_of_measurement,
      unit_price: Number(formData.unit_price),
      initial_stock: Number(formData.initial_stock),
      safety_stock: Number(formData.safety_stock),
      reorder_threshold: Number(formData.reorder_threshold),
    });
    setLoading(false);

    if (res.ok) {
      setSuccess(`Medicine '${formData.medicine_name}' added to your shop inventory!`);
      onMedicineAdded(formData.medicine_name.trim());
      setTimeout(() => {
        onClose();
      }, 1000);
    } else {
      setError(res.error);
    }
  };

  const handleSeedStarter = async () => {
    setError(null);
    setSuccess(null);
    setSeedLoading(true);
    const res = await seedStarterMedicines();
    setSeedLoading(false);

    if (res.ok) {
      setSuccess(res.data.message);
      onMedicineAdded('Paracetamol');
      setTimeout(() => {
        onClose();
      }, 1200);
    } else {
      setError(res.error);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4 font-sans">
      <div className="w-full max-w-lg bg-white rounded-2xl border border-slate-200 shadow-xl p-6 sm:p-7 space-y-5">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center border border-teal-100">
              <Pill className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">
                Add Medicine to Inventory
              </h3>
              <p className="text-xs text-slate-500">
                Register a new pharmaceutical drug into your shop catalog
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-500 hover:text-slate-800 flex items-center justify-center transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Notifications */}
        {error && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{success}</span>
          </div>
        )}

        {/* Starter catalog banner */}
        <div className="p-3.5 rounded-xl bg-teal-50/70 border border-teal-200 flex items-center justify-between gap-3 text-xs">
          <div>
            <div className="font-semibold text-teal-900 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-teal-600" />
              Quick Setup: Standard Pharmacy Catalog
            </div>
            <p className="text-[11px] text-teal-700 mt-0.5">
              Pre-load 18 top hospital drugs (Paracetamol, Amoxicillin, Insulin, etc.)
            </p>
          </div>
          <button
            type="button"
            disabled={seedLoading}
            onClick={handleSeedStarter}
            className="px-3 py-1.5 rounded-lg bg-teal-700 hover:bg-teal-800 text-white font-medium text-xs whitespace-nowrap shadow-xs disabled:opacity-60 transition cursor-pointer"
          >
            {seedLoading ? 'Loading...' : 'Import Catalog'}
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          
          {/* Medicine Name */}
          <div className="space-y-1">
            <label className="block text-xs font-semibold text-slate-700">
              Medicine Name *
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Paracetamol 500mg, Amoxicillin"
              value={formData.medicine_name}
              onChange={(e) => setFormData({ ...formData, medicine_name: e.target.value })}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500 text-slate-800"
            />
          </div>

          {/* Category & Unit of Measurement */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="block text-xs font-semibold text-slate-700">
                Therapeutic Category
              </label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500 text-slate-800 bg-white"
              >
                {POPULAR_CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>

            <div className="space-y-1">
              <label className="block text-xs font-semibold text-slate-700">
                Unit of Measurement
              </label>
              <select
                value={formData.unit_of_measurement}
                onChange={(e) => setFormData({ ...formData, unit_of_measurement: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500 text-slate-800 bg-white"
              >
                <option value="tablets">Tablets</option>
                <option value="capsules">Capsules</option>
                <option value="vials">Vials (Injectable)</option>
                <option value="bottles">Bottles (Syrup)</option>
                <option value="inhalers">Inhalers</option>
                <option value="strips">Strips</option>
                <option value="units">Units</option>
              </select>
            </div>
          </div>

          {/* Price & Initial Stock */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="space-y-1">
              <label className="block text-xs font-semibold text-slate-700">
                Unit Price ($)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                required
                value={formData.unit_price}
                onChange={(e) => setFormData({ ...formData, unit_price: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500 text-slate-800"
              />
            </div>

            <div className="space-y-1">
              <label className="block text-xs font-semibold text-slate-700">
                Current Stock (Units)
              </label>
              <input
                type="number"
                min="0"
                required
                value={formData.initial_stock}
                onChange={(e) => setFormData({ ...formData, initial_stock: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500 text-slate-800"
              />
            </div>

            <div className="space-y-1">
              <label className="block text-xs font-semibold text-slate-700">
                Safety Stock Buffer
              </label>
              <input
                type="number"
                min="0"
                required
                value={formData.safety_stock}
                onChange={(e) => setFormData({ ...formData, safety_stock: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500 text-slate-800"
              />
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg border border-slate-200 text-xs font-medium text-slate-600 hover:bg-slate-50 cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 rounded-lg bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold shadow-xs disabled:opacity-60 transition cursor-pointer"
            >
              {loading ? 'Adding...' : 'Add Medicine'}
            </button>
          </div>

        </form>

      </div>
    </div>
  );
}
