"""
Model Training Module for Medicine Demand Forecasting.

Loads chronological model-ready features, performs time-series train/validation/test split,
fits Linear Regression (baseline), Random Forest Regressor, and XGBoost Regressor,
and serializes models and preprocessing metadata to ml/models/.
"""

import os
import sys
import json
from typing import Dict, Any, Tuple, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import numpy as np
import pandas as pd
import joblib

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor


def load_model_data(file_path: str = "dataset/model_ready_data.csv") -> pd.DataFrame:
    """Load model-ready dataset with chronological date parsing."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Model-ready dataset not found at {file_path}")
    df = pd.read_csv(file_path)
    df["Date"] = pd.to_datetime(df["Date"])
    # Strictly sort by Date and Medicine
    return df.sort_values(by=["Date", "Medicine"]).reset_index(drop=True)


def time_series_split(
    df: pd.DataFrame,
    val_cutoff: str = "2024-05-01",
    test_cutoff: str = "2024-09-01",
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform chronological split without shuffling to strictly prevent future lookahead bias:
    - Train: Start to < val_cutoff (2022-01-31 to 2024-04-30, ~77%)
    - Validation: val_cutoff to < test_cutoff (2024-05-01 to 2024-08-31, ~11.5%)
    - Test: >= test_cutoff (2024-09-01 to 2024-12-31, ~11.5%)
    """
    train_df = df[df["Date"] < val_cutoff].copy()
    val_df = df[(df["Date"] >= val_cutoff) & (df["Date"] < test_cutoff)].copy()
    test_df = df[df["Date"] >= test_cutoff].copy()

    return train_df, val_df, test_df


def get_feature_and_target_matrices(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    target_col: str = "Quantity_Sold",
    metadata_cols: List[str] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, List[str], StandardScaler]:
    """
    Extract feature matrices and scale features using scaler fitted ONLY on the training split.
    """
    if metadata_cols is None:
        metadata_cols = ["Date", "Medicine", "Medicine_Category", "Season"]

    feature_cols = [c for c in train_df.columns if c not in metadata_cols and c != target_col]

    X_train_raw = train_df[feature_cols].values
    y_train = train_df[target_col].values

    X_val_raw = val_df[feature_cols].values
    y_val = val_df[target_col].values

    X_test_raw = test_df[feature_cols].values
    y_test = test_df[target_col].values

    # Fit scaler strictly on training data
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_raw)
    X_val_scaled = scaler.transform(X_val_raw)
    X_test_scaled = scaler.transform(X_test_raw)

    return (
        X_train_raw, X_train_scaled, y_train,
        X_val_raw, X_val_scaled, y_val,
        X_test_raw, X_test_scaled, y_test,
        feature_cols, scaler
    )


def train_models(
    X_train_scaled: np.ndarray,
    X_train_raw: np.ndarray,
    y_train: np.ndarray,
    X_val_scaled: np.ndarray,
    X_val_raw: np.ndarray,
    y_val: np.ndarray,
) -> Dict[str, Any]:
    """
    Train Linear Regression (on scaled inputs), Random Forest, and XGBoost regressors.
    """
    models = {}

    print("Training 1/3: Linear Regression (Baseline)...")
    lr = LinearRegression()
    lr.fit(X_train_scaled, y_train)
    models["linear_regression"] = {
        "model": lr,
        "uses_scaled": True,
        "display_name": "Linear Regression",
    }

    print("Training 2/3: Random Forest Regressor...")
    rf = RandomForestRegressor(
        n_estimators=100,
        max_depth=16,
        min_samples_split=4,
        random_state=42,
        n_jobs=-1,
    )
    rf.fit(X_train_raw, y_train)
    models["random_forest"] = {
        "model": rf,
        "uses_scaled": False,
        "display_name": "Random Forest",
    }

    print("Training 3/3: XGBoost Regressor...")
    xgb = XGBRegressor(
        n_estimators=150,
        learning_rate=0.05,
        max_depth=5,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42,
        n_jobs=-1,
    )
    xgb.fit(
        X_train_raw, y_train,
        eval_set=[(X_val_raw, y_val)],
        verbose=False,
    )
    models["xgboost"] = {
        "model": xgb,
        "uses_scaled": False,
        "display_name": "XGBoost Regressor",
    }

    return models


def save_models_and_artifacts(
    models: Dict[str, Any],
    scaler: StandardScaler,
    feature_cols: List[str],
    df: pd.DataFrame,
    output_dir: str = "ml/models",
):
    """Serialize trained models and preprocessing metadata."""
    os.makedirs(output_dir, exist_ok=True)

    # Save individual models
    for key, item in models.items():
        model_path = os.path.join(output_dir, f"{key}.pkl")
        joblib.dump(item["model"], model_path)
        print(f"Saved {item['display_name']} -> {model_path}")

    # Build and save preprocessing metadata
    unique_meds = sorted(df["Medicine"].unique())
    unique_cats = sorted(df["Medicine_Category"].unique())
    season_mapping = {"Winter": 0, "Spring": 1, "Summer": 2, "Monsoon": 3, "Autumn": 4}

    preprocessing_artifact = {
        "scaler": scaler,
        "feature_columns": feature_cols,
        "medicine_mapping": {med: idx for idx, med in enumerate(unique_meds)},
        "category_mapping": {cat: idx for idx, cat in enumerate(unique_cats)},
        "season_mapping": season_mapping,
        "medicines": unique_meds,
        "categories": unique_cats,
        "train_range": "2022-01-31 to 2024-04-30",
        "val_range": "2024-05-01 to 2024-08-31",
        "test_range": "2024-09-01 to 2024-12-31",
    }
    prep_path = os.path.join(output_dir, "preprocessing.pkl")
    joblib.dump(preprocessing_artifact, prep_path)
    print(f"Saved Preprocessing Artifacts -> {prep_path}")


def run_training_pipeline(
    data_path: str = "dataset/model_ready_data.csv",
    output_dir: str = "ml/models",
) -> Tuple[Dict[str, Any], Tuple]:
    """Execute complete chronological training pipeline."""
    print("=" * 65)
    print("PHASE 6: MACHINE LEARNING MODEL TRAINING")
    print("=" * 65)
    df = load_model_data(data_path)
    print(f"Loaded {len(df):,} chronological records from {data_path}")

    train_df, val_df, test_df = time_series_split(df)
    print(f"Chronological Splits:")
    print(f" - Train:      {len(train_df):,} records ({train_df['Date'].min().strftime('%Y-%m-%d')} to {train_df['Date'].max().strftime('%Y-%m-%d')})")
    print(f" - Validation: {len(val_df):,} records ({val_df['Date'].min().strftime('%Y-%m-%d')} to {val_df['Date'].max().strftime('%Y-%m-%d')})")
    print(f" - Test:       {len(test_df):,} records ({test_df['Date'].min().strftime('%Y-%m-%d')} to {test_df['Date'].max().strftime('%Y-%m-%d')})")

    (
        X_train_raw, X_train_scaled, y_train,
        X_val_raw, X_val_scaled, y_val,
        X_test_raw, X_test_scaled, y_test,
        feature_cols, scaler
    ) = get_feature_and_target_matrices(train_df, val_df, test_df)

    print(f"Features: {len(feature_cols)} predictor columns.")

    models = train_models(
        X_train_scaled, X_train_raw, y_train,
        X_val_scaled, X_val_raw, y_val,
    )

    save_models_and_artifacts(models, scaler, feature_cols, df, output_dir)
    print("All models successfully trained and serialized.")
    print("=" * 65)

    split_data = (
        X_train_raw, X_train_scaled, y_train,
        X_val_raw, X_val_scaled, y_val,
        X_test_raw, X_test_scaled, y_test,
        test_df, feature_cols
    )
    return models, split_data


if __name__ == "__main__":
    run_training_pipeline()
