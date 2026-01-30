"""
Script pour calculer les retards réels en faisant heure réelle - heure prévue.
En fusionnant GTFS statique (horaires théoriques) et GTFS-RT (horaires réels)
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta # Pour manipuler les dates et heures

BASE_DIR = Path(__file__).resolve().parent.parent.parent # Pour être sur dêtre a la Racine du projet

def load_gtfs_static():
    print("Chargement des horaires théoriques (GTFS statique)...")
    gtfs_dir = Path("data/raw/gtfs")
    # Charger stop_times (horaires théoriques)
    stop_times = pd.read_csv(gtfs_dir / "stop_times.txt")
    print(f"  ✅ {len(stop_times)} horaires théoriques chargés")

    return stop_times

def load_gtfs_rt_parsed():
    print("Chargement des horaires réels (GTFS-RT)...")
    df = pd.read_csv("data/processed/gtfs_rt_parsed.csv")
    print(f"  ✅ {len(df)} passages temps réel chargés")
    return df


def parse_gtfs_time(time_str):
    """
    Convertit un horaire GTFS (format HH:MM:SS) en secondes depuis minuit
    Gère les heures supérieur à 24 (ex : 25:30:00 = 01:30:00 le lendemain)
    """
    if pd.isna(time_str): #verifie si c'est vide
        return None
    parts = time_str.split(':') #découpage de l'horaire avec :
    heures = int(parts[0])
    minutes = int(parts[1])
    secondes = int(parts[2])
    # Convertir en secondes depuis minuit
    total_secondes = heures * 3600 + minutes * 60 + secondes
    
    return total_secondes

def calculate_delays(stop_times, gtfs_rt):
    """
    Calcule les retards en comparant horaires théoriques vs réels
    """
    print("\n Calcul des retards...")
   
    # Convertir les horaires théoriques en secondes EX : "25:30:00" -> 91800 secondes
    print("  → Conversion des horaires théoriques...")
    stop_times['arrival_time_seconds'] = stop_times['arrival_time'].apply(parse_gtfs_time)
    stop_times['departure_time_seconds'] = stop_times['departure_time'].apply(parse_gtfs_time)
    #ici on garde que les colonnes utiles
    stop_times_col = stop_times[['trip_id', 'stop_id', 'arrival_time', 'arrival_time_seconds', 'departure_time_seconds']].copy()
    # Fusion sur trip_id et stop_id
    print("  → Fusion GTFS statique + GTFS-RT...")
    merged = gtfs_rt.merge(
        stop_times_col,
        on=['trip_id', 'stop_id'],
        how='left'
    )
    print(f"✅ {len(merged)} passages fusionnés")
    
### CALCUL DES RETARDS RÉELS : Convertir les timestamps Unix en secondes depuis minuit
    print("  → Calcul des retards (heure réelle - heure théorique)...")
    merged['collecte_datetime'] = pd.to_datetime(merged['collecte_timestamp'])
    merged['jour'] = merged['collecte_datetime'].dt.date
        
    def unix_en_seconde_depuis_minuit(unix_timestamp, date):
        """Convertit un timestamp Unix en secondes depuis minuit (heure locale France)"""
        if pd.isna(unix_timestamp):
            return None
        
        # Convertir en datetime avec fuseau horaire Europe/Paris
        dt = pd.to_datetime(unix_timestamp, unit='s', utc=True).tz_convert('Europe/Paris')
        return dt.hour * 3600 + dt.minute * 60 + dt.second
    
    # Appliquer la conversion a chaque ligne
    merged['arrival_time_real_seconds'] = merged.apply(
        lambda row: unix_en_seconde_depuis_minuit(row['arrival_time_unix'], row['jour']) 
        if pd.notna(row['arrival_time_unix']) else None, 
        axis=1
    )
    
#Retard en secondes
    merged['delay_seconds'] = merged['arrival_time_real_seconds'] - merged['arrival_time_seconds']
#Retard en minutes
    merged['delay_minutes'] = merged['delay_seconds'] / 60   

    retards_calcules = merged['delay_minutes'].notna().sum()
    print(f"  ✅ {retards_calcules} retards calculés avec succès")
    
    if retards_calcules > 0:
        print(f"\n📊 STATISTIQUES DES RETARDS :")
        print(f"  Retard moyen : {merged['delay_minutes'].mean():.2f} minutes")
        print(f"  Retard médian : {merged['delay_minutes'].median():.2f} minutes")
        print(f"  Retard max : {merged['delay_minutes'].max():.2f} minutes")
        print(f"  Retard min : {merged['delay_minutes'].min():.2f} minutes")
        print(f"  Écart-type : {merged['delay_minutes'].std():.2f} minutes")
    
    return merged



def main():
    """
    Fonction principale
    """
    print("="*60)
    print("🚀 CALCUL DES RETARDS RÉELS")
    print("="*60)
    
    # Charger les données
    stop_times = load_gtfs_static()
    gtfs_rt = load_gtfs_rt_parsed()
    # Calculer les retards
    result = calculate_delays(stop_times, gtfs_rt)
    # Sauvegarder
    output_file = Path("data/processed/delays_calculated.csv")
    result.to_csv(output_file, index=False)
    print(f"\n💾 Résultats sauvegardés : {output_file}")
    # Afficher les premières lignes
    print("\n👀 Aperçu des données :")
    print(result[['trip_id', 'stop_id', 'arrival_time', 'collecte_timestamp']].head(10))

if __name__ == "__main__":
    main()