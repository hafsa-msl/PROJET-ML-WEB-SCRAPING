"""
train_model.py 
- Baseline (moyenne)
- LinearRegression
- RandomForestRegressor
- GradientBoostingRegressor (+ GridSearchCV léger)
"""


import json
import numpy as np
import pandas as pd
from __future__ import annotations # pour les annotations de type
from pathlib import Path # Chemins
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score # Métriques
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import GridSearchCV
import joblib # Sauvegarde modèle

# CHEMINS qu'on a pris dans prepare_dataset.py
PROJECT_ROOT = Path(".")
FINAL_DIR = PROJECT_ROOT / "data" / "final"
MODELS_DIR = PROJECT_ROOT / "models"
TRAIN_PATH = FINAL_DIR / "train.csv"
TEST_PATH = FINAL_DIR / "test.csv"

def log(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

# Chargement des données
def load_data():
    if not TRAIN_PATH.exists() or not TEST_PATH.exists():
        raise FileNotFoundError("train.csv ou test.csv introuvable. Lance prepare_dataset.py avant.")
    return pd.read_csv(TRAIN_PATH), pd.read_csv(TEST_PATH)

# Sélection de tous les features et de la variable cible
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
    X = df.drop(columns=cols_to_drop) # ici on garde tout sauf les colonnes à dropper cad features + target cad delay_minutes (target c'est ce qu'on veut prédire)
    y = df[target].astype(float) # ici on s'assure que y est float cad numérique
    X = X.apply(pd.to_numeric, errors="coerce").fillna(0).astype("float32") # Force en numérique (one-hot / bool / object)

    return X, y, X.columns.tolist()

# Calcul et affichage des métriques et de la variable à prédire 
def evaluate(y_true, y_pred, name: str) -> dict:
    mae = mean_absolute_error(y_true, y_pred) # Mean Absolute Error = moyenne des erreurs absolues
    rmse = mean_squared_error(y_true, y_pred) ** 0.5 # Root Mean Squared Error = racine carrée de la moyenne des erreurs au carré
    r2 = r2_score(y_true, y_pred)
    print(f"{name:>18s} | MAE: {mae:.3f} | RMSE: {rmse:.3f} | R²: {r2:.3f}")
    return {"model": name, "mae": mae, "rmse": rmse, "r2": r2}


def main():
    MODELS_DIR.mkdir(parents=True, exist_ok=True) # Crée le dossier models s'il n'existe pas
    log("Chargement train/test")
    train_df, test_df = load_data()
    print(f"Train: {len(train_df):,} | Test: {len(test_df):,}")
    log("Features / variable cible")
    X_train, y_train, feat_cols = select_features(train_df)
    X_test, y_test, _ = select_features(test_df)
    print(f"Nb features: {X_train.shape[1]}")
    results = []
    best_model = None
    best_name = None
    best_mae = float("inf")
    best_params = None
# Baseline
    log("Baseline - Modèle Naif")
    baseline_pred = np.full(shape=len(y_test), fill_value=y_train.mean())
    r = evaluate(y_test, baseline_pred, "baseline_moyenne")
    results.append(r)
# Régression Linéaire
    log("Régression Linéaire")
    lr = LinearRegression(n_jobs=-1)
    lr.fit(X_train, y_train)
    pred = lr.predict(X_test)
    r = evaluate(y_test, pred, "régression_linéaire")
    results.append(r)
    if r["mae"] < best_mae:
        best_mae, best_model, best_name, best_params = r["mae"], lr, "régression_linéaire", {}
# Forêt Aléatoire
    log("Forêt Aléatoire")
    rf = RandomForestRegressor(
        n_estimators=300,
        random_state=42,
        n_jobs=-1,
        min_samples_leaf=2,)
    rf.fit(X_train, y_train)
    pred = rf.predict(X_test)
    r = evaluate(y_test, pred, "forêt_aléatoire")
    results.append(r)
    if r["mae"] < best_mae:
        best_mae, best_model, best_name, best_params = r["mae"], rf, "forêt_aléatoire", {}

# Gradient Boosting + GridSearch léger (gridsearch pour trouver les meilleurs hyperparamètres)
    log("Gradient Boosting ( + GridSearch)") 
    gbr = GradientBoostingRegressor(random_state=42)
    param_grid = {
        "n_estimators": [200, 400],
        "learning_rate": [0.05, 0.1], # taux d'apprentissage
        "max_depth": [2, 3],}
    grid = GridSearchCV( #ici les meilleurs hyperparamètres sont cherchés via GridSearchCV
        estimator=gbr,
        param_grid=param_grid,
        scoring="neg_mean_absolute_error",
        cv=3,
        n_jobs=-1,
        verbose=1,)
    grid.fit(X_train, y_train)
    best_gbr = grid.best_estimator_
    pred = best_gbr.predict(X_test)
    r = evaluate(y_test, pred, "gradient_boosting")
    results.append(r)
    # Meilleur modèle ou non 
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
# Sauvegarde du meilleur modèle
    best_path = MODELS_DIR / "best_model.joblib"
    joblib.dump({"model": best_model, "features": feat_cols, "name": best_name}, best_path)
    print(f"✅ Best model : {best_path} ({best_name})")
# Sauvegarde des meilleurs hyperparamètres
    params_path = MODELS_DIR / "best_params.json"
    with open(params_path, "w", encoding="utf-8") as f:
        json.dump(best_params or {}, f, ensure_ascii=False, indent=2)
    print(f"✅ Best params : {params_path}")
# Résumé
    log("Résumé")
    print(metrics_df.to_string(index=False))

if __name__ == "__main__":
    main()
