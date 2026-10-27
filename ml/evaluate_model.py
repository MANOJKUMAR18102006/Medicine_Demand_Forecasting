"""
Model Evaluation Module for Medicine Demand Forecasting.

Evaluates Linear Regression, Random Forest, and XGBoost models on the chronological holdout Test set.
Computes MAE, RMSE, R2, and Safe MAPE metrics.
Exports model comparison table, saves ml/models/model_metrics.json,
selects and persists ml/models/best_model.pkl, and generates Actual vs Predicted visualization.
"""

import os
import sys
import json
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from ml.train_model import load_model_data, time_series_split, get_feature_and_target_matrices


def safe_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate Mean Absolute Percentage Error (MAPE) safely by avoiding division by zero.
    Values of y_true < 1 are protected using denominator threshold max(y_true, 1.0).
    """
    y_true_safe = np.maximum(y_true, 1.0)
    return float(np.mean(np.abs((y_true - y_pred) / y_true_safe)) * 100.0)


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Compute MAE, RMSE, R2, and Safe MAPE."""
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = float(r2_score(y_true, y_pred))
    mape = safe_mape(y_true, y_pred)

    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "r2": round(r2, 4),
        "mape": round(mape, 2),
    }


def plot_actual_vs_predicted(
    test_df: pd.DataFrame,
    predictions: Dict[str, np.ndarray],
    y_true: np.ndarray,
    output_path: str = "reports/figures/09_actual_vs_predicted.png",
):
    """
    Generate comparison plot showing Actual vs Predicted demand on test set:
    1. Overall scatter plot with identity line.
    2. Chronological demand timeline for a representative medicine.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    sns.set_theme(style="whitegrid")

    fig, axes = plt.subplots(1, 2, figsize=(15, 6))

    # Left: Scatter Actual vs Predicted for XGBoost and Random Forest
    colors = {"Linear Regression": "#94a3b8", "Random Forest": "#10b981", "XGBoost Regressor": "#0ea5e9"}
    sample_indices = np.random.choice(len(y_true), size=min(800, len(y_true)), replace=False)

    for model_name, y_pred in predictions.items():
        axes[0].scatter(
            y_true[sample_indices],
            y_pred[sample_indices],
            label=model_name,
            alpha=0.45,
            s=22,
            color=colors.get(model_name, "#6366f1"),
        )

    # 45-degree reference line
    min_val = min(y_true[sample_indices].min(), min(p[sample_indices].min() for p in predictions.values()))
    max_val = max(y_true[sample_indices].max(), max(p[sample_indices].max() for p in predictions.values()))
    axes[0].plot([min_val, max_val], [min_val, max_val], color="red", linestyle="--", linewidth=1.5, label="Perfect Prediction (y=x)")
    axes[0].set_title("Actual vs Predicted Demand (Test Set Samples)")
    axes[0].set_xlabel("Actual Quantity Sold")
    axes[0].set_ylabel("Predicted Quantity Sold")
    axes[0].legend(loc="upper left")

    # Right: Timeline for a sample medicine (e.g. Paracetamol in test split)
    sample_med = "Paracetamol"
    med_mask = (test_df["Medicine"] == sample_med).values
    med_dates = test_df.loc[med_mask, "Date"].values
    med_actual = y_true[med_mask]

    axes[1].plot(med_dates, med_actual, label="Actual Demand", color="#0f172a", linewidth=2.0)
    for model_name, y_pred in predictions.items():
        if model_name in ["Random Forest", "XGBoost Regressor"]:
            axes[1].plot(
                med_dates,
                y_pred[med_mask],
                label=f"{model_name} Prediction",
                linestyle="--",
                linewidth=1.5,
                color=colors.get(model_name),
            )

    axes[1].set_title(f"Holdout Test Prediction Timeline: {sample_med} (Sep-Dec 2024)")
    axes[1].set_xlabel("Date")
    axes[1].set_ylabel("Daily Units Sold")
    axes[1].tick_params(axis="x", rotation=30)
    axes[1].legend(loc="upper right")

    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()
    print(f"Actual vs Predicted plot saved to {output_path}")


def run_evaluation_pipeline(
    data_path: str = "dataset/model_ready_data.csv",
    models_dir: str = "ml/models",
    reports_fig_dir: str = "reports/figures",
) -> Dict[str, Any]:
    """Load models, evaluate on chronological Test split, select best model, and save metrics."""
    print("=" * 65)
    print("PHASE 6: MODEL EVALUATION & SELECTION")
    print("=" * 65)

    # Load split data
    df = load_model_data(data_path)
    train_df, val_df, test_df = time_series_split(df)
    (
        _, _, _,
        _, _, _,
        X_test_raw, X_test_scaled, y_test,
        feature_cols, scaler
    ) = get_feature_and_target_matrices(train_df, val_df, test_df)

    # Load trained models
    model_configs = [
        ("linear_regression", "Linear Regression", True),
        ("random_forest", "Random Forest", False),
        ("xgboost", "XGBoost Regressor", False),
    ]

    metrics_list = []
    predictions_dict = {}
    loaded_models = {}

    for file_key, display_name, uses_scaled in model_configs:
        model_path = os.path.join(models_dir, f"{file_key}.pkl")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Trained model not found at {model_path}. Run train_model.py first.")
        
        model = joblib.load(model_path)
        loaded_models[file_key] = model

        # Predict
        X_eval = X_test_scaled if uses_scaled else X_test_raw
        y_pred = model.predict(X_eval)
        # Ensure zero-floor for physical demand
        y_pred = np.maximum(0.0, y_pred)
        predictions_dict[display_name] = y_pred

        perf = evaluate_predictions(y_test, y_pred)
        perf["model"] = display_name
        perf["file_key"] = file_key
        metrics_list.append(perf)

    # Determine best model based on lowest Test MAE and highest R2
    best_perf = min(metrics_list, key=lambda m: (m["mae"], -m["r2"]))
    best_file_key = best_perf["file_key"]
    best_model_obj = loaded_models[best_file_key]

    # Save best_model.pkl
    best_model_path = os.path.join(models_dir, "best_model.pkl")
    joblib.dump(best_model_obj, best_model_path)
    print(f"\nBest Model Selected: {best_perf['model']} (Test MAE: {best_perf['mae']}, R2: {best_perf['r2']})")
    print(f"Persisted best model -> {best_model_path}")

    # Build model_metrics.json structure
    metrics_payload = {
        "comparison": [
            {
                "model": m["model"],
                "mae": m["mae"],
                "rmse": m["rmse"],
                "r2": m["r2"],
                "mape": m["mape"],
            }
            for m in metrics_list
        ],
        "best_model": {
            "model_name": best_perf["model"],
            "file_key": best_perf["file_key"],
            "mae": best_perf["mae"],
            "rmse": best_perf["rmse"],
            "r2": best_perf["r2"],
            "mape": best_perf["mape"],
        },
        "evaluation_period": {
            "test_start": test_df["Date"].min().strftime("%Y-%m-%d"),
            "test_end": test_df["Date"].max().strftime("%Y-%m-%d"),
            "test_records": len(test_df),
        }
    }

    metrics_json_path = os.path.join(models_dir, "model_metrics.json")
    with open(metrics_json_path, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2)
    print(f"Saved metrics JSON -> {metrics_json_path}")

    # Print clean comparison table
    print("\n" + "-" * 65)
    print(f"{'Model':<22} | {'MAE':<7} | {'RMSE':<7} | {'R2':<7} | {'MAPE (%)'}")
    print("-" * 65)
    for m in metrics_list:
        star = " * (Best)" if m["model"] == best_perf["model"] else ""
        print(f"{m['model']:<22} | {m['mae']:<7.2f} | {m['rmse']:<7.2f} | {m['r2']:<7.4f} | {m['mape']:<7.2f}{star}")
    print("-" * 65)

    # Plot Actual vs Predicted
    chart_path = os.path.join(reports_fig_dir, "09_actual_vs_predicted.png")
    plot_actual_vs_predicted(test_df, predictions_dict, y_test, chart_path)

    print("=" * 65)
    return metrics_payload


if __name__ == "__main__":
    run_evaluation_pipeline()
