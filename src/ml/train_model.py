"""
train_model.py (version M2)

- Baseline (moyenne)
- LinearRegression
- RandomForestRegressor
- GradientBoostingRegressor (+ GridSearchCV léger)
- (Optionnel) SVR sur sous-échantillon (sinon trop lent)

Entrées :
- data/final/train.csv
- data/final/test.csv

Sorties :
- models/best_model.joblib (modèle retenu)
- models/metrics.csv
- models/best_params.json (si GridSearch)
"""

from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import GridSearchCV
import joblib

current_script_path = Path(__file__).resolve()
PROJECT_ROOT = current_script_path.parent.parent.parent

# On pointe vers le dossier data à la racine
DATA_DIR = PROJECT_ROOT / "data"

# On définit le chemin vers le dossier final (à la racine)
FINAL_DIR = DATA_DIR / "final"
MODELS_DIR = PROJECT_ROOT / "models"

TRAIN_PATH = FINAL_DIR / "train.csv"
TEST_PATH = FINAL_DIR / "test.csv"




def log(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def load_data():
    if not TRAIN_PATH.exists() or not TEST_PATH.exists():
        raise FileNotFoundError("train.csv ou test.csv introuvable. Lance prepare_dataset.py avant.")
    return pd.read_csv(TRAIN_PATH), pd.read_csv(TEST_PATH)


def select_features(df: pd.DataFrame):
    target = "delay_minutes"

    drop_cols = [
        target,
        "trip_id", "stop_id", "stop_name", "route_id",
        "collecte_timestamp", "collecte_datetime", "jour",
        "arrival_time", "arrival_time_unix", "departure_time_unix",
        "delay_seconds", "arrival_time_real_seconds",
        "arrival_delay_seconds", "departure_delay_seconds",
        "arrival_delay_minutes", "departure_delay_minutes",
        "arrival_time_seconds", "departure_time_seconds",
    ]

    cols_to_drop = [c for c in drop_cols if c in df.columns]
    X = df.drop(columns=cols_to_drop)
    y = df[target].astype(float)

    # Forcer en numérique (one-hot / bool / object)
    X = X.apply(pd.to_numeric, errors="coerce").fillna(0).astype("float32")

    return X, y, X.columns.tolist()


def evaluate(y_true, y_pred, name: str) -> dict:
    mae = mean_absolute_error(y_true, y_pred)
    rmse = mean_squared_error(y_true, y_pred) ** 0.5
    r2 = r2_score(y_true, y_pred)
    print(f"{name:>18s} | MAE: {mae:.3f} | RMSE: {rmse:.3f} | R²: {r2:.3f}")
    return {"model": name, "mae": mae, "rmse": rmse, "r2": r2}


def main():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    log("📥 Chargement train/test")
    train_df, test_df = load_data()
    print(f"Train: {len(train_df):,} | Test: {len(test_df):,}")

    log("🧱 Features / cible")
    X_train, y_train, feat_cols = select_features(train_df)
    X_test, y_test, _ = select_features(test_df)
    print(f"Nb features: {X_train.shape[1]}")

    results = []
    best_model = None
    best_name = None
    best_mae = float("inf")
    best_params = None

    print("\n--- APERÇU DES DONNÉES (5 premières lignes) ---")
    print(X_train.head())

    # 1) Baseline
    log("📏 Baseline")
    baseline_pred = np.full(shape=len(y_test), fill_value=y_train.mean())
    r = evaluate(y_test, baseline_pred, "baseline_mean")
    results.append(r)

    # 2) Linear Regression
    log("📐 Linear Regression")
    lr = LinearRegression(n_jobs=-1)
    lr.fit(X_train, y_train)
    pred = lr.predict(X_test)
    r = evaluate(y_test, pred, "linear_regression")
    results.append(r)
    if r["mae"] < best_mae:
        best_mae, best_model, best_name, best_params = r["mae"], lr, "linear_regression", {}

    # 3) Random Forest
    log("🌲 Random Forest")
    rf = RandomForestRegressor(
        n_estimators=300,
        random_state=42,
        n_jobs=-1,
        min_samples_leaf=2,
    )
    rf.fit(X_train, y_train)
    pred = rf.predict(X_test)
    r = evaluate(y_test, pred, "random_forest")
    results.append(r)
    if r["mae"] < best_mae:
        best_mae, best_model, best_name, best_params = r["mae"], rf, "random_forest", {}

    # 4) Gradient Boosting + GridSearch (léger)
    # ⚠️ Important: GradientBoosting sklearn peut être un peu long, mais avec un grid petit ça passe.
    log("⚡ Gradient Boosting (GridSearch léger)")
    gbr = GradientBoostingRegressor(random_state=42)

    param_grid = {
        "n_estimators": [200, 400],
        "learning_rate": [0.05, 0.1],
        "max_depth": [2, 3],
    }

    grid = GridSearchCV(
        estimator=gbr,
        param_grid=param_grid,
        scoring="neg_mean_absolute_error",
        cv=3,
        n_jobs=-1,
        verbose=1,
    )
    grid.fit(X_train, y_train)
    best_gbr = grid.best_estimator_
    pred = best_gbr.predict(X_test)

    r = evaluate(y_test, pred, "gradient_boosting")
    results.append(r)

    if r["mae"] < best_mae:
        best_mae = r["mae"]
        best_model = best_gbr
        best_name = "gradient_boosting"
        best_params = grid.best_params_

    # Sauvegardes
    log("💾 Sauvegardes")
    metrics_df = pd.DataFrame(results).sort_values("mae")
    metrics_path = MODELS_DIR / "metrics.csv"
    metrics_df.to_csv(metrics_path, index=False)
    print(f"✅ Metrics : {metrics_path}")

    best_path = MODELS_DIR / "best_model.joblib"
    joblib.dump({"model": best_model, "features": feat_cols, "name": best_name}, best_path)
    print(f"✅ Best model : {best_path} ({best_name})")

    params_path = MODELS_DIR / "best_params.json"
    with open(params_path, "w", encoding="utf-8") as f:
        json.dump(best_params or {}, f, ensure_ascii=False, indent=2)
    print(f"✅ Best params : {params_path}")

    log("🏁 Résumé")
    print(metrics_df.to_string(index=False))

if __name__ == "__main__":
    main()
