# 1️⃣ Les "Outils" (Imports)

📍 Rôle : Préparer les accessoires nécessaires au script.
- from google.transit import gtfs_realtime_pb2= permet de lire le langage binaire (le format .bin de Google)
- import pandas as pd= manipulation et nettoyage de données
- from pathlib import Path= enregistrer le chemin accès
- from datetime import datetime= sert à lire les dates et les heures

# Création de la fonction pour transfo .bin en .csv

- def parse_trip_updates_file(filepath):= fonction qui reçoit le chemin d'un seul fichier .bin (celui qui est dans filepath) et sa mission est de le transformer en un tableau (DataFrame)
    """
    Parse un fichier trip_updates .bin et retourne un DataFrame
    """
- feed = gtfs_realtime_pb2.FeedMessage()= crée une variable feed qui respecte scrupuleusement le format officiel de Google (GTFS-Realtime)
    
- with open(filepath, 'rb') as f:= ouvre le fichier en mode binaire (rb = read binary), et le nomme f

- feed.ParseFromString(f.read())= lit le contenu binaire du fichier et le convertit en une structure compréhensible par Python (grâce à gtfs_realtime_pb2)
    
- data = []= crée une liste vide qui va accueillir les données extraites du fichier
    
- for entity in feed.entity: = parcourt chaque "entité" dans le flux de données (chaque entité représente une mise à jour pour un bus spécifique)
- if entity.HasField('trip_update'):  = vérifie si l'entité contient une mise à jour de trajet (trip_update)
- trip_update = entity.trip_update = récupère la mise à jour du trajet
- trip_id = trip_update.trip.trip_id = récupère l'identifiant du trajet (trip_id)
            
- for stop_time_update in trip_update.stop_time_update: = parcourt chaque mise à jour d'heure d'arrêt (stop_time_update) dans la mise à jour du trajet
- stop_id = stop_time_update.stop_id = récupère l'identifiant de l'arrêt (stop_id)

# Récupérer les retards

- arrival_delay = None = Le retard prévu à l'arrivée (en secondes).
- departure_delay = None = Le retard prévu au départ (souvent le même)
- arrival_time = None    =   L'heure réelle de passage prévue à l'arrivée format spécial appelé Timestamp Unix 
- departure_time = None = L'heure réelle de départ prévue de l'arrêt
                
- if stop_time_update.HasField('arrival'):= « Est-ce qu'on a une case "Arrivée" sur ce formulaire ? » Si OUI : On ouvre la case et on regarde ce qu'il y a dedans (le retard, l'heure). Si NON : On ne cherche même pas à regarder (pour ne pas faire d'erreur) et on passe à la suite.

- if hasattr(stop_time_update.arrival, 'delay'):
                        arrival_delay = stop_time_update.arrival.delay = Une fois que j'ai validé la présence du bloc "Arrivée", je vérifie si une information spécifique de retard y est associée

- if hasattr(stop_time_update.arrival, 'time'):  
                        arrival_time = stop_time_update.arrival.time= est ce que qu'il a une case heure
                
- if stop_time_update.HasField('departure'):= Elle demande au fichier binaire : « Est-ce que tu as une case qui contient l'heure à laquelle le bus quitte cet arrêt ? »

- if hasattr(stop_time_update.departure, 'delay'):
                        departure_delay = stop_time_update.departure.delay= retard

- if hasattr(stop_time_update.departure, 'time'):  
                        departure_time = stop_time_update.departure.time= heure 
                
- data.append({
                    'trip_id': trip_id,= numéro de mission du bus 
                    'stop_id': stop_id,= identifiant de l'arrêt
                    'arrival_delay_seconds': arrival_delay,= retard à l'arrivée en sec
                    'departure_delay_seconds': departure_delay,
                    'arrival_delay_minutes': arrival_delay / 60 if arrival_delay is not None else None,
                    'departure_delay_minutes': departure_delay / 60 if departure_delay is not None else None,
                    'arrival_time_unix': arrival_time,= L'heure réelle de passage à l'arrêt      
                    'departure_time_unix': departure_time,  
                })
    
    return pd.DataFrame(data)

# Création d'une fonction pour combiner tous les fichiers

- def parse_all_trip_updates():=  Elle parcourt mon dossier de stockage, décode chaque fichier binaire un par un, et fusionne le tout dans une base de données unique.
    """
    Parse tous les fichiers trip_updates et les combine
    """
    gtfs_rt_dir = Path("data/raw/gtfs_rt")
    
# Trouver tous les fichiers trip_updates

- files = sorted(gtfs_rt_dir.glob("trip_updates_*.bin"))= trie les fichiers par ordre 
    
- if not files:
- print("❌ Aucun fichier trip_updates trouvé dans data/raw/gtfs_rt/")
- return None
- print(f"📁 {len(files)} fichiers trip_updates trouvés")
    
- all_data = []
    
- for i, filepath in enumerate(files, 1):
        print(f"📊 Parsing {i}/{len(files)}: {filepath.name}")
- try:
    df = parse_trip_updates_file(filepath)
            
# Extraire le timestamp du nom de fichier
# Format: trip_updates_20251212_223805.bin

- timestamp_str = filepath.stem.replace('trip_updates_', '')
- timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
- df['collecte_timestamp'] = timestamp
- all_data.append(df)
- except Exception as e:
- print(f"⚠️ Erreur sur {filepath.name}: {e}")
            continue
    
-if not all_data:
        print("❌ Aucune donnée parsée avec succès")
        return None
    
# Combiner tous les DataFrames

combined_df = pd.concat(all_data, ignore_index=True)
print(f"\n✅ Parsing terminé !")
print(f"📊 Total de passages collectés : {len(combined_df)}")
    return combined_df

# Création d'une fonction pour sauvegarder les données parsées 

- def save_parsed_data(df): = fonction qui reçoit le tableau final (DataFrame) et l’enregistre en format CSV
    """
    Sauvegarde les données parsées en CSV
    """
- output_dir = Path("data/processed")
- output_dir.mkdir(parents=True, exist_ok=True)
    
- output_file = output_dir / "gtfs_rt_parsed.csv"
- df.to_csv(output_file, index=False)
    
- print(f"💾 Données sauvegardées : {output_file}")
    
# Afficher quelques statistiques
    
- print(f"\n📈 STATISTIQUES :")
- print(f"Nombre de passages : {len(df)}")
    
# Compter combien de retards on a vraiment
    
- retards_non_nuls = df['arrival_delay_minutes'].notna().sum()
- print(f"Passages avec retards : {retards_non_nuls}")
    
- if retards_non_nuls > 0:
    print(f"Retard moyen : {df['arrival_delay_minutes'].mean():.2f} minutes")
    print(f"Retard max : {df['arrival_delay_minutes'].max():.2f} minutes")
    print(f"Retard min : {df['arrival_delay_minutes'].min():.2f} minutes")
        else:
        print("⚠️ Aucun retard trouvé dans les données")
    
    return output_file

- if __name__ == "__main__":
    print("🚀 Début du parsing des fichiers GTFS-RT\n")
    
# Parser tous les fichiers

- df = parse_all_trip_updates()
    
- if df is not None:
        save_parsed_data(df)
        print("\n👀 Aperçu des données :")
        print(df.head(10))
    else:
        print("\n❌ Échec du parsing")