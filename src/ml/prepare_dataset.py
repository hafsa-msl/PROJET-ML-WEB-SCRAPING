import argparse
import pandas as pd
import numpy as np
from __future__ import annotations
from pathlib import Path

# Chemins
current_script_path = Path(__file__).resolve()
PROJECT_ROOT = current_script_path.parent.parent.parent

# On prend direct le dossier data à la racine
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
GTFS_DIR = DATA_DIR / "raw" / "gtfs" 
FINAL_DIR = DATA_DIR / "final"
DELAYS_FILE = PROCESSED_DIR / "delays_calculated.csv"

def log(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def chargement_delays(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable: {path}")
    log("Chargement delays_calculated.csv")
    df = pd.read_csv(path)
    print(f"✅ Lignes: {len(df):,}")
    print(f"✅ Colonnes: {len(df.columns)}")
    print("✅ Colonnes disponibles:", list(df.columns))

    if "collecte_timestamp" not in df.columns:
        raise ValueError("Colonne manquante: 'collecte_timestamp'")
    df["collecte_datetime"] = pd.to_datetime(df["collecte_timestamp"], errors="coerce")
    df["jour"] = df["collecte_datetime"].dt.date

    if "delay_minutes" not in df.columns: # Conversion en numérique
        raise ValueError("Colonne manquante: 'delay_minutes' (cible ML)")
    df["delay_minutes"] = pd.to_numeric(df["delay_minutes"], errors="coerce")

    return df


def bilan_qualite(df: pd.DataFrame) -> None:
    log("Contrôle de la qualité des données")
    key_cols = ["trip_id", "stop_id", "arrival_time", "collecte_timestamp", "collecte_datetime", "delay_minutes"] # recherche des valeurs manquantes sur les colonnes importantes
    existing = [c for c in key_cols if c in df.columns]
    na_counts = df[existing].isna().sum().sort_values(ascending=False)
    print("\n🧩 Valeurs manquantes :")
    for col, n in na_counts.items():
        pct = (n / len(df)) * 100 if len(df) else 0
        print(f" - {col:20s}: {n:>8,}  ({pct:>5.2f}%)")

    s = df["delay_minutes"].dropna()
    if len(s) == 0:
        print("\n Aucune valeur non-NA pour delay_minutes.")
        return
    print("\n Statistiques delay_minutes :")
    print(f" - count  : {len(s):,}")
    print(f" - mean   : {s.mean():.2f} min")
    print(f" - median : {s.median():.2f} min")
    print(f" - min    : {s.min():.2f} min")
    print(f" - max    : {s.max():.2f} min")
    print(f" - std    : {s.std():.2f} min")

#Indicateur pour le retard
    neg = (s < 0).mean() * 100
    over5 = (s > 5).mean() * 100
    over10 = (s > 10).mean() * 100
    over60 = (s > 60).mean() * 100
    print("\n Indicateurs :")
    print(f" - % en avance (delay < 0)  : {neg:.2f}%")
    print(f" - % retard > 5 min         : {over5:.2f}%")
    print(f" - % retard > 10 min        : {over10:.2f}%")
    print(f" - % retard > 60 min        : {over60:.2f}%")

 # Couverture temporelle
    dt = df["collecte_datetime"].dropna()
    if len(dt):
        print("\n Couverture collecte :")
        print(f" - début : {dt.min()}")
        print(f" - fin   : {dt.max()}")
        print(f" - jours : {df['jour'].nunique()}")
    print("\n Exemple (5 lignes) :")
    cols_preview = [c for c in ["trip_id", "stop_id", "arrival_time", "delay_minutes", "collecte_timestamp"] if c in df.columns]
    print(df[cols_preview].head(5))


# La fonction qui suit supprime les lignes aberrantes. On ne garde que les bus ayant entre 10 min d'avance et 60 min de retard. 
def filtrage_extreme(df: pd.DataFrame, min_delay: float = -10.0, max_delay: float = 60.0) -> pd.DataFrame:
    """
    Filtre les retards extrêmes (incidents / valeurs aberrantes) pour un apprentissage ML plus stable.
    On garde uniquement min_delay <= delay_minutes <= max_delay
    """
    log(f"Filtrage outliers: delay_minutes ∈ [{min_delay}, {max_delay}]")
    before = len(df)
    mask = df["delay_minutes"].between(min_delay, max_delay)
    df_f = df.loc[mask].copy()
    after = len(df_f) 

    removed = before - after
    pct_removed = (removed / before) * 100 if before else 0
    print(f"Avant : {before:,} lignes")
    print(f"Après : {after:,} lignes")
    print(f"Supprimées : {removed:,} ({pct_removed:.2f}%)")
# Stat après filtrage
    s = df_f["delay_minutes"]
    print("\n Stats delay_minutes APRÈS filtrage :")
    print(f" - mean   : {s.mean():.2f} min")
    print(f" - median : {s.median():.2f} min")
    print(f" - min    : {s.min():.2f} min")
    print(f" - max    : {s.max():.2f} min")
    print(f" - std    : {s.std():.2f} min")

    return df_f

#Ici on cherche les tables GTFS statiques nécessaires pour l'enrichissement des données. Et on les renomme avec panda. 
def chargement_tables_gtfs(gtfs_dir: Path):
    """
    Charge les tables GTFS statiques nécessaires à l'enrichissement:
    - trips.txt  (trip -> route_id)
    - routes.txt (route -> route_short_name, route_type)
    - stops.txt  (stop -> stop_name, stop_lat, stop_lon) #stop lon et lat ca veut dire la longitude et la latitude de l'arrêt 
    """
    log("Chargement GTFS statique (trips/routes/stops)")
    trips_path = gtfs_dir / "trips.txt"
    routes_path = gtfs_dir / "routes.txt"
    stops_path = gtfs_dir / "stops.txt"
    for p in [trips_path, routes_path, stops_path]:
        if not p.exists():
            raise FileNotFoundError(f"Fichier GTFS introuvable: {p}")

    trips = pd.read_csv(trips_path, usecols=["route_id", "trip_id"])
    routes = pd.read_csv(routes_path, usecols=["route_id", "route_short_name", "route_type"])
    stops = pd.read_csv(stops_path, usecols=["stop_id", "stop_name", "stop_lat", "stop_lon"])
    print(f"✅ trips  : {len(trips):,} lignes")
    print(f"✅ routes : {len(routes):,} lignes")
    print(f"✅ stops  : {len(stops):,} lignes")

    return trips, routes, stops


def enrichissement_gtfs(df: pd.DataFrame, trips: pd.DataFrame, routes: pd.DataFrame, stops: pd.DataFrame) -> pd.DataFrame:
    """
    Ajoute les infos GTFS statiques dans le dataset:
    - route_id, route_short_name, route_type
    - stop_name, stop_lat, stop_lon
    """
    log("Jointures GTFS (trip_id->route_id, route_id->routes, stop_id->stops)")
    before = len(df)
    # trip_id -> route_id
    df2 = df.merge(trips, on="trip_id", how="left")
    # route_id -> route_short_name, route_type
    df2 = df2.merge(routes, on="route_id", how="left")
    # stop_id -> stop_name, lat/lon
    df2 = df2.merge(stops, on="stop_id", how="left")
    print(f"Lignes avant/après jointures : {before:,} → {len(df2):,}")

# On contrôle NA sur colonnes ajoutées
    added_cols = ["route_id", "route_short_name", "route_type", "stop_name", "stop_lat", "stop_lon"]
    print("\n NA après jointures (colonnes ajoutées) :")
    for c in added_cols:
        n = df2[c].isna().sum()
        pct = (n / len(df2)) * 100 if len(df2) else 0
        print(f" - {c:16s}: {n:>8,} ({pct:>5.2f}%)") # ici on affiche le nombre et le pourcentage de valeurs manquantes pour chaque colonne ajoutée

    return df2

def feature_engineering_temporel(df: pd.DataFrame) -> pd.DataFrame:
    log("Feature engineering temporel") #feature c'est les variables utilisées pour faire des prédictions
    dt = df["collecte_datetime"]
    df["hour"] = dt.dt.hour
    df["day_of_week"] = dt.dt.dayofweek  # 0=lundi, 6=dimanche
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int) 
    # Heure de pointe : 7 à 9 et 17 à 19 (inclusif 7-9, 17-19)
    df["is_peak_hour"] = df["hour"].isin([7, 8, 9, 17, 18, 19]).astype(int)
# Période de la journée
    def period(h: int) -> str:
        if 0 <= h <= 5:
            return "nuit"
        elif 6 <= h <= 10:
            return "matin"
        elif 11 <= h <= 14:
            return "midi"
        elif 15 <= h <= 18:
            return "apres-midi"
        else:
            return "soir"
    df["period_of_day"] = df["hour"].apply(period)
    print("✅ Features ajoutées: hour, day_of_week, is_weekend, is_peak_hour, period_of_day")

    return df


def feature_engineering_trajet(df: pd.DataFrame) -> pd.DataFrame:
    log("Feature engineering trajet")
    if "stop_sequence" not in df.columns: #séquence c'est l'ordre des arrêts dans un trajet (du début jusqu'au terminus)
        print("⚠️ Colonne 'stop_sequence' absente : seq_norm ne peut pas être calculé.")
        return df
    # max stop_sequence par trip_id
    max_seq = df.groupby("trip_id")["stop_sequence"].transform("max") #on calcule la séquence maximale d'arrêt pour chaque trip_id
    df["seq_norm"] = df["stop_sequence"] / max_seq
    df["seq_norm"] = df["seq_norm"].fillna(0).clip(0, 1) #ici on remplit les valeurs manquantes avec 0 et on s'assure que les valeurs sont entre 0 et 1 car c'est une normalisation

    print("✅ Features ajoutées: seq_norm")
    return df

def encodage_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Encodage simple et robuste :
    - stop_id : frequency encoding (un nombre entre 0 et 1) 
    - route_short_name : one-hot #ce qui permet de transformer une variable catégorielle en plusieurs colonnes binaires
    - period_of_day : one-hot
    """
    log("Encodage des features")
    # Frequency encoding pour stop_id
    stop_freq = df["stop_id"].value_counts(normalize=True) #normalize=True pour avoir des fréquences entre 0 et 1
    df["stop_freq"] = df["stop_id"].map(stop_freq).astype(float) 
    # One-hot pour route_short_name et period_of_day
    cat_cols = []
    if "route_short_name" in df.columns:
        cat_cols.append("route_short_name")
    if "period_of_day" in df.columns:
        cat_cols.append("period_of_day")
    df_encoded = pd.get_dummies(df, columns=cat_cols, drop_first=False) #drop_first=False pour garder toutes les catégories
    print(f"✅ stop_freq ajouté + one-hot sur: {cat_cols}")
    print(f"✅ Nb colonnes après encodage: {len(df_encoded.columns)}")

    return df_encoded

def split_temporel(df: pd.DataFrame, train_ratio: float = 0.8):
    """
    Split temporel : on trie par collecte_datetime et on coupe à train_ratio.
    """
    log(" Split temporel train/test")
    df_sorted = df.sort_values("collecte_datetime").reset_index(drop=True)
    n = len(df_sorted)
    split_idx = int(n * train_ratio)
    train_df = df_sorted.iloc[:split_idx].copy()
    test_df = df_sorted.iloc[split_idx:].copy()
    split_date = df_sorted.loc[split_idx, "collecte_datetime"] if split_idx < n else df_sorted["collecte_datetime"].max()
    #sert à savoir la date de séparation entre train et test car on trie par date
    print(f"✅ Train : {len(train_df):,} lignes")
    print(f"✅ Test  : {len(test_df):,} lignes")
    print(f" Date de coupure approx : {split_date}")

    return train_df, test_df, split_date

def sauvegarde_datasets(train_df: pd.DataFrame, test_df: pd.DataFrame, out_dir: Path) -> None:
    log("💾 Sauvegarde des datasets finaux")
    out_dir.mkdir(parents=True, exist_ok=True)
    train_path = out_dir / "train.csv"
    test_path = out_dir / "test.csv"
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
    print(f"✅ Train sauvegardé : {train_path}")
    print(f"✅ Test  sauvegardé : {test_path}")

def rapport_couverture(df: pd.DataFrame, out_dir: Path | None = None) -> None:
    log("📋 Couverture du dataset (lignes/arrêts/temps)")
#Lignes (routes)
    by_route = (
        df.groupby("route_short_name")
          .agg(
              n=("delay_minutes", "size"),
              mean_delay=("delay_minutes", "mean"),
              median_delay=("delay_minutes", "median"),
              p_retard_5=("delay_minutes", lambda s: (s > 5).mean() * 100),)
          .sort_values("n", ascending=False))
    print("\n Top 15 lignes (route_short_name) :")
    print(by_route.head(15).to_string())
#Arrêts
    by_stop = (
        df.groupby(["stop_id", "stop_name"])
          .agg(
              n=("delay_minutes", "size"),
              mean_delay=("delay_minutes", "mean"),)
          .sort_values("n", ascending=False))
    print("\nTop 10 arrêts (par volume) :")
    print(by_stop.head(10).to_string())
#Répartition par jour et heure
    if "jour" in df.columns:
        by_day = df["jour"].value_counts().sort_index()
        print("\n Volume par jour :")
        print(by_day.to_string())

    if "hour" in df.columns:
        by_hour = df["hour"].value_counts().sort_index()
        print("\n Volume par heure :")
        print(by_hour.to_string())

# Sauvegarde optionnelle
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        by_route.to_csv(out_dir / "coverage_by_route.csv")
        by_stop.head(200).to_csv(out_dir / "coverage_top_stops.csv")
        if "jour" in df.columns:
            by_day.to_csv(out_dir / "coverage_by_day.csv")
        if "hour" in df.columns:
            by_hour.to_csv(out_dir / "coverage_by_hour.csv")
        print(f"\n Tableaux sauvegardés dans: {out_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prépare le dataset ML pour prédiction des retards Fil Bleu.")
    parser.add_argument("--input", type=str, default=str(DELAYS_FILE), help="Chemin du fichier delays_calculated.csv")
    args = parser.parse_args()
    input_path = Path(args.input)
    df = chargement_delays(input_path)
    bilan_qualite(df)
    # Étape 2 : filtrage outliers (incidents / valeurs extrêmes)
    df = filtrage_extreme(df, min_delay=-10, max_delay=60)
    # Étape 3 : jointures GTFS (enrichissement)
    trips, routes, stops = chargement_tables_gtfs(GTFS_DIR)
    df = enrichissement_gtfs(df, trips, routes, stops)
    # Étape 4 : features (temps + trajet)
    df = feature_engineering_temporel(df)
    df = feature_engineering_trajet(df)
    # Rapport de couverture (AVANT encodage pour rester lisible)
    rapport_couverture(df, out_dir=FINAL_DIR)
    # Étape 5 : encodage
    df = encodage_features(df)
    # Étape 6 : split temporel
    train_df, test_df, split_date = split_temporel(df, train_ratio=0.8)
    # Étape 7 : sauvegarde
    sauvegarde_datasets(train_df, test_df, FINAL_DIR)
    log("✅ Pipeline prepare_dataset terminé")

if __name__ == "__main__":
    main()