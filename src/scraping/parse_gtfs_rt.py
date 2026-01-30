"""
Script pour parser les fichiers GTFS-RT (Protocol Buffers)
Convertit les .bin en CSV exploitables
"""

from google.transit import gtfs_realtime_pb2
import pandas as pd
from pathlib import Path
from datetime import datetime
BASE_DIR = Path(__file__).resolve().parent.parent.parent
def parse_trip_updates_file(filepath):
    """
    Parse un fichier trip_updates .bin et retourne un DataFrame
    """
    feed = gtfs_realtime_pb2.FeedMessage()
    
    with open(filepath, 'rb') as f:
        feed.ParseFromString(f.read())
    
    data = []
    
    for entity in feed.entity:
        if entity.HasField('trip_update'):
            trip_update = entity.trip_update
            trip_id = trip_update.trip.trip_id
            
            for stop_time_update in trip_update.stop_time_update:
                stop_id = stop_time_update.stop_id
                
                # Récupérer les retards
                arrival_delay = None
                departure_delay = None
                arrival_time = None      
                departure_time = None    
                
                if stop_time_update.HasField('arrival'):
                    if hasattr(stop_time_update.arrival, 'delay'):
                        arrival_delay = stop_time_update.arrival.delay
                    if hasattr(stop_time_update.arrival, 'time'):  
                        arrival_time = stop_time_update.arrival.time
                
                if stop_time_update.HasField('departure'):
                    if hasattr(stop_time_update.departure, 'delay'):
                        departure_delay = stop_time_update.departure.delay
                    if hasattr(stop_time_update.departure, 'time'):  
                        departure_time = stop_time_update.departure.time
                
                data.append({
                    'trip_id': trip_id,
                    'stop_id': stop_id,
                    'arrival_delay_seconds': arrival_delay,
                    'departure_delay_seconds': departure_delay,
                    'arrival_delay_minutes': arrival_delay / 60 if arrival_delay is not None else None,
                    'departure_delay_minutes': departure_delay / 60 if departure_delay is not None else None,
                    'arrival_time_unix': arrival_time,      
                    'departure_time_unix': departure_time,  
                })
    
    return pd.DataFrame(data)

def parse_all_trip_updates():
    """
    Parse tous les fichiers trip_updates et les combine
    """
    gtfs_rt_dir = Path("data/raw/gtfs_rt")
    
    # Trouver tous les fichiers trip_updates
    files = sorted(gtfs_rt_dir.glob("trip_updates_*.bin"))
    
    if not files:
        print("❌ Aucun fichier trip_updates trouvé dans data/raw/gtfs_rt/")
        return None
    
    print(f"📁 {len(files)} fichiers trip_updates trouvés")
    
    all_data = []
    
    for i, filepath in enumerate(files, 1):
        print(f"Parsing {i}/{len(files)}: {filepath.name}")
        
        try:
            df = parse_trip_updates_file(filepath)
            
            # Extraire le timestamp du nom de fichier
            # Format: trip_updates_20251212_223805.bin
            timestamp_str = filepath.stem.replace('trip_updates_', '')
            timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
            df['collecte_timestamp'] = timestamp
            
            all_data.append(df)
            
        except Exception as e:
            print(f"⚠️ Erreur sur {filepath.name}: {e}")
            continue
    
    if not all_data:
        print("❌ Aucune donnée parsée avec succès")
        return None
    
    # Combiner tous les DataFrames
    combined_df = pd.concat(all_data, ignore_index=True)
    
    print(f"\n✅ Parsing terminé !")
    print(f" Total de passages collectés : {len(combined_df)}")
    
    return combined_df

def save_parsed_data(df):
    """
    Sauvegarde les données parsées en CSV
    """
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "gtfs_rt_parsed.csv"
    df.to_csv(output_file, index=False)
    
    print(f"Données sauvegardées : {output_file}")
    print(f"\n STATISTIQUES :")
    print(f"Nombre de passages : {len(df)}")
    
    # Compter combien de retards on a vraiment
    retards_non_nuls = df['arrival_delay_minutes'].notna().sum()
    print(f"Passages avec retards : {retards_non_nuls}")
    
    if retards_non_nuls > 0:
        print(f"Retard moyen : {df['arrival_delay_minutes'].mean():.2f} minutes")
        print(f"Retard max : {df['arrival_delay_minutes'].max():.2f} minutes")
        print(f"Retard min : {df['arrival_delay_minutes'].min():.2f} minutes")
    else:
        print("⚠️ Aucun retard trouvé dans les données")
    
    return output_file

if __name__ == "__main__":
    print(" Début du parsing des fichiers GTFS-RT\n")
    
    # Parser tous les fichiers
    df = parse_all_trip_updates()
    
    if df is not None:
        save_parsed_data(df)
        print("\n Aperçu des données :")
        print(df.head(10))
    else:
        print("\n❌ Échec du parsing")