from __future__ import annotations
import json
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
import time

from sklearn.model_selection import KFold, GridSearchCV
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


current_script_path = Path(__file__).resolve()
PROJECT_ROOT = current_script_path.parent.parent.parent

DATA_DIR = PROJECT_ROOT / "data"
FINAL_DIR = DATA_DIR / "final"
MODELS_DIR = PROJECT_ROOT / "models"


TRAIN_PATH = FINAL_DIR / "train.csv"
TEST_PATH = FINAL_DIR / "test.csv"

def log(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def prepare_data(df: pd.DataFrame):
    """
    Sépare les variables (X) de la cible (y).
    Utilise la liste d'exclusion de ta binôme + One-Hot Encoding.
    """
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
    
    actual_drop = [c for c in drop_cols if c in df.columns]
    X = df.drop(columns=actual_drop)
    y = df[target]

   
    if "route_short_name" in X.columns:
        X = pd.get_dummies(X, columns=["route_short_name"], prefix="ligne")
    
    X = X.apply(pd.to_numeric, errors="coerce").fillna(0).astype("float32")
    
    return X, y, X.columns.tolist()

def evaluer_modele(model, X_test, y_test, name):
    """
    Évaluation FINALE sur les données de test.
    """
    start_time = time.time()
    y_pred = model.predict(X_test)
    inference_time = time.time() - start_time
    
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    return {
        "model": name, 
        "mae": round(mae, 3), 
        "rmse": round(rmse, 3), 
        "r2": round(r2, 3),
        "time_sec": round(inference_time, 4)
    }

def main():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
<<<<<<< Updated upstream
    log("🚀 DÉMARRAGE DU MACHINE LEARNING ")

    if not TRAIN_PATH.exists() or not TEST_PATH.exists():
        raise FileNotFoundError("❌ Erreur : Fichiers manquants. Lance 'prepare_dataset.py' d'abord.")
=======
    log("DÉMARRAGE DU MACHINE LEARNING ")

    if not TRAIN_PATH.exists() or not TEST_PATH.exists():
        raise FileNotFoundError("Erreur : Fichiers manquants. Lance 'prepare_dataset.py' d'abord.")
>>>>>>> Stashed changes

    print("Chargement des fichiers séparés...")
    df_train = pd.read_csv(TRAIN_PATH)
    df_test = pd.read_csv(TEST_PATH)
    
    print(f"✅ TRAIN : {len(df_train):,} lignes (Pour apprendre et régler les paramètres)")
    print(f"🔒 TEST  : {len(df_test):,} lignes (Verrouillé jusqu'à la fin)")

    X_train, y_train, feat_cols = prepare_data(df_train)
    X_test, y_test, _ = prepare_data(df_test)
    
    X_test = X_test.reindex(columns=X_train.columns, fill_value=0)

    cv_strategy = KFold(n_splits=3, shuffle=True, random_state=42)
    
    results = []
    best_global_mae = float("inf")
    best_global_model = None
    best_global_name = ""
    best_global_params = {}

 # --- 1. Baseline ---
    log("1. Baseline (Moyenne)")
    mean_delay = y_train.mean()
    y_pred_base = np.full(len(y_test), mean_delay) 

    mae_base = mean_absolute_error(y_test, y_pred_base)
    rmse_base = np.sqrt(mean_squared_error(y_test, y_pred_base))


    print(f"   MAE: {mae_base:.2f} min | RMSE: {rmse_base:.2f} min")
    
    results.append({
        "model": "Baseline", 
        "mae": mae_base, 
        "rmse": rmse_base 
    })

    # --- 2. RÉGRESSION LINÉAIRE ---
    log("2. Régression Linéaire")
    lr = LinearRegression()
    lr.fit(X_train, y_train) 
    
    scores = evaluer_modele(lr, X_test, y_test, "LinearRegression")
    print(f"👉 MAE: {scores['mae']} min ")
    results.append(scores)
    
    if scores['mae'] < best_global_mae:
        best_global_mae = scores['mae']
        best_global_model = lr
        best_global_name = "LinearRegression"

    # --- 3. RANDOM FOREST (Avec Tuning sur TRAIN) ---
    log("3. Random Forest (GridSearch)")
    rf = RandomForestRegressor(random_state=42, n_jobs=-1)
    
    param_grid_rf = {
        "n_estimators": [50, 100],  
        "max_depth": [10, 20]       
    }
    
    print("⏳ Recherche des meilleurs paramètres")
    
    grid_rf = GridSearchCV(rf, param_grid_rf, cv=cv_strategy, scoring="neg_mean_absolute_error", n_jobs=-1)
    grid_rf.fit(X_train, y_train)
    
    best_rf = grid_rf.best_estimator_
    print(f"✅ Meilleurs paramètres trouvés : {grid_rf.best_params_}")
    
    scores = evaluer_modele(best_rf, X_test, y_test, "RandomForest")
<<<<<<< Updated upstream
    print(f"👉 MAE: {scores['mae']} min")
=======
    print(f"MAE: {scores['mae']} min")
>>>>>>> Stashed changes
    results.append(scores)

    if scores['mae'] < best_global_mae:
        best_global_mae = scores['mae']
        best_global_model = best_rf
        best_global_name = "RandomForest"
        best_global_params = grid_rf.best_params_

    # --- 4. GRADIENT BOOSTING ---
    log("4. Gradient Boosting (GridSearch)")
    gb = GradientBoostingRegressor(random_state=42)
    
    param_grid_gb = {
        "n_estimators": [100],
        "learning_rate": [0.1],
        "max_depth": [3, 5]
    }
    
    grid_gb = GridSearchCV(gb, param_grid_gb, cv=cv_strategy, scoring="neg_mean_absolute_error", n_jobs=-1)
    grid_gb.fit(X_train, y_train)
    best_gb = grid_gb.best_estimator_
    
    scores = evaluer_modele(best_gb, X_test, y_test, "GradientBoosting")
<<<<<<< Updated upstream
    print(f"👉 MAE: {scores['mae']} min")
=======
    print(f" MAE: {scores['mae']} min")
>>>>>>> Stashed changes
    results.append(scores)

    if scores['mae'] < best_global_mae:
        best_global_mae = scores['mae']
        best_global_model = best_gb
        best_global_name = "GradientBoosting"
        best_global_params = grid_gb.best_params_

    
<<<<<<< Updated upstream
    log("🏁 RÉSULTATS COMPARATIFS")
    df_results = pd.DataFrame(results).sort_values("mae")
    print(df_results[["model", "mae", "rmse"]].to_string(index=False))
    
    print(f"\n🏆 Le meilleur modèle est : {best_global_name.upper()}")
=======
    log(" RÉSULTATS COMPARATIFS")
    df_results = pd.DataFrame(results).sort_values("mae")
    print(df_results[["model", "mae", "rmse"]].to_string(index=False))
    
    print(f"\n Le meilleur modèle est : {best_global_name.upper()}")
>>>>>>> Stashed changes
    print(f"   Il se trompe en moyenne de {best_global_mae} minutes.")

  
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    df_results.to_csv(MODELS_DIR / "metrics.csv", index=False)

    joblib.dump({
        "model": best_global_model,
        "features": feat_cols,
        "name": best_global_name,
        "params": best_global_params
    }, MODELS_DIR / "best_model.joblib")
    
    
    with open(MODELS_DIR / "best_params.json", "w") as f:
        json.dump(best_global_params, f)

<<<<<<< Updated upstream
    print(f"\n💾 Modèle sauvegardé dans : models/best_model.joblib")
=======
    print(f"\n Modèle sauvegardé dans : models/best_model.joblib")
>>>>>>> Stashed changes

if __name__ == "__main__":
    main()