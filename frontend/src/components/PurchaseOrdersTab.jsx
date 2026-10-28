import React, { useState, useEffect } from 'react';
import { 
  ClipboardList, 
  Truck, 
  CheckCircle2, 
  Clock, 
  XCircle, 
  RotateCcw, 
  Building2, 
  Package, 
  Calendar, 
  FileText, 
  ShieldCheck,
  CreditCard,
  MapPin,
  ArrowRight
} from 'lucide-react';
import { getPurchaseOrders, updatePurchaseOrderStatus } from '../services/api';

export default function PurchaseOrdersTab({ onStockUpdated }) {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(null);

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    setLoading(true);
    setError(null);
    const res = await getPurchaseOrders();
    if (res.ok) {
      setOrders(res.data);
    } else {
      setError(res.error);
    }
    setLoading(false);
  };

  const handleUpdateStatus = async (orderId, newStatus, notes) => {
    setActionLoading(orderId);
    const res = await updatePurchaseOrderStatus(orderId, newStatus, notes);
    setActionLoading(null);

    if (res.ok) {
      fetchOrders();
      if (onStockUpdated && newStatus === 'Delivered') {
        onStockUpdated();
      }
    } else {
      setError(res.error);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'Pending':
      case 'Confirmed':
        return 'bg-amber-50 text-amber-800 border-amber-200';
      case 'Processing':
        return 'bg-indigo-50 text-indigo-800 border-indigo-200';
      case 'Dispatched':
        return 'bg-blue-50 text-blue-800 border-blue-200';
      case 'Delivered':
        return 'bg-emerald-50 text-emerald-800 border-emerald-200';
      case 'Cancelled':
        return 'bg-slate-100 text-slate-600 border-slate-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <ClipboardList className="w-6 h-6 text-teal-600" />
            <span>Supplier Purchase Orders &amp; Receipts</span>
          </h2>
          <p className="text-sm text-slate-500 mt-0.5">
            Audit history of authorized wholesale orders, tracking dispatch, and physical stock intake.
          </p>
        </div>

        <button
          onClick={fetchOrders}
          disabled={loading}
          className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-2xs transition cursor-pointer self-start sm:self-auto"
        >
          <RotateCcw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-teal-600' : ''}`} />
          <span>Refresh Orders</span>
        </button>
      </div>

      {error && (
        <div className="p-3.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
          {error}
        </div>
      )}

      {loading ? (
        <div className="py-20 text-center space-y-3">
          <div className="w-8 h-8 border-2 border-teal-600 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-slate-500 font-medium">Loading purchase order audit records...</p>
        </div>
      ) : orders.length === 0 ? (
        <div className="py-16 text-center bg-white rounded-xl border border-slate-200 text-slate-500 text-xs shadow-xs space-y-2">
          <ClipboardList className="w-8 h-8 text-slate-300 mx-auto" />
          <p className="font-semibold text-slate-700">No purchase orders placed yet</p>
          <p>Browse the Medicine Marketplace to create purchase orders from authorized suppliers.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {orders.map((po) => (
            <div key={po.id} className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 space-y-4">
              
              {/* Order Meta Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                <div className="flex items-center gap-3 flex-wrap">
                  <span className="font-mono text-sm font-bold text-slate-900">{po.id}</span>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${getStatusBadge(po.status)}`}>
                    {po.status}
                  </span>
                  <span className="text-xs text-slate-500 font-medium flex items-center gap-1">
                    <Building2 className="w-3.5 h-3.5 text-slate-400" />
                    <span>{po.supplier_name}</span>
                  </span>
                </div>

                <div className="text-right text-xs text-slate-400 flex items-center gap-2">
                  {po.tracking_number && (
                    <span className="font-mono text-slate-600 bg-slate-50 px-2 py-0.5 rounded border border-slate-200">
                      Tracking: {po.tracking_number}
                    </span>
                  )}
                  <span>{po.created_at ? new Date(po.created_at).toLocaleDateString() : ''}</span>
                </div>
              </div>

              {/* Items Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-100 text-[11px] uppercase tracking-wider text-slate-400">
                      <th className="py-2 px-1">Medicine</th>
                      <th className="py-2 px-3">Formulation &amp; Strength</th>
                      <th className="py-2 px-3 text-right">Quantity</th>
                      <th className="py-2 px-3 text-right">Unit Price</th>
                      <th className="py-2 px-3 text-right">Line Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50 font-sans">
                    {po.items.map((item) => (
                      <tr key={item.id} className="hover:bg-slate-50/50">
                        <td className="py-2.5 px-1 font-semibold text-slate-900">{item.medicine_name}</td>
                        <td className="py-2.5 px-3 text-slate-500">{item.dosage_form || 'Tablets'} • {item.strength || 'Standard'}</td>
                        <td className="py-2.5 px-3 text-right font-mono font-bold text-teal-800">{item.quantity.toLocaleString()} units</td>
                        <td className="py-2.5 px-3 text-right font-mono text-slate-600">₹{item.unit_price.toFixed(2)}</td>
                        <td className="py-2.5 px-3 text-right font-mono font-bold text-slate-900">₹{item.total_price.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Order Footer & Actions */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-slate-100">
                <div className="text-xs text-slate-500 space-y-0.5">
                  <p>
                    <strong>Destination:</strong> {po.delivery_address}
                  </p>
                  <p>
                    <strong>Payment Terms:</strong> {po.payment_method} ({po.payment_status})
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <span className="text-[10px] text-slate-400 uppercase font-bold block">Total Amount</span>
                    <span className="text-lg font-bold text-teal-700 font-mono">₹{po.total_amount.toFixed(2)}</span>
                  </div>

                  {/* Delivery Confirmation Button */}
                  {po.status !== 'Delivered' && po.status !== 'Cancelled' && (
                    <button
                      type="button"
                      disabled={actionLoading === po.id}
                      onClick={() => handleUpdateStatus(po.id, 'Delivered', 'Shipment received, verified, and stocked.')}
                      className="px-3.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-2xs transition cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>{actionLoading === po.id ? 'Updating Stock...' : 'Confirm Delivery & Add Stock'}</span>
                    </button>
                  )}

                  {po.status === 'Delivered' && (
                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-lg">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      <span>Stock Added to Inventory</span>
                    </span>
                  )}

                  {po.status === 'Confirmed' && (
                    <button
                      type="button"
                      disabled={actionLoading === po.id}
                      onClick={() => handleUpdateStatus(po.id, 'Cancelled', 'Cancelled by shop owner.')}
                      className="px-2.5 py-1.5 rounded-lg border border-slate-200 text-slate-500 hover:text-rose-600 text-xs font-medium cursor-pointer"
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </div>

            </div>
          ))}
        </div>
      )}

    </div>
  );
}
