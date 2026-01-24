from __future__ import annotations 

"""
prepare_dataset.py 
- Chargement des données
- Nettoyage Outliers
- Enrichissement GTFS
- Feature Engineering
- SÉPARATION STRATIFIÉE (Train/Test)
"""

import pandas as pd
import numpy as np
from pathlib import Path 
from sklearn.model_selection import train_test_split 


current_script_path = Path(__file__).resolve()
PROJECT_ROOT = current_script_path.parent.parent.parent 

DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
FINAL_DIR = DATA_DIR / "final"
GTFS_DIR = DATA_DIR / "raw" / "gtfs"

DELAYS_FILE = PROCESSED_DIR / "delays_calculated.csv"


def log(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def chargement_donnees(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"❌ Le fichier est introuvable : {path}")
    
    print(f"Chargement de {path.name}...")
    df = pd.read_csv(path)
    
    if "collecte_timestamp" not in df.columns:
        raise ValueError("Colonne 'collecte_timestamp' manquante !")
        
    df["collecte_datetime"] = pd.to_datetime(df["collecte_timestamp"], errors="coerce")
    

    df["delay_minutes"] = pd.to_numeric(df["delay_minutes"], errors="coerce")
    
    print(f"✅ Chargé : {len(df):,} lignes.")
    return df

def nettoyage_outliers(df: pd.DataFrame) -> pd.DataFrame:
    log("1. Nettoyage des données (Outliers)")
    before = len(df)
    

    mask = df["delay_minutes"].between(-10, 60)
    df = df.loc[mask].copy()
    
    removed = before - len(df)
    print(f"Lignes supprimées (valeurs extrêmes) : {removed:,}")
    return df

def enrichissement_gtfs(df: pd.DataFrame) -> pd.DataFrame:
    log("2. Enrichissement GTFS (Lignes & Arrêts)")
    
    try:
        if (GTFS_DIR / "trips.txt").exists():
            trips = pd.read_csv(GTFS_DIR / "trips.txt", usecols=["route_id", "trip_id"])
            routes = pd.read_csv(GTFS_DIR / "routes.txt", usecols=["route_id", "route_short_name"])
            stops = pd.read_csv(GTFS_DIR / "stops.txt", usecols=["stop_id", "stop_name", "stop_lat", "stop_lon"])
            
            df = df.merge(trips, on="trip_id", how="left")
            df = df.merge(routes, on="route_id", how="left")
            df = df.merge(stops, on="stop_id", how="left")
            
            print(f"✅ Données enrichies (Route, Arrêt, Lat/Lon).")
        else:
            print("⚠️ Fichiers GTFS manquants, on passe.")
            
    except Exception as e:
        print(f"⚠️ Erreur GTFS : {e}")
        
    return df

def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    log("3. Feature Engineering")
    
    df["hour"] = df["collecte_datetime"].dt.hour
    
    df["day_of_week"] = df["collecte_datetime"].dt.dayofweek 
    
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    
    df["is_peak_hour"] = df["hour"].isin([7, 8, 9, 12, 13, 17, 18, 19]).astype(int)
    
    df["period_of_day_matin"] = df["hour"].between(5, 10).astype(int)
    df["period_of_day_midi"] = df["hour"].between(11, 13).astype(int)
    df["period_of_day_apresmidi"] = df["hour"].between(14, 18).astype(int)
    df["period_of_day_soir"] = df["hour"].between(19, 23).astype(int)
    
    if "route_type" not in df.columns:
        df["route_type"] = 3
    else:
        
        df["route_type"] = pd.to_numeric(df["route_type"], errors='coerce').fillna(3)
    
    if "stop_id" in df.columns:
        stop_counts = df["stop_id"].value_counts(normalize=True)
        df["stop_freq"] = df["stop_id"].map(stop_counts)
    

    df = df.dropna(subset=["delay_minutes", "hour"])
    
    print("✅ Features créées : hour, day_of_week...")
    return df

def split_et_sauvegarde(df: pd.DataFrame) -> None:
    log("4. Séparation Train / Test (Stratifiée par Heure)")
  
    
    train_df, test_df = train_test_split(
        df, 
        test_size=0.2,      
        shuffle=True,       
        random_state=42,    
        stratify=df["hour"] 
    ) 

    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    
    train_path = FINAL_DIR / "train.csv"
    test_path = FINAL_DIR / "test.csv"
    
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    print(f"✂️  DIVISION EFFECTUÉE (80% / 20%)")
    print(f"   📂 Train set : {len(train_df):,} lignes")
    print(f"   📂 Test set  : {len(test_df):,} lignes")
    print("\n   ℹ️  Note : Split Stratifié sur l'heure (hour).")
    print("       La distribution des heures de pointe est identique dans Train et Test.")


def main():
    df = chargement_donnees(DELAYS_FILE)
    df = nettoyage_outliers(df)
    df = enrichissement_gtfs(df)
    df = feature_engineering(df)
    split_et_sauvegarde(df)
    
    log("✅ PRÉPARATION TERMINÉE AVEC SUCCÈS")

if __name__ == "__main__":
    main()