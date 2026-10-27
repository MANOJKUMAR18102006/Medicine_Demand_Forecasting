import React, { useState, useEffect } from 'react';
import { 
  Cpu, 
  CheckCircle2, 
  Award, 
  HelpCircle, 
  AlertCircle
} from 'lucide-react';
import { getModelMetrics } from '../services/api';

export default function ModelPerformanceTab() {
  const [metricsData, setMetricsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      setLoading(true);
      const res = await getModelMetrics();
      if (res.ok) {
        setMetricsData(res.data);
      } else {
        setError(res.error);
      }
      setLoading(false);
    };
    fetchMetrics();
  }, []);

  if (loading) {
    return (
      <div className="py-24 text-center space-y-3">
        <div className="w-8 h-8 border-2 border-teal-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
        <p className="text-sm text-slate-500 font-medium">Loading model evaluation metrics...</p>
      </div>
    );
  }

  if (error || !metricsData) {
    return (
      <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-center gap-3">
        <AlertCircle className="w-5 h-5 shrink-0" />
        <span>{error || 'Unable to load model metrics.'}</span>
      </div>
    );
  }

  const { comparison, best_model, evaluation_period } = metricsData;

  return (
    <div className="space-y-6">
      
      {/* Title */}
      <div className="pb-2">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">
          Machine Learning Model Performance & Evaluation
        </h2>
        <p className="text-sm text-slate-500 mt-0.5">
          Comparative benchmarking across candidate regression models evaluated strictly out-of-time on holdout data.
        </p>
      </div>

      {/* Top Banner: Best Model Callout */}
      <div className="rounded-xl border border-teal-200 bg-teal-50/40 p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 shadow-xs">
        <div className="space-y-2 max-w-xl">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-xs font-semibold bg-teal-100 text-teal-800 border border-teal-300">
            <Award className="w-3.5 h-3.5 text-teal-700" /> Selected Production Model
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">{best_model.model_name}</h2>
          <p className="text-xs text-slate-600 leading-relaxed">
            Evaluated on an independent, strictly holdout chronological Test set ({evaluation_period?.test_start} to {evaluation_period?.test_end}, {evaluation_period?.test_records} records). Outperformed linear and tree benchmarks across MAE, RMSE, and R².
          </p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 w-full md:w-auto">
          <div className="p-3.5 rounded-lg bg-white border border-teal-200/80 text-center space-y-0.5 shadow-2xs">
            <span className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">Test MAE</span>
            <div className="text-lg font-bold text-slate-900 font-mono">{best_model.mae.toFixed(2)}</div>
            <span className="text-[10px] text-teal-700 font-medium">units</span>
          </div>

          <div className="p-3.5 rounded-lg bg-white border border-teal-200/80 text-center space-y-0.5 shadow-2xs">
            <span className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">Test RMSE</span>
            <div className="text-lg font-bold text-slate-900 font-mono">{best_model.rmse.toFixed(2)}</div>
            <span className="text-[10px] text-teal-700 font-medium">units</span>
          </div>

          <div className="p-3.5 rounded-lg bg-white border border-teal-200/80 text-center space-y-0.5 shadow-2xs">
            <span className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">R² Score</span>
            <div className="text-lg font-bold text-emerald-700 font-mono">{(best_model.r2 * 100).toFixed(1)}%</div>
            <span className="text-[10px] text-slate-500">variance exp.</span>
          </div>

          <div className="p-3.5 rounded-lg bg-white border border-teal-200/80 text-center space-y-0.5 shadow-2xs">
            <span className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">Safe MAPE</span>
            <div className="text-lg font-bold text-blue-700 font-mono">{best_model.mape.toFixed(2)}%</div>
            <span className="text-[10px] text-slate-500">relative err</span>
          </div>
        </div>
      </div>

      {/* Model Comparison Table */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 space-y-4 shadow-xs">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-slate-900 text-base">Model Benchmark on Holdout Test Split</h3>
            <p className="text-xs text-slate-500">
              Rigorous out-of-time evaluation with zero future lookahead bias
            </p>
          </div>
          <span className="text-xs font-mono text-slate-600 px-2.5 py-1 rounded bg-slate-50 border border-slate-200">
            Chronological Split
          </span>
        </div>

        <div className="overflow-x-auto border border-slate-200 rounded-lg">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-slate-600 uppercase tracking-wider text-[11px] border-b border-slate-200">
              <tr>
                <th className="py-3 px-4 font-semibold">Regression Model</th>
                <th className="py-3 px-4 font-semibold text-right">MAE (Units)</th>
                <th className="py-3 px-4 font-semibold text-right">RMSE (Units)</th>
                <th className="py-3 px-4 font-semibold text-right">R² Score</th>
                <th className="py-3 px-4 font-semibold text-right">Safe MAPE (%)</th>
                <th className="py-3 px-4 font-semibold text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {comparison.map((item) => {
                const isBest = item.model === best_model.model_name;
                return (
                  <tr key={item.model} className={`transition ${isBest ? 'bg-teal-50/40 font-medium' : 'hover:bg-slate-50/70'}`}>
                    <td className="py-3.5 px-4 text-slate-900 flex items-center gap-2">
                      <Cpu className="w-4 h-4 text-teal-600" />
                      <span className="font-medium">{item.model}</span>
                    </td>
                    <td className="py-3.5 px-4 text-right font-mono">{item.mae.toFixed(2)}</td>
                    <td className="py-3.5 px-4 text-right font-mono">{item.rmse.toFixed(2)}</td>
                    <td className="py-3.5 px-4 text-right font-mono text-emerald-700 font-semibold">
                      {item.r2.toFixed(4)}
                    </td>
                    <td className="py-3.5 px-4 text-right font-mono">{item.mape.toFixed(2)}%</td>
                    <td className="py-3.5 px-4 text-center">
                      {isBest ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[10px] font-semibold bg-teal-100 text-teal-800 border border-teal-300">
                          <CheckCircle2 className="w-3 h-3" /> Selected Best
                        </span>
                      ) : (
                        <span className="text-slate-400 text-[11px] font-normal">Benchmark</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Educational Explanations Section */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 space-y-4 shadow-xs">
        <h3 className="font-semibold text-slate-900 text-base flex items-center gap-2">
          <HelpCircle className="w-4 h-4 text-teal-600" />
          Evaluation Metrics Explained
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-slate-700">
          
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-1.5">
            <h4 className="font-bold text-teal-800">What does MAE (Mean Absolute Error) mean?</h4>
            <p className="text-slate-600 leading-relaxed">
              MAE measures the average magnitude of prediction errors in actual physical units (boxes of medicine). For XGBoost, an MAE of 12.68 means the predicted daily demand is, on average, within approximately 12 to 13 units of actual sales.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-1.5">
            <h4 className="font-bold text-teal-800">What does R² (Coefficient of Determination) mean?</h4>
            <p className="text-slate-600 leading-relaxed">
              R² represents the proportion of total variance in medicine demand explained by the engineered features (lags, rolling averages, seasonality, and calendar signals). An R² of 0.8486 indicates that ~84.9% of historical demand dynamics are captured by the model.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-1.5">
            <h4 className="font-bold text-teal-800">What does RMSE (Root Mean Squared Error) mean?</h4>
            <p className="text-slate-600 leading-relaxed">
              RMSE penalizes larger prediction discrepancies more heavily due to squaring. Comparing RMSE (17.67) to MAE (12.68) indicates that while occasional stochastic demand spikes occur, the model does not suffer from catastrophic over-prediction.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-1.5">
            <h4 className="font-bold text-teal-800">What does Safe MAPE mean?</h4>
            <p className="text-slate-600 leading-relaxed">
              MAPE calculates the average percentage error relative to actual demand. Standard MAPE fails on zero-demand days due to division by zero; our Safe MAPE protects zero denominators, yielding a realistic relative error rate of ~28.2%.
            </p>
          </div>

        </div>

      </div>

    </div>
  );
}
